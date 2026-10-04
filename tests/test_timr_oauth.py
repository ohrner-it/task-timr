"""
Unit tests for the Timr.com OAuth2 client (timr_oauth.py).

Only the HTTP boundary (the requests session) is replaced; all request building
and response handling runs through the production code.
"""

import base64
import hashlib
import unittest
from unittest.mock import Mock, patch
from urllib.parse import urlparse, parse_qs

import requests

from config import REQUEST_TIMEOUT_SECONDS
from timr_api import TimrApiError
from timr_oauth import TimrOAuthClient, create_pkce_pair, token_expires_soon, token_is_expired
from tests.utils.http_responses import make_json_response as make_response

ISSUER = "https://id.example.com/id"
DISCOVERY_URL = "https://id.example.com/id/.well-known/openid-configuration"
DISCOVERY_DOCUMENT = {
    "issuer": ISSUER,
    "authorization_endpoint": "https://login.example.com/authorize",
    "token_endpoint": "https://login.example.com/token",
    "userinfo_endpoint": "https://login.example.com/userinfo",
    "revocation_endpoint": "https://login.example.com/revoke",
}


class TestCreatePkcePair(unittest.TestCase):
    """PKCE verifier/challenge generation (RFC 7636, S256)."""

    def test_challenge_is_base64url_sha256_of_verifier_without_padding(self):
        verifier, challenge = create_pkce_pair()

        expected = base64.urlsafe_b64encode(
            hashlib.sha256(verifier.encode("ascii")).digest()).rstrip(b"=").decode("ascii")
        self.assertEqual(challenge, expected)

    def test_verifier_length_is_within_rfc_7636_bounds(self):
        verifier, _ = create_pkce_pair()

        self.assertGreaterEqual(len(verifier), 43)
        self.assertLessEqual(len(verifier), 128)

    def test_each_call_creates_a_new_verifier(self):
        self.assertNotEqual(create_pkce_pair()[0], create_pkce_pair()[0])


class TestTokenExpiresSoon(unittest.TestCase):
    """Decision whether an access token must be refreshed before use."""

    @patch("timr_oauth.time.time", return_value=1000)
    def test_token_expiring_within_margin_needs_refresh(self, _):
        self.assertTrue(token_expires_soon(1030))

    @patch("timr_oauth.time.time", return_value=1000)
    def test_already_expired_token_needs_refresh(self, _):
        self.assertTrue(token_expires_soon(900))

    @patch("timr_oauth.time.time", return_value=1000)
    def test_token_valid_beyond_margin_needs_no_refresh(self, _):
        self.assertFalse(token_expires_soon(1000 + 3599))

    def test_unknown_expiry_needs_no_refresh(self):
        # RFC 6749 makes expires_in optional; without it the token is used until rejected
        self.assertFalse(token_expires_soon(None))


class TestTokenIsExpired(unittest.TestCase):
    """Decision whether an access token can no longer be used at all."""

    @patch("timr_oauth.time.time", return_value=1000)
    def test_token_at_expiry_time_is_expired(self, _):
        self.assertTrue(token_is_expired(1000))

    @patch("timr_oauth.time.time", return_value=1000)
    def test_token_within_refresh_margin_is_not_yet_expired(self, _):
        self.assertFalse(token_is_expired(1030))

    def test_token_with_unknown_expiry_is_not_expired(self):
        self.assertFalse(token_is_expired(None))


class OAuthClientTestCase(unittest.TestCase):
    """Fixture: client whose HTTP session serves the discovery document."""

    def setUp(self):
        self.client = TimrOAuthClient(
            client_id="client-id@example.timr.com",
            client_secret="client-secret",
            redirect_uri="http://localhost:5000/oauth/callback",
            issuer=ISSUER)
        self.client.session = Mock()
        self.discovery_response = make_response(200, DISCOVERY_DOCUMENT)
        self.userinfo_response = make_response(200, {"sub": "user-uuid-1"})
        self.client.session.get.side_effect = self._get

    def _get(self, url, **kwargs):
        if url == DISCOVERY_URL:
            return self.discovery_response
        return self.userinfo_response

    def _discovery_requests(self):
        return [c for c in self.client.session.get.call_args_list if c.args[0] == DISCOVERY_URL]


class TestProviderDiscovery(OAuthClientTestCase):
    """Endpoints are read from the OpenID Provider metadata of the issuer."""

    def test_discovery_document_is_requested_from_issuer_well_known_url(self):
        self.client.authorization_url(state="state-123", code_challenge="challenge-abc")

        self.assertEqual(self._discovery_requests()[0].kwargs, {"timeout": REQUEST_TIMEOUT_SECONDS})

    def test_discovery_document_is_fetched_only_once(self):
        self.client.session.post.return_value = make_response(200, {"access_token": "a"})

        self.client.authorization_url(state="state-123", code_challenge="challenge-abc")
        self.client.exchange_code("auth-code", "verifier-xyz")
        self.client.fetch_user_id("a")

        self.assertEqual(len(self._discovery_requests()), 1)

    def test_discovery_document_of_other_issuer_is_rejected(self):
        self.discovery_response = make_response(200, dict(DISCOVERY_DOCUMENT,
                                                          issuer="https://evil.example.com/id"))

        with self.assertRaises(TimrApiError):
            self.client.authorization_url(state="state-123", code_challenge="challenge-abc")

    def test_discovery_document_without_required_endpoint_is_rejected(self):
        incomplete = {k: v for k, v in DISCOVERY_DOCUMENT.items() if k != "revocation_endpoint"}
        self.discovery_response = make_response(200, incomplete)

        with self.assertRaises(TimrApiError):
            self.client.revoke_token("refresh-1")

    def test_unavailable_discovery_document_raises_timr_api_error(self):
        self.discovery_response = make_response(503, {})

        with self.assertRaises(TimrApiError):
            self.client.authorization_url(state="state-123", code_challenge="challenge-abc")

    def test_failed_discovery_is_retried_on_next_use(self):
        self.discovery_response = make_response(503, {})
        with self.assertRaises(TimrApiError):
            self.client.authorization_url(state="state-123", code_challenge="challenge-abc")

        self.discovery_response = make_response(200, DISCOVERY_DOCUMENT)
        url = self.client.authorization_url(state="state-123", code_challenge="challenge-abc")

        self.assertTrue(url.startswith("https://login.example.com/authorize?"))


class TestTimrOAuthClient(OAuthClientTestCase):
    """Token endpoint, authorization URL, userinfo and revocation handling."""

    def test_authorization_url_contains_all_authorization_code_parameters(self):
        url = self.client.authorization_url(state="state-123", code_challenge="challenge-abc")

        parsed = urlparse(url)
        self.assertEqual(f"{parsed.scheme}://{parsed.netloc}{parsed.path}",
                         "https://login.example.com/authorize")
        self.assertEqual(parse_qs(parsed.query), {
            "response_type": ["code"],
            "client_id": ["client-id@example.timr.com"],
            "redirect_uri": ["http://localhost:5000/oauth/callback"],
            "scope": ["openid offline_access"],
            "state": ["state-123"],
            "code_challenge": ["challenge-abc"],
            "code_challenge_method": ["S256"],
        })

    @patch("timr_oauth.time.time", return_value=1000)
    def test_exchange_code_posts_code_grant_and_returns_tokens_with_absolute_expiry(self, _):
        self.client.session.post.return_value = make_response(200, {
            "access_token": "access-1", "refresh_token": "refresh-1",
            "scope": "openid offline_access", "token_type": "Bearer", "expires_in": 3599})

        tokens = self.client.exchange_code("auth-code", "verifier-xyz")

        self.client.session.post.assert_called_once_with(
            "https://login.example.com/token",
            data={
                "grant_type": "authorization_code",
                "code": "auth-code",
                "redirect_uri": "http://localhost:5000/oauth/callback",
                "code_verifier": "verifier-xyz",
                "client_id": "client-id@example.timr.com",
                "client_secret": "client-secret",
            },
            timeout=REQUEST_TIMEOUT_SECONDS)
        self.assertEqual(tokens, {
            "access_token": "access-1", "refresh_token": "refresh-1", "expires_at": 4599})

    def test_token_response_without_expires_in_has_unknown_expiry(self):
        self.client.session.post.return_value = make_response(200, {
            "access_token": "access-1", "token_type": "Bearer"})

        tokens = self.client.exchange_code("auth-code", "verifier-xyz")

        self.assertIsNone(tokens["expires_at"])

    def test_refresh_tokens_posts_refresh_grant_and_returns_rotated_refresh_token(self):
        self.client.session.post.return_value = make_response(200, {
            "access_token": "access-2", "refresh_token": "refresh-2", "expires_in": 3599})

        tokens = self.client.refresh_tokens("refresh-1")

        self.assertEqual(self.client.session.post.call_args.kwargs["data"], {
            "grant_type": "refresh_token",
            "refresh_token": "refresh-1",
            "client_id": "client-id@example.timr.com",
            "client_secret": "client-secret",
        })
        self.assertEqual(tokens["access_token"], "access-2")
        self.assertEqual(tokens["refresh_token"], "refresh-2")

    def test_refresh_tokens_keeps_previous_refresh_token_when_none_is_returned(self):
        self.client.session.post.return_value = make_response(200, {
            "access_token": "access-2", "expires_in": 3599})

        tokens = self.client.refresh_tokens("refresh-1")

        self.assertEqual(tokens["refresh_token"], "refresh-1")

    def test_refresh_tokens_without_refresh_token_fails_without_http_request(self):
        with self.assertRaises(TimrApiError):
            self.client.refresh_tokens(None)

        self.client.session.post.assert_not_called()

    def test_fetch_client_credentials_tokens_requests_timrclient_scope(self):
        self.client.session.post.return_value = make_response(200, {
            "access_token": "client-access", "expires_in": 3599})

        tokens = self.client.fetch_client_credentials_tokens()

        self.assertEqual(self.client.session.post.call_args.kwargs["data"], {
            "grant_type": "client_credentials",
            "scope": "openid timrclient",
            "client_id": "client-id@example.timr.com",
            "client_secret": "client-secret",
        })
        self.assertEqual(tokens["access_token"], "client-access")
        self.assertIsNone(tokens["refresh_token"])

    def test_token_endpoint_error_raises_timr_api_error_with_oauth_error_details(self):
        self.client.session.post.return_value = make_response(400, {
            "error": "invalid_grant", "error_description": "Authorization code expired"})

        with self.assertRaises(TimrApiError) as context:
            self.client.exchange_code("stale-code", "verifier-xyz")

        self.assertEqual(context.exception.status_code, 400)
        self.assertIn("invalid_grant", context.exception.get_technical_message())
        self.assertIn("Authorization code expired", context.exception.get_technical_message())

    def test_token_endpoint_network_error_raises_timr_api_error(self):
        self.client.session.post.side_effect = requests.exceptions.ConnectionError("unreachable")

        with self.assertRaises(TimrApiError):
            self.client.exchange_code("auth-code", "verifier-xyz")

    def test_fetch_user_id_returns_subject_from_userinfo(self):
        user_id = self.client.fetch_user_id("access-1")

        self.client.session.get.assert_called_with(
            "https://login.example.com/userinfo",
            headers={"Authorization": "Bearer access-1"},
            timeout=REQUEST_TIMEOUT_SECONDS)
        self.assertEqual(user_id, "user-uuid-1")

    def test_fetch_user_id_with_rejected_token_raises_timr_api_error(self):
        self.userinfo_response = make_response(401, {"error": "invalid_token"})

        with self.assertRaises(TimrApiError) as context:
            self.client.fetch_user_id("bad-token")

        self.assertEqual(context.exception.status_code, 401)

    def test_revoke_token_posts_refresh_token_to_revocation_endpoint(self):
        self.client.session.post.return_value = make_response(200, {})

        self.client.revoke_token("refresh-1")

        self.client.session.post.assert_called_once_with(
            "https://login.example.com/revoke",
            data={
                "token": "refresh-1",
                "token_type_hint": "refresh_token",
                "client_id": "client-id@example.timr.com",
                "client_secret": "client-secret",
            },
            timeout=REQUEST_TIMEOUT_SECONDS)

    def test_revoke_token_failure_raises_timr_api_error(self):
        self.client.session.post.return_value = make_response(400, {"error": "invalid_client"})

        with self.assertRaises(TimrApiError):
            self.client.revoke_token("refresh-1")


if __name__ == "__main__":
    unittest.main()

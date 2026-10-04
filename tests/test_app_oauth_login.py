"""
Tests for the OAuth2 authorization code login, session token refresh and logout in app.py.

The OAuth client and the Timr API client are the HTTP boundary and are replaced
where a request to Timr.com would happen; routes and session handling run for real.
"""

import base64
import hashlib
import unittest
from unittest.mock import patch
from urllib.parse import urlparse

from app import app, get_current_user, oauth_client
from timr_api import TimrApiError

USER = {"id": "user-1", "fullname": "Test User"}
AUTHORIZATION_URL = "https://login.example.com/authorize?client_id=task-timr"


class OAuthAppTestCase(unittest.TestCase):
    """Common fixture: fresh test client and a mocked Timr API client."""

    def setUp(self):
        app.testing = True
        self.client = app.test_client()
        self.timr_api_patch = patch("app.timr_api")
        self.mock_timr_api = self.timr_api_patch.start()

    def tearDown(self):
        self.timr_api_patch.stop()

    def _session(self):
        with self.client.session_transaction() as sess:
            return dict(sess)


@patch.object(oauth_client, "authorization_url", return_value=AUTHORIZATION_URL)
class TestLoginRedirect(OAuthAppTestCase):
    """GET /login starts the authorization code flow."""

    def test_login_redirects_to_timr_authorization_url(self, _):
        response = self.client.get("/login")

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.location, AUTHORIZATION_URL)

    def test_login_stores_state_sent_to_authorization_endpoint(self, mock_authorization_url):
        self.client.get("/login")

        state, _ = mock_authorization_url.call_args.args
        self.assertEqual(state, self._session()["oauth_state"])

    def test_login_sends_pkce_challenge_of_stored_verifier(self, mock_authorization_url):
        self.client.get("/login")

        _, code_challenge = mock_authorization_url.call_args.args
        verifier = self._session()["oauth_code_verifier"]
        expected_challenge = base64.urlsafe_b64encode(
            hashlib.sha256(verifier.encode("ascii")).digest()).rstrip(b"=").decode("ascii")
        self.assertEqual(code_challenge, expected_challenge)

    def test_session_cookie_is_restricted_to_same_site_top_level_navigation(self, _):
        response = self.client.get("/login")

        self.assertIn("SameSite=Lax", response.headers["Set-Cookie"])
        self.assertIn("HttpOnly", response.headers["Set-Cookie"])

    def test_each_login_uses_a_new_state(self, mock_authorization_url):
        self.client.get("/login")
        self.client.get("/login")

        first_state, second_state = (c.args[0] for c in mock_authorization_url.call_args_list)
        self.assertNotEqual(first_state, second_state)

    def test_unavailable_authorization_server_returns_to_index(self, mock_authorization_url):
        mock_authorization_url.side_effect = TimrApiError("Timr.com login service is not reachable.")

        response = self.client.get("/login")

        self.assertEqual(response.status_code, 302)
        self.assertEqual(urlparse(response.location).path, "/")


@patch.object(oauth_client, "fetch_user_id", return_value="user-1")
@patch.object(oauth_client, "exchange_code")
class TestOAuthCallback(OAuthAppTestCase):
    """GET /oauth/callback completes the login."""

    TOKENS = {"access_token": "access-1", "refresh_token": "refresh-1", "expires_at": 5000}

    def setUp(self):
        super().setUp()
        self.mock_timr_api.get_user.return_value = dict(USER, email="test@example.com",
                                                        employee_number="EMP001")
        with self.client.session_transaction() as sess:
            sess["oauth_state"] = "expected-state"
            sess["oauth_code_verifier"] = "verifier-1"

    def test_valid_callback_exchanges_code_with_stored_verifier(self, mock_exchange, _):
        mock_exchange.return_value = self.TOKENS

        self.client.get("/oauth/callback?code=code-1&state=expected-state")

        mock_exchange.assert_called_once_with("code-1", "verifier-1")

    def test_valid_callback_stores_tokens_and_user_in_session(self, mock_exchange, mock_fetch_user_id):
        mock_exchange.return_value = self.TOKENS

        response = self.client.get("/oauth/callback?code=code-1&state=expected-state")

        self.assertEqual(response.status_code, 302)
        self.assertEqual(urlparse(response.location).path, "/")
        mock_fetch_user_id.assert_called_once_with("access-1")
        self.mock_timr_api.get_user.assert_called_once_with("user-1")
        session = self._session()
        self.assertEqual(session["token"], "access-1")
        self.assertEqual(session["refresh_token"], "refresh-1")
        self.assertEqual(session["token_expires_at"], 5000)
        # Only the user data the application needs is kept in the session cookie
        self.assertEqual(session["user"], USER)

    def test_valid_callback_removes_one_time_login_values_from_session(self, mock_exchange, _):
        mock_exchange.return_value = self.TOKENS

        self.client.get("/oauth/callback?code=code-1&state=expected-state")

        self.assertNotIn("oauth_state", self._session())
        self.assertNotIn("oauth_code_verifier", self._session())

    def test_callback_with_wrong_state_is_rejected(self, mock_exchange, _):
        response = self.client.get("/oauth/callback?code=code-1&state=forged-state")

        self.assertEqual(response.status_code, 302)
        mock_exchange.assert_not_called()
        self.assertNotIn("token", self._session())

    def test_callback_without_started_login_is_rejected(self, mock_exchange, _):
        with self.client.session_transaction() as sess:
            sess.clear()

        self.client.get("/oauth/callback?code=code-1&state=expected-state")

        mock_exchange.assert_not_called()
        self.assertNotIn("token", self._session())

    def test_state_cannot_be_reused(self, mock_exchange, _):
        mock_exchange.side_effect = TimrApiError("invalid_grant")
        self.client.get("/oauth/callback?code=code-1&state=expected-state")
        mock_exchange.reset_mock()

        self.client.get("/oauth/callback?code=code-2&state=expected-state")

        mock_exchange.assert_not_called()

    def test_callback_with_authorization_error_does_not_log_in(self, mock_exchange, _):
        response = self.client.get("/oauth/callback?error=access_denied&state=expected-state")

        self.assertEqual(response.status_code, 302)
        mock_exchange.assert_not_called()
        self.assertNotIn("token", self._session())

    def test_failed_code_exchange_does_not_log_in(self, mock_exchange, _):
        mock_exchange.side_effect = TimrApiError("Login failed")

        response = self.client.get("/oauth/callback?code=code-1&state=expected-state")

        self.assertEqual(response.status_code, 302)
        self.assertNotIn("token", self._session())
        self.assertNotIn("user", self._session())

    def test_failed_user_lookup_does_not_log_in(self, mock_exchange, _):
        mock_exchange.return_value = self.TOKENS
        self.mock_timr_api.get_user.side_effect = TimrApiError("Forbidden", 403)

        self.client.get("/oauth/callback?code=code-1&state=expected-state")

        self.assertNotIn("token", self._session())
        self.assertNotIn("user", self._session())


class TestGetCurrentUser(OAuthAppTestCase):
    """get_current_user() authorizes the Timr API client and refreshes tokens."""

    def _call_with_session(self, **session_values):
        with app.test_request_context():
            from flask import session
            session.update(session_values)
            user = get_current_user()
            return user, dict(session)

    def test_returns_none_without_token(self):
        user, _ = self._call_with_session(user=USER)

        self.assertIsNone(user)

    @patch("app.token_expires_soon", return_value=False)
    def test_valid_token_authorizes_api_client_for_request(self, _):
        user, _ = self._call_with_session(token="access-1", token_expires_at=5000, user=USER)

        self.assertEqual(user, USER)
        self.assertEqual(self.mock_timr_api.token, "access-1")
        self.assertEqual(self.mock_timr_api.user, USER)

    @patch("app.token_expires_soon", return_value=False)
    @patch.object(oauth_client, "refresh_tokens")
    def test_valid_token_is_not_refreshed(self, mock_refresh, _):
        self._call_with_session(token="access-1", token_expires_at=5000, user=USER)

        mock_refresh.assert_not_called()

    @patch("app.token_expires_soon", return_value=True)
    @patch.object(oauth_client, "refresh_tokens")
    def test_expiring_token_is_refreshed_and_stored(self, mock_refresh, _):
        mock_refresh.return_value = {"access_token": "access-2", "refresh_token": "refresh-2",
                                     "expires_at": 9000}

        user, session = self._call_with_session(
            token="access-1", refresh_token="refresh-1", token_expires_at=5000, user=USER)

        mock_refresh.assert_called_once_with("refresh-1")
        self.assertEqual(user, USER)
        self.assertEqual(session["token"], "access-2")
        self.assertEqual(session["refresh_token"], "refresh-2")
        self.assertEqual(session["token_expires_at"], 9000)
        self.assertEqual(self.mock_timr_api.token, "access-2")

    @patch("app.token_is_expired", return_value=True)
    @patch("app.token_expires_soon", return_value=True)
    @patch.object(oauth_client, "refresh_tokens", side_effect=TimrApiError("invalid_grant", 400))
    def test_failed_refresh_of_expired_token_ends_session(self, *_):
        user, session = self._call_with_session(
            token="access-1", refresh_token="refresh-1", token_expires_at=5000, user=USER)

        self.assertIsNone(user)
        self.assertNotIn("token", session)
        self.assertNotIn("user", session)

    @patch("app.token_is_expired", return_value=False)
    @patch("app.token_expires_soon", return_value=True)
    @patch.object(oauth_client, "refresh_tokens", side_effect=TimrApiError("invalid_grant", 400))
    def test_failed_refresh_of_still_valid_token_keeps_session(self, *_):
        # Timr.com rotates refresh tokens: when parallel requests refresh concurrently,
        # all but the first fail although the session is still valid
        user, session = self._call_with_session(
            token="access-1", refresh_token="refresh-1", token_expires_at=5000, user=USER)

        self.assertEqual(user, USER)
        self.assertEqual(session["token"], "access-1")
        self.assertEqual(self.mock_timr_api.token, "access-1")

    @patch("app.token_is_expired", return_value=True)
    @patch("app.token_expires_soon", return_value=True)
    @patch.object(oauth_client, "refresh_tokens", side_effect=TimrApiError("invalid_grant", 400))
    def test_api_endpoint_with_unrefreshable_session_returns_unauthorized(self, *_):
        with self.client.session_transaction() as sess:
            sess.update(token="access-1", refresh_token="refresh-1", token_expires_at=5000, user=USER)

        response = self.client.get("/api/working-times?date=2026-10-04")

        self.assertEqual(response.status_code, 401)


@patch.object(oauth_client, "revoke_token")
class TestLogout(OAuthAppTestCase):
    """GET /logout ends the session and revokes the refresh token."""

    def setUp(self):
        super().setUp()
        with self.client.session_transaction() as sess:
            sess.update(token="access-1", refresh_token="refresh-1", token_expires_at=5000, user=USER)

    def test_logout_clears_session(self, _):
        response = self.client.get("/logout")

        self.assertEqual(response.status_code, 302)
        self.assertNotIn("token", self._session())
        self.assertNotIn("refresh_token", self._session())
        self.assertNotIn("user", self._session())

    def test_logout_revokes_refresh_token(self, mock_revoke):
        self.client.get("/logout")

        mock_revoke.assert_called_once_with("refresh-1")

    def test_logout_clears_session_even_if_revocation_fails(self, mock_revoke):
        mock_revoke.side_effect = TimrApiError("unreachable")

        response = self.client.get("/logout")

        self.assertEqual(response.status_code, 302)
        self.assertNotIn("token", self._session())


class TestLoginPage(OAuthAppTestCase):
    """The index page offers the timr login instead of a password form."""

    def test_unauthenticated_index_links_to_oauth_login(self):
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b'href="/login"', response.data)
        self.assertNotIn(b'type="password"', response.data)


if __name__ == "__main__":
    unittest.main()

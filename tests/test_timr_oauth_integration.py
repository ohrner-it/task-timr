"""
Integration tests for the OAuth2 client against the real Timr.com authorization server.

They use the client credentials OAuth client of the integration test configuration
(see tests/utils/integration.py) and do not change any data.
"""

import unittest

from config import API_BASE_URL, OAUTH_ISSUER, TIMR_SERVICE_CLIENT_ID, TIMR_SERVICE_CLIENT_SECRET
from timr_api import TimrApi, TimrApiError
from timr_oauth import TimrOAuthClient


class TimrOAuthIntegrationTest(unittest.TestCase):
    """Contract tests for discovery and token handling of the Timr.com authorization server."""

    def setUp(self):
        if not (TIMR_SERVICE_CLIENT_ID and TIMR_SERVICE_CLIENT_SECRET):
            self.skipTest("Skipping integration tests: set TIMR_SERVICE_CLIENT_ID and "
                          "TIMR_SERVICE_CLIENT_SECRET to run them")
        self.client = TimrOAuthClient(TIMR_SERVICE_CLIENT_ID, TIMR_SERVICE_CLIENT_SECRET)

    def test_provider_metadata_provides_all_endpoints_via_https(self):
        for name in ("authorization_endpoint", "token_endpoint", "userinfo_endpoint",
                     "revocation_endpoint"):
            with self.subTest(endpoint=name):
                self.assertTrue(self.client._endpoint(name).startswith("https://"))

    def test_authorization_url_uses_discovered_authorization_endpoint(self):
        url = self.client.authorization_url(state="state", code_challenge="challenge")

        self.assertTrue(url.startswith(f"{OAUTH_ISSUER}/"))

    def test_client_credentials_token_authorizes_api_requests(self):
        api = TimrApi()
        api.token = self.client.fetch_client_credentials_tokens()["access_token"]

        self.assertIsInstance(api.get_working_time_types(), list)

    def test_rejected_client_credentials_raise_timr_api_error(self):
        client = TimrOAuthClient(TIMR_SERVICE_CLIENT_ID, "wrong-secret")

        with self.assertRaises(TimrApiError) as context:
            client.fetch_client_credentials_tokens()

        self.assertIn(context.exception.status_code, (400, 401))

    def test_api_base_url_is_protected_by_this_authorization_server(self):
        response = self.client.session.get(f"{API_BASE_URL}/.well-known/oauth-protected-resource",
                                           timeout=30)

        self.assertIn(OAUTH_ISSUER, response.json()["authorization_servers"])


if __name__ == "__main__":
    unittest.main()

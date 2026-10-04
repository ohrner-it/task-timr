"""
Setup helpers for integration tests against the real Timr.com API.

Integration tests cannot perform the interactive OAuth2 authorization code login
used by the web application. They authenticate with an OAuth2 client credentials
client instead and act on behalf of a dedicated test user, which mirrors how the
application acts for the logged-in user.

Required environment variables:
- TIMR_SERVICE_CLIENT_ID / TIMR_SERVICE_CLIENT_SECRET: client credentials OAuth client
- TIMR_TEST_USER_ID: ID of the Timr user whose data the tests create and delete
"""

import os
import unittest

from config import TIMR_SERVICE_CLIENT_ID, TIMR_SERVICE_CLIENT_SECRET
from timr_api import TimrApi
from timr_oauth import TimrOAuthClient


def create_integration_api():
    """
    Create a TimrApi client authorized via client credentials acting for the test user.

    Raises:
        unittest.SkipTest: If the integration test configuration is missing
    """
    test_user_id = os.environ.get("TIMR_TEST_USER_ID")
    if not (TIMR_SERVICE_CLIENT_ID and TIMR_SERVICE_CLIENT_SECRET and test_user_id):
        raise unittest.SkipTest(
            "Skipping integration tests: set TIMR_SERVICE_CLIENT_ID, TIMR_SERVICE_CLIENT_SECRET "
            "and TIMR_TEST_USER_ID to run them")

    tokens = TimrOAuthClient(TIMR_SERVICE_CLIENT_ID, TIMR_SERVICE_CLIENT_SECRET) \
        .fetch_client_credentials_tokens()
    api = TimrApi()
    api.token = tokens["access_token"]
    api.user = api.get_user(test_user_id)
    return api


def get_attendance_working_time_type_id(api):
    """Return the ID of the first active attendance time working time type."""
    return next(wt_type["id"] for wt_type in api.get_working_time_types()
                if wt_type["category"] == "attendance_time")

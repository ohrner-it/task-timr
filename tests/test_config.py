"""
Test configuration file for the Timr.com Alternative Frontend

This file provides configuration settings for running tests
"""

import os
import logging

# Configure logging for tests
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Define test credentials - these can be overridden by environment variables
TEST_USERNAME = os.environ.get("TIMR_USERNAME", "test_user")
TEST_PASSWORD = os.environ.get("TIMR_PASSWORD", "test_password")

# Define test database (use in-memory SQLite for unit tests)
TEST_DATABASE_URI = "sqlite:///:memory:"

# Default test date (tomorrow)
import datetime
TEST_DATE = (datetime.datetime.now() + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
"""
Configuration settings for Task Timr
Task duration-focused alternative frontend to Timr.com

Copyright (c) 2025 Ohrner IT GmbH
Licensed under the MIT License
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

# Used for session security
# Environment variable takes precedence over config value
SESSION_SECRET = os.environ.get('SESSION_SECRET', 'dev-secret-key-change-in-production')

# Timr.com company ID, used to link to the company's Timr.com web application
# Environment variable takes precedence over config value
COMPANY_ID = os.environ.get('TIMR_COMPANY_ID', 'ohrnerit')

# API base URL
API_BASE_URL = "https://api.timr.com/v1"

# Timeout in seconds for requests to Timr.com
REQUEST_TIMEOUT_SECONDS = 30

# Issuer of the Timr.com OAuth2 authorization server. Its endpoints are read from
# the OpenID Provider metadata at <issuer>/.well-known/openid-configuration
OAUTH_ISSUER = "https://system.timr.com/id"

# OAuth2 client for the user login (grant type "Authorization Code" in Timr.com).
# The redirect URI must exactly match one of the redirect URLs configured for the client.
# Environment variables take precedence over config values
TIMR_OAUTH_CLIENT_ID = os.environ.get('TIMR_OAUTH_CLIENT_ID', '')
TIMR_OAUTH_CLIENT_SECRET = os.environ.get('TIMR_OAUTH_CLIENT_SECRET', '')
TIMR_OAUTH_REDIRECT_URI = os.environ.get('TIMR_OAUTH_REDIRECT_URI', 'http://localhost:5000/oauth/callback')

# OAuth2 client with grant type "Client Credentials" for developer tools and
# integration tests. It grants access to all data of the Timr.com account and is
# not used by the web application.
TIMR_SERVICE_CLIENT_ID = os.environ.get('TIMR_SERVICE_CLIENT_ID', '')
TIMR_SERVICE_CLIENT_SECRET = os.environ.get('TIMR_SERVICE_CLIENT_SECRET', '')

# Date and time formats (for UI display and user input parsing only)
# Note: API communication uses ISO 8601 format with timezone offset
DATE_FORMAT = "%Y-%m-%d"
TIME_FORMAT = "%H:%M"
DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S%z"

# UI configuration
DEFAULT_PAGE_SIZE = 20
MAX_RECENT_TASKS = 10

# Network configuration for deployment
# Environment variables take precedence over config values
BIND_IP = os.environ.get('BIND_IP', '127.0.0.1')
PORT = int(os.environ.get('PORT', '5000'))

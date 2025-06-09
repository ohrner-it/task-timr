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

# Timr.com company ID
# Environment variable takes precedence over config value
COMPANY_ID = os.environ.get('TIMR_COMPANY_ID', 'ohrnerit')

# API base URL
API_BASE_URL = "https://api.timr.com/v0.2"

# Date and time formats (for UI display and user input parsing only)
# Note: API communication uses ISO 8601 format with timezone offset
DATE_FORMAT = "%Y-%m-%d"
TIME_FORMAT = "%H:%M"
DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S%z"

# UI configuration
DEFAULT_PAGE_SIZE = 20
MAX_RECENT_TASKS = 10

# Task list retrieval user credentials
# Regular Timr users cannot retrieve the full task list, so we need an additional 
# account with elevated privileges specifically for task operations.
# In Timr.com, this account must be configured with Task editing capabilities
# (even though Task Timr only reads tasks and never modifies them).
# Environment variables take precedence over config values
TASKLIST_TIMR_USER = os.environ.get('TASKLIST_TIMR_USER', '')
TASKLIST_TIMR_PASSWORD = os.environ.get('TASKLIST_TIMR_PASSWORD', '')

# Network configuration for deployment
# Environment variables take precedence over config values
BIND_IP = os.environ.get('BIND_IP', '127.0.0.1')
PORT = int(os.environ.get('PORT', '5000'))

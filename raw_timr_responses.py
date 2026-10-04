"""
Script to fetch and display raw, unparsed responses from the TIMR API.

Authenticates with the OAuth2 client credentials client configured via
TIMR_SERVICE_CLIENT_ID and TIMR_SERVICE_CLIENT_SECRET. As this client can access
the data of all users, working times are only shown for the user TIMR_TEST_USER_ID.
"""

import json
import os
from datetime import date

import requests

from config import API_BASE_URL, TIMR_SERVICE_CLIENT_ID, TIMR_SERVICE_CLIENT_SECRET
from timr_api import TimrApiError
from timr_oauth import TimrOAuthClient

user_id = os.environ.get("TIMR_TEST_USER_ID")

if not TIMR_SERVICE_CLIENT_ID or not TIMR_SERVICE_CLIENT_SECRET or not user_id:
    print("Error: TIMR_SERVICE_CLIENT_ID, TIMR_SERVICE_CLIENT_SECRET and TIMR_TEST_USER_ID "
          "environment variables must be set")
    exit(1)

print("REQUESTING ACCESS TOKEN (client credentials):")
print("=" * 50)

try:
    tokens = TimrOAuthClient(TIMR_SERVICE_CLIENT_ID, TIMR_SERVICE_CLIENT_SECRET) \
        .fetch_client_credentials_tokens()
except TimrApiError as e:
    print(f"Token request failed: {e.get_technical_message()}")
    exit(1)

print(f"Access token received, expires at: {tokens['expires_at']}")
print("\n")

# Prepare headers with authentication token
headers = {
    'Authorization': f"Bearer {tokens['access_token']}",
    'Content-Type': 'application/json'
}

print("TESTING RAW WORKING TIME TYPES RESPONSE:")
print("=" * 50)

# Fetch working time types
working_time_types_response = requests.get(
    f"{API_BASE_URL}/working-time-types",
    headers=headers
)

print(f"Working Time Types Status Code: {working_time_types_response.status_code}")
print(f"Working Time Types Headers: {dict(working_time_types_response.headers)}")
print("Raw Working Time Types Response:")
print(working_time_types_response.text)

# Also fetch a working time to see how working_time_type is included
print("\n")
print("TESTING RAW WORKING TIMES RESPONSE:")
print("=" * 50)

today = date.today()

working_times_response = requests.get(
    f"{API_BASE_URL}/working-times",
    headers=headers,
    params={
        'users': user_id,
        'start_from': today.strftime('%Y-%m-%d'),
        'start_to': today.strftime('%Y-%m-%d')
    }
)

print(f"Working Times Status Code: {working_times_response.status_code}")
print("Raw Working Times Response:")
print(working_times_response.text)

# If successful, also parse and display working times structure
if working_times_response.status_code == 200:
    try:
        working_times_data = working_times_response.json()
        print("\n")
        print("PARSED WORKING TIMES STRUCTURE:")
        print("=" * 50)
        print(json.dumps(working_times_data, indent=2, ensure_ascii=False))

        # Show how working_time_type is structured in actual working times
        if 'data' in working_times_data and working_times_data['data']:
            print(f"\nWorking Time Type Structure in actual working times:")
            print("-" * 50)
            for wt in working_times_data['data']:
                wt_type = wt.get('working_time_type', {})
                print(f"Working Time ID: {wt.get('id')}")
                print(f"Working Time Type: {wt_type}")
                if wt_type:
                    print(f"  - ID: {wt_type.get('id')}")
                    print(f"  - Name: {wt_type.get('name')}")
                print()
    except json.JSONDecodeError as e:
        print(f"Error parsing working times JSON: {e}")

# If successful, also try to parse and display in a more readable format
if working_time_types_response.status_code == 200:
    try:
        types_data = working_time_types_response.json()
        print("\n")
        print("PARSED WORKING TIME TYPES:")
        print("=" * 50)
        print(json.dumps(types_data, indent=2, ensure_ascii=False))

        # Display summary information
        if 'data' in types_data:
            print(f"\nTotal Working Time Types Found: {len(types_data['data'])}")
            print("\nSummary of Working Time Types:")
            print("-" * 30)
            for idx, wtt in enumerate(types_data['data'], 1):
                name = wtt.get('name', 'N/A')
                short_name = wtt.get('short_name', 'N/A')
                category = wtt.get('category', 'N/A')
                archived = wtt.get('archived', False)
                print(f"{idx}. {name} ({short_name}) - Category: {category} - Archived: {archived}")

    except json.JSONDecodeError as e:
        print(f"Error parsing working time types JSON: {e}")
else:
    print(f"Failed to fetch working time types: {working_time_types_response.status_code}")

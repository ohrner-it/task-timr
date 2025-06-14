"""
Script to fetch and display raw, unparsed responses from the TIMR API.
"""

import os
import json
import requests
from datetime import date
from config import COMPANY_ID

# Get credentials
username = os.environ.get("TIMR_USER")
password = os.environ.get("TIMR_PASSWORD")

if not username or not password:
    print("Error: TIMR_USER and TIMR_PASSWORD environment variables must be set")
    exit(1)

base_url = "https://api.timr.com/v0.2"

# Make raw login request to see the actual response
print("TESTING RAW LOGIN RESPONSE:")
print("=" * 50)

login_data = {
    "identifier": COMPANY_ID,
    "login": username,
    "password": password
}

login_response = requests.post(f"{base_url}/login", json=login_data)

print(f"Login Status Code: {login_response.status_code}")
print(f"Login Headers: {dict(login_response.headers)}")
print("Raw Login Response:")
print(login_response.text)
print("\n")

# If login successful, get the token and fetch working time types
if login_response.status_code == 200:
    try:
        login_data_parsed = login_response.json()
        token = login_data_parsed.get('token')
        
        if token:
            print("TESTING RAW WORKING TIME TYPES RESPONSE:")
            print("=" * 50)
            
            # Prepare headers with authentication token
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
            
            # Fetch working time types
            working_time_types_response = requests.get(
                f"{base_url}/working-time-types",
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
            
            # Get today's date for working times query
            today = date.today()
            
            working_times_response = requests.get(
                f"{base_url}/working-times",
                headers=headers,
                params={
                    'start_date': today.strftime('%Y-%m-%d'),
                    'end_date': today.strftime('%Y-%m-%d')
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
                                print(f"  - Category: {wt_type.get('category')}")
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
        else:
            print("No token found in login response")
            
    except json.JSONDecodeError as e:
        print(f"Error parsing login JSON: {e}")
else:
    print(f"Login failed with status code: {login_response.status_code}")
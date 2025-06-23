"""
Reference mock data structures that accurately match Timr API responses.

This module provides realistic mock data templates validated against real API responses:
- Login responses with proper user data structure
- Working time objects with complete field coverage
- Task objects with all required fields
- Project time entries
- Error response structures

All mock data uses proper UUID formats and realistic field values.
These templates ensure tests accurately reflect production API behavior.
"""

# Realistic login response mock
REALISTIC_LOGIN_RESPONSE = {
    "token": "12345678-1234-1234-1234-123456789abc",
    "alias": None,
    "valid_until": None,
    "user": {
        "id": "87654321-4321-4321-4321-cba987654321",
        "firstname": "Test",
        "lastname": "User",
        "fullname": "Test User",
        "email": "test@example.com",
        "employee_number": "EMP001",
        "external_id": "EXT001"
    }
}

# Realistic working time object mock
REALISTIC_WORKING_TIME = {
    "id": "11111111-2222-3333-4444-555555555555",
    "start": "2025-04-01T09:00:00+00:00",
    "end": "2025-04-01T17:00:00+00:00",
    "break_time_total_minutes": 30,
    "break_times": [
        {
            "type": "manual",
            "start": "2025-04-01T12:00:00+00:00",
            "duration_minutes": 30
        }
    ],
    "duration": {
        "type": "time_tracking",
        "minutes": 450,
        "minutes_rounded": 450
    },
    "changed": True,
    "notes": "Test working time",
    "user": {
        "id": "87654321-4321-4321-4321-cba987654321",
        "firstname": "Test",
        "lastname": "User",
        "fullname": "Test User",
        "email": "test@example.com",
        "employee_number": "EMP001",
        "external_id": "EXT001"
    },
    "working_time_type": {
        "id": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
        "name": "Regular Work",
        "external_id": ""
    },
    "working_time_date_span": {
        "id": "12345678-abcd-1234-abcd-123456789abc"
    },
    "working_time_request": None,
    "start_location": None,
    "end_location": None,
    "start_platform": "timr_web",
    "end_platform": "timr_web",
    "last_modified": "2025-04-01T17:00:00Z",
    "last_modified_by": {
        "id": "87654321-4321-4321-4321-cba987654321",
        "firstname": "Test",
        "lastname": "User",
        "fullname": "Test User",
        "email": "test@example.com",
        "employee_number": "EMP001",
        "external_id": "EXT001"
    },
    "status": "changeable"
}

# Realistic working time type object mock
REALISTIC_WORKING_TIME_TYPE = {
    "id": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
    "name": "Regular Work",
    "short_name": "REG",
    "description": "Regular working time",
    "external_id": "",
    "edit_unit": "minutes",
    "category": "attendance_time",
    "sub_category": "present",
    "recording_mode_user": None,
    "non_creditable_deductible": 0,
    "compensation_deductible": None,
    "archived": False,
    "requires_substitute": False
}

# Another working time type for variety
REALISTIC_WORKING_TIME_TYPE_VACATION = {
    "id": "bbbbbbbb-cccc-dddd-eeee-ffffffffffff",
    "name": "Vacation",
    "short_name": "VAC",
    "description": "Vacation time",
    "external_id": "",
    "edit_unit": "half_days",
    "category": "vacation",
    "sub_category": None,
    "recording_mode_user": "allowed",
    "non_creditable_deductible": 0,
    "compensation_deductible": None,
    "archived": False,
    "requires_substitute": False
}

# Realistic task object mock
REALISTIC_TASK = {
    "id": "abcdefab-1234-5678-9abc-def123456789",
    "name": "Test Task",
    "description": "A test task for validation",
    "external_id": "TASK-001",
    "bookable": True,
    # Fields identified as missing in real API
    "project_time_notes_required": False,
    "earliest_start_time": None,
    "end_date": None,
    "custom_field_1": "",
    "breadcrumbs": "Test Customer > Test Project > Test Task",
    "active_from": None,
    "billable": True,
    "location_restriction_radius_meters": None,
    "start_date": None,
    "active_to": None,
    "latest_end_time": None,
    "parent_task": None,
    "custom_field_2": "",
    "location_inherited": False,
    "custom_field_3": "",
    "lock_date": None,
    "location": {
        "address": "",
        "zip_code": "",
        "state": "",
        "lat": None,
        "city": "",
        "country": "",
        "lon": None
    },
    "description_external": ""
    # Note: Removed 'archived', 'project', 'customer' fields as they were extra fields not in real API
}

# Realistic project time object mock
REALISTIC_PROJECT_TIME = {
    "id": "dddddddd-eeee-ffff-aaaa-bbbbbbbbbbbb",
    "start": "2025-04-01T09:00:00+00:00",
    "end": "2025-04-01T11:00:00+00:00",
    "status": "changeable",
    "changed": True,
    "notes": "Test project time",
    "task": {
        "id": "abcdefab-1234-5678-9abc-def123456789",
        "name": "Test Task",
        "external_id": "TASK-001"
    },
    "user": {
        "id": "87654321-4321-4321-4321-cba987654321",
        "firstname": "Test",
        "lastname": "User",
        "fullname": "Test User",
        "email": "test@example.com",
        "employee_number": "EMP001",
        "external_id": "EXT001"
    },
    "last_modified": "2025-04-01T11:00:00Z",
    "last_modified_by": {
        "id": "87654321-4321-4321-4321-cba987654321",
        "firstname": "Test",
        "lastname": "User",
        "fullname": "Test User",
        "email": "test@example.com",
        "employee_number": "EMP001",
        "external_id": "EXT001"
    }
}

# Error response structures based on common patterns
TIMR_API_ERROR_RESPONSES = {
    "unauthorized": {
        "status_code": 401,
        "message": "Invalid username or password.",
        "error_code": "UNAUTHORIZED"
    },
    "not_found": {
        "status_code": 404,
        "message": "The requested resource was not found.",
        "error_code": "NOT_FOUND"
    },
    "validation_error": {
        "status_code": 400,
        "message": "Validation failed",
        "error_code": "VALIDATION_ERROR",
        "details": {
            "field": "start",
            "message": "Start time is required"
        }
    },
    "business_rule_violation": {
        "status_code": 422,
        "message": "Business rule violation",
        "error_code": "BUSINESS_RULE_VIOLATION",
        "details": {
            "rule": "working_time_overlap",
            "message": "Working time overlaps with existing entry"
        }
    }
}

def create_working_time_list_response(working_times_list=None):
    """Create a realistic working times list response with pagination"""
    if working_times_list is None:
        working_times_list = [REALISTIC_WORKING_TIME]
    
    return {
        "next_page_token": None,  # or a cursor string for next page
        "data": working_times_list
    }

def create_working_time_types_list_response(wt_types_list=None):
    """Create a realistic working time types list response with pagination"""
    if wt_types_list is None:
        wt_types_list = [REALISTIC_WORKING_TIME_TYPE, REALISTIC_WORKING_TIME_TYPE_VACATION]
    
    return {
        "next_page_token": None,
        "data": wt_types_list
    }

def create_tasks_list_response(tasks_list=None):
    """Create a realistic tasks list response with pagination"""
    if tasks_list is None:
        tasks_list = [REALISTIC_TASK]
    
    return {
        "next_page_token": None,
        "data": tasks_list
    }

def create_project_times_list_response(project_times_list=None):
    """Create a realistic project times list response with pagination"""
    if project_times_list is None:
        project_times_list = [REALISTIC_PROJECT_TIME]
    
    return {
        "next_page_token": None,
        "data": project_times_list
    }

# Helper functions to create variations of data
def create_working_time_variant(**overrides):
    """Create a working time object with specified field overrides"""
    working_time = REALISTIC_WORKING_TIME.copy()
    working_time.update(overrides)
    return working_time

def create_task_variant(**overrides):
    """Create a task object with specified field overrides"""
    task = REALISTIC_TASK.copy()
    task.update(overrides)
    return task

def create_user_variant(**overrides):
    """Create a user object with specified field overrides"""
    user = REALISTIC_LOGIN_RESPONSE["user"].copy()
    user.update(overrides)
    return user
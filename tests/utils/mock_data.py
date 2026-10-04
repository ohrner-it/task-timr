"""
Reference mock data structures that accurately match Timr API responses.

This module provides realistic mock data templates validated against real API responses:
- User objects as returned by GET /users/{id}
- Working time objects with complete field coverage
- Task objects with all required fields
- Project time entries
- Error response structures

All mock data uses proper UUID formats and realistic field values.
These templates ensure tests accurately reflect production API behavior.
"""

# Realistic user object mock (GET /users/{id} with the user's own access token)
REALISTIC_USER = {
    "id": "87654321-4321-4321-4321-cba987654321",
    "firstname": "Test",
    "lastname": "User",
    "fullname": "Test User",
    "email": "test@example.com",
    "employee_number": "EMP001",
    "external_id": "EXT001",
    "holiday_calendar": {
        "id": "f929d979-a27c-446d-8541-c973c14cbee3",
        "description": "Deutschland: Baden-Württemberg"
    },
    "vacation_year_start": "--01-01"
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
        "type": "minutes",
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
    "working_time_date_span": None,
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
    "recording_mode_user": "allowed",
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
    "archived": False,
    "requires_substitute": False
}

# Realistic task object mock (GET /users/{id}/tasks returns this reduced task shape)
REALISTIC_TASK = {
    "id": "abcdefab-1234-5678-9abc-def123456789",
    "name": "Test Task",
    "breadcrumbs": "Test Customer/Test Project/Test Task",
    "external_id": "TASK-001",
    "parent_task": {
        "id": "fedcbafe-4321-8765-cba9-987654321fed",
        "name": "Test Project",
        "breadcrumbs": "Test Customer/Test Project",
        "external_id": None
    },
    "description": "A test task for validation",
    "bookable": True,
    "billable": True,
    "project_time_notes_required": False,
    "lock_date": None,
    "active_from": None,
    "active_to": None,
    "budget_planning_type": "none",
    "location_inherited": True,
    "location": None,
    "location_restriction_radius_meters": None,
    "custom_field_1": None,
    "custom_field_2": None,
    "custom_field_3": None
}

# Realistic project time object mock
REALISTIC_PROJECT_TIME = {
    "id": "dddddddd-eeee-ffff-aaaa-bbbbbbbbbbbb",
    "start": "2025-04-01T09:00:00+00:00",
    "end": "2025-04-01T11:00:00+00:00",
    "break_time_total_minutes": 0,
    "break_times": [],
    "duration": {
        "type": "minutes",
        "minutes": 120,
        "minutes_rounded": 120
    },
    "status": "changeable",
    "changed": True,
    "notes": "Test project time",
    "task": {
        "id": "abcdefab-1234-5678-9abc-def123456789",
        "name": "Test Task",
        "breadcrumbs": "Test Customer/Test Project/Test Task",
        "external_id": "TASK-001"
    },
    "billable": True,
    "start_location": None,
    "end_location": None,
    "start_platform": "timr_web",
    "end_platform": "timr_web",
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
    user = REALISTIC_USER.copy()
    user.update(overrides)
    return user
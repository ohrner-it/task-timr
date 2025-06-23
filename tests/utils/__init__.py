"""
Test utilities package for Task Timr.

This package contains reusable testing components:
- Mock validation framework
- Reference mock data structures  
- Test helper functions
"""

from .mock_validator import MockValidator, validate_mock_against_real, extract_structure_template
from .mock_data import (
    REALISTIC_LOGIN_RESPONSE, REALISTIC_WORKING_TIME, REALISTIC_WORKING_TIME_TYPE,
    REALISTIC_TASK, REALISTIC_PROJECT_TIME, TIMR_API_ERROR_RESPONSES,
    create_working_time_list_response, create_working_time_types_list_response,
    create_tasks_list_response, create_project_times_list_response,
    create_working_time_variant, create_task_variant, create_user_variant
)

__all__ = [
    # Mock validator
    'MockValidator', 'validate_mock_against_real', 'extract_structure_template',
    
    # Mock data
    'REALISTIC_LOGIN_RESPONSE', 'REALISTIC_WORKING_TIME', 'REALISTIC_WORKING_TIME_TYPE',
    'REALISTIC_TASK', 'REALISTIC_PROJECT_TIME', 'TIMR_API_ERROR_RESPONSES',
    
    # Mock data helpers
    'create_working_time_list_response', 'create_working_time_types_list_response', 
    'create_tasks_list_response', 'create_project_times_list_response',
    'create_working_time_variant', 'create_task_variant', 'create_user_variant'
]
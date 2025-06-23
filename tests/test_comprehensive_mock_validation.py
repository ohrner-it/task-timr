"""
Comprehensive mock validation tests using the new validation framework.
"""

import unittest
import json
import os
from timr_api import TimrApi
from config import COMPANY_ID
from tests.utils import (
    MockValidator, validate_mock_against_real, extract_structure_template,
    REALISTIC_LOGIN_RESPONSE, REALISTIC_WORKING_TIME, REALISTIC_WORKING_TIME_TYPE,
    REALISTIC_TASK, REALISTIC_PROJECT_TIME
)


class TestComprehensiveMockValidation(unittest.TestCase):
    """Comprehensive validation of mocks against real API responses."""
    
    @classmethod
    def setUpClass(cls):
        """Set up integration test capability if credentials available."""
        cls.username = os.environ.get("TIMR_USER")
        cls.password = os.environ.get("TIMR_PASSWORD")
        cls.has_credentials = bool(cls.username and cls.password)
        
        if cls.has_credentials:
            cls.api = TimrApi(company_id=COMPANY_ID)
    
    def test_login_response_comprehensive_validation(self):
        """Comprehensive validation of login response mock."""
        if not self.has_credentials:
            self.skipTest("No credentials available for real API comparison")
            
        # Get real API response
        real_response = self.api.login(self.username, self.password)
        
        # Validate our realistic mock against real response
        report = validate_mock_against_real(
            REALISTIC_LOGIN_RESPONSE, 
            real_response, 
            "login_response"
        )
        
        print("\n" + "="*80)
        print("LOGIN RESPONSE VALIDATION")
        print("="*80)
        print(report)
        
        # Use validator to check for critical issues
        validator = MockValidator()
        validator.validate_structure(REALISTIC_LOGIN_RESPONSE, real_response, "login_response")
        
        # Assert no critical issues (warnings are acceptable)
        critical_issues = validator.get_critical_issues()
        if critical_issues:
            critical_details = "\n".join([
                f"- {issue.path}: {issue.issue}" for issue in critical_issues
            ])
            self.fail(f"Critical mock validation issues found:\n{critical_details}")
    
    def test_working_time_comprehensive_validation(self):
        """Comprehensive validation of working time mock."""
        if not self.has_credentials:
            self.skipTest("No credentials available for real API comparison")
            
        # Login first
        self.api.login(self.username, self.password)
        
        # Get real working times
        real_working_times = self.api.get_working_times()
        
        if not real_working_times:
            self.skipTest("No working times available for validation")
            
        real_working_time = real_working_times[0]
        
        # Validate our realistic mock against real response
        report = validate_mock_against_real(
            REALISTIC_WORKING_TIME,
            real_working_time,
            "working_time"
        )
        
        print("\n" + "="*80)
        print("WORKING TIME VALIDATION")
        print("="*80)
        print(report)
        
        # Check for critical issues
        validator = MockValidator()
        validator.validate_structure(REALISTIC_WORKING_TIME, real_working_time, "working_time")
        
        critical_issues = validator.get_critical_issues()
        if critical_issues:
            critical_details = "\n".join([
                f"- {issue.path}: {issue.issue}" for issue in critical_issues
            ])
            self.fail(f"Critical working time mock validation issues found:\n{critical_details}")
    
    def test_working_time_types_comprehensive_validation(self):
        """Comprehensive validation of working time types mock."""
        if not self.has_credentials:
            self.skipTest("No credentials available for real API comparison")
            
        # Get real working time types (no login required)
        real_wt_types = self.api.get_working_time_types()
        
        if not real_wt_types:
            self.skipTest("No working time types available for validation")
            
        real_wt_type = real_wt_types[0]
        
        # Validate our realistic mock against real response
        report = validate_mock_against_real(
            REALISTIC_WORKING_TIME_TYPE,
            real_wt_type,
            "working_time_type"
        )
        
        print("\n" + "="*80)
        print("WORKING TIME TYPE VALIDATION")
        print("="*80)
        print(report)
        
        # Check for critical issues
        validator = MockValidator()
        validator.validate_structure(REALISTIC_WORKING_TIME_TYPE, real_wt_type, "working_time_type")
        
        critical_issues = validator.get_critical_issues()
        if critical_issues:
            critical_details = "\n".join([
                f"- {issue.path}: {issue.issue}" for issue in critical_issues
            ])
            self.fail(f"Critical working time type mock validation issues found:\n{critical_details}")
    
    def test_tasks_comprehensive_validation(self):
        """Comprehensive validation of task mock."""
        if not self.has_credentials:
            self.skipTest("No credentials available for real API comparison")
            
        # Login first
        self.api.login(self.username, self.password)
        
        # Get real tasks
        real_tasks = self.api.get_tasks()
        
        if not real_tasks:
            self.skipTest("No tasks available for validation")
            
        real_task = real_tasks[0]
        
        # Validate our realistic mock against real response
        report = validate_mock_against_real(
            REALISTIC_TASK,
            real_task,
            "task"
        )
        
        print("\n" + "="*80)
        print("TASK VALIDATION")
        print("="*80)
        print(report)
        
        # Check for critical issues
        validator = MockValidator()
        validator.validate_structure(REALISTIC_TASK, real_task, "task")
        
        critical_issues = validator.get_critical_issues()
        if critical_issues:
            critical_details = "\n".join([
                f"- {issue.path}: {issue.issue}" for issue in critical_issues
            ])
            self.fail(f"Critical task mock validation issues found:\n{critical_details}")
    
    def test_generate_structure_templates(self):
        """Generate structure templates from real API responses for documentation."""
        if not self.has_credentials:
            self.skipTest("No credentials available for real API comparison")
            
        print("\n" + "="*80)
        print("STRUCTURE TEMPLATES FROM REAL API")
        print("="*80)
        
        # Login
        login_response = self.api.login(self.username, self.password)
        login_template = extract_structure_template(login_response)
        print("\n### LOGIN RESPONSE TEMPLATE:")
        print(json.dumps(login_template, indent=2))
        
        # Working times
        working_times = self.api.get_working_times()
        if working_times:
            wt_template = extract_structure_template(working_times[0])
            print("\n### WORKING TIME TEMPLATE:")
            print(json.dumps(wt_template, indent=2))
        
        # Working time types
        wt_types = self.api.get_working_time_types()
        if wt_types:
            wtt_template = extract_structure_template(wt_types[0])
            print("\n### WORKING TIME TYPE TEMPLATE:")
            print(json.dumps(wtt_template, indent=2))
        
        # Tasks
        tasks = self.api.get_tasks()
        if tasks:
            task_template = extract_structure_template(tasks[0])
            print("\n### TASK TEMPLATE:")
            print(json.dumps(task_template, indent=2))
    
    def test_validate_old_mock_structures(self):
        """Validate old-style mocks to show improvement needed."""
        if not self.has_credentials:
            self.skipTest("No credentials available for real API comparison")
            
        # Example of old-style simple mock
        old_login_mock = {
            'token': 'test-token',
            'user': {'id': 'user1', 'fullname': 'Test User'}
        }
        
        old_working_time_mock = {
            'id': 'wt1',
            'start': '2025-04-01T09:00:00Z',
            'end': '2025-04-01T17:00:00Z'
        }
        
        # Get real responses
        real_login = self.api.login(self.username, self.password)
        real_working_times = self.api.get_working_times()
        
        print("\n" + "="*80)
        print("OLD MOCK VALIDATION (SHOWS PROBLEMS)")
        print("="*80)
        
        # Validate old login mock
        print("\n### OLD LOGIN MOCK VALIDATION:")
        old_login_report = validate_mock_against_real(old_login_mock, real_login, "old_login_mock")
        print(old_login_report)
        
        # Validate old working time mock
        if real_working_times:
            print("\n### OLD WORKING TIME MOCK VALIDATION:")
            old_wt_report = validate_mock_against_real(old_working_time_mock, real_working_times[0], "old_working_time_mock")
            print(old_wt_report)
    
    def test_bidirectional_field_validation(self):
        """Test that bidirectional validation catches both missing and extra fields."""
        # Create test data with known issues
        incomplete_mock = {
            'token': 'test-token',
            # Missing 'alias', 'valid_until', incomplete user
            'user': {
                'id': 'test-user-id',
                # Missing firstname, lastname, email, etc.
            },
            'extra_field': 'should not be here'  # Extra field
        }
        
        real_login_sample = {
            'token': 'real-token-123',
            'alias': None,
            'valid_until': None,
            'user': {
                'id': 'real-user-id-456',
                'firstname': 'Real',
                'lastname': 'User',
                'fullname': 'Real User',
                'email': 'real@example.com',
                'employee_number': 'EMP123',
                'external_id': 'EXT123'
            }
        }
        
        validator = MockValidator()
        validator.validate_structure(incomplete_mock, real_login_sample, "test_bidirectional")
        
        # Should find missing fields
        missing_field_issues = [issue for issue in validator.issues if issue.category == "missing_field"]
        self.assertGreater(len(missing_field_issues), 0, "Should detect missing fields")
        
        # Should find extra fields
        extra_field_issues = [issue for issue in validator.issues if issue.category == "extra_field"]
        self.assertGreater(len(extra_field_issues), 0, "Should detect extra fields")
        
        # Should find type mismatches if any
        print(f"\nBidirectional validation found {len(validator.issues)} issues:")
        print(validator.generate_report())
    
    def test_type_validation(self):
        """Test that type validation catches data type mismatches."""
        mock_with_wrong_types = {
            'id': 123,  # Should be string
            'name': ['wrong', 'type'],  # Should be string
            'count': '456',  # Should be int
            'active': 'true'  # Should be boolean
        }
        
        real_data_sample = {
            'id': 'real-id-789',
            'name': 'Real Name',
            'count': 456,
            'active': True
        }
        
        validator = MockValidator()
        validator.validate_structure(mock_with_wrong_types, real_data_sample, "test_types")
        
        # Should find type mismatches
        type_issues = [issue for issue in validator.issues if issue.category == "type_mismatch"]
        self.assertEqual(len(type_issues), 4, "Should detect all 4 type mismatches")
        
        print(f"\nType validation found {len(type_issues)} type mismatches:")
        for issue in type_issues:
            print(f"- {issue.path}: {issue.issue}")
    
    def test_format_validation(self):
        """Test that string format validation works."""
        mock_with_wrong_formats = {
            'id': 'simple-id',  # Should be UUID format
            'email': 'not-an-email',  # Should be email format
            'created_at': '2025-01-01'  # Should be ISO datetime format
        }
        
        real_data_sample = {
            'id': '12345678-1234-1234-1234-123456789abc',
            'email': 'real@example.com',
            'created_at': '2025-01-01T10:30:00+00:00'
        }
        
        validator = MockValidator()
        validator.validate_structure(mock_with_wrong_formats, real_data_sample, "test_formats")
        
        # Should find format mismatches
        format_issues = [issue for issue in validator.issues if issue.category == "format_mismatch"]
        self.assertGreater(len(format_issues), 0, "Should detect format mismatches")
        
        print(f"\nFormat validation found {len(format_issues)} format issues:")
        for issue in format_issues:
            print(f"- {issue.path}: {issue.issue}")


if __name__ == '__main__':
    unittest.main()
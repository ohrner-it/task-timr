"""
Comprehensive tests for stacktrace handling in the enhanced error system.
Tests the intelligent stacktrace inclusion logic based on error context.

Copyright (c) 2025 Ohrner IT GmbH
Licensed under the MIT License
"""

import unittest
import logging
from unittest.mock import Mock, patch
from io import StringIO

from error_handler import (
    EnhancedErrorHandler, ErrorCategory, ErrorSeverity, ErrorContext
)


class TestStacktraceHandling(unittest.TestCase):
    """Test systematic stacktrace inclusion in error logs."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a test logger with string capture
        self.log_capture_string = StringIO()
        self.log_handler = logging.StreamHandler(self.log_capture_string)
        
        # Set up formatter to capture full log output including tracebacks
        formatter = logging.Formatter('%(levelname)s:%(name)s:%(message)s')
        self.log_handler.setFormatter(formatter)
        
        self.test_logger = logging.getLogger('test_stacktrace')
        self.test_logger.handlers.clear()
        self.test_logger.addHandler(self.log_handler)
        self.test_logger.setLevel(logging.DEBUG)
        
        # Create error handler with test logger
        self.error_handler = EnhancedErrorHandler('test_stacktrace')
        self.error_handler.logger = self.test_logger
    
    def tearDown(self):
        """Clean up test fixtures."""
        self.test_logger.removeHandler(self.log_handler)
        self.log_handler.close()
    
    def test_stacktrace_included_for_critical_severity(self):
        """Test that critical errors always include stacktraces."""
        try:
            raise RuntimeError("Critical system failure")
        except Exception as e:
            self.error_handler.log_error(
                error=e,
                context=ErrorContext(
                    category=ErrorCategory.SYSTEM,
                    severity=ErrorSeverity.CRITICAL,
                    operation="critical_operation"
                )
            )
        
        log_output = self.log_capture_string.getvalue()
        self.assertIn("Traceback", log_output)
        self.assertIn("RuntimeError: Critical system failure", log_output)
        self.assertIn("test_stacktrace_included_for_critical_severity", log_output)
    
    def test_stacktrace_included_for_high_severity(self):
        """Test that high severity errors include stacktraces."""
        try:
            raise ValueError("High severity error")
        except Exception as e:
            self.error_handler.log_error(
                error=e,
                context=ErrorContext(
                    category=ErrorCategory.TIMR_API_ERROR,
                    severity=ErrorSeverity.HIGH,
                    operation="high_severity_operation"
                )
            )
        
        log_output = self.log_capture_string.getvalue()
        self.assertIn("Traceback", log_output)
        self.assertIn("ValueError: High severity error", log_output)
    
    def test_stacktrace_included_for_system_errors(self):
        """Test that system errors always include stacktraces regardless of severity."""
        try:
            raise ConnectionError("Database connection lost")
        except Exception as e:
            self.error_handler.log_error(
                error=e,
                context=ErrorContext(
                    category=ErrorCategory.SYSTEM,
                    severity=ErrorSeverity.MEDIUM,  # Even medium severity
                    operation="database_operation"
                )
            )
        
        log_output = self.log_capture_string.getvalue()
        self.assertIn("Traceback", log_output)
        self.assertIn("ConnectionError: Database connection lost", log_output)
    
    def test_stacktrace_included_for_5xx_api_errors(self):
        """Test that server-side API errors (5xx) include stacktraces."""
        try:
            raise RuntimeError("Internal server error")
        except Exception as e:
            self.error_handler.log_error(
                error=e,
                context=ErrorContext(
                    category=ErrorCategory.TIMR_API_ERROR,
                    severity=ErrorSeverity.MEDIUM,
                    operation="api_request",
                    api_status_code=500
                )
            )
        
        log_output = self.log_capture_string.getvalue()
        self.assertIn("Traceback", log_output)
        self.assertIn("RuntimeError: Internal server error", log_output)
    
    def test_stacktrace_included_for_network_errors(self):
        """Test that network errors include stacktraces."""
        try:
            raise ConnectionError("Network timeout")
        except Exception as e:
            self.error_handler.log_error(
                error=e,
                context=ErrorContext(
                    category=ErrorCategory.NETWORK,
                    severity=ErrorSeverity.MEDIUM,
                    operation="network_request"
                )
            )
        
        log_output = self.log_capture_string.getvalue()
        self.assertIn("Traceback", log_output)
        self.assertIn("ConnectionError: Network timeout", log_output)
    
    def test_stacktrace_included_for_authorization_errors(self):
        """Test that authorization errors include stacktraces (may indicate config issues)."""
        try:
            raise PermissionError("Access denied to resource")
        except Exception as e:
            self.error_handler.log_error(
                error=e,
                context=ErrorContext(
                    category=ErrorCategory.AUTHORIZATION,
                    severity=ErrorSeverity.MEDIUM,
                    operation="resource_access"
                )
            )
        
        log_output = self.log_capture_string.getvalue()
        self.assertIn("Traceback", log_output)
        self.assertIn("PermissionError: Access denied to resource", log_output)
    
    def test_stacktrace_excluded_for_business_rule_violations(self):
        """Test that business rule violations do not include stacktraces."""
        try:
            raise ValueError("Task is not bookable")
        except Exception as e:
            self.error_handler.log_error(
                error=e,
                context=ErrorContext(
                    category=ErrorCategory.TIMR_BUSINESS_RULE,
                    severity=ErrorSeverity.MEDIUM,
                    operation="create_project_time"
                )
            )
        
        log_output = self.log_capture_string.getvalue()
        self.assertNotIn("Traceback", log_output)
        self.assertIn("[TIMR_BUSINESS_RULE]", log_output)
    
    def test_stacktrace_excluded_for_validation_errors(self):
        """Test that validation errors do not include stacktraces."""
        try:
            raise ValueError("Duration must be positive")
        except Exception as e:
            self.error_handler.log_error(
                error=e,
                context=ErrorContext(
                    category=ErrorCategory.DATA_VALIDATION,
                    severity=ErrorSeverity.LOW,
                    operation="validate_duration"
                )
            )
        
        log_output = self.log_capture_string.getvalue()
        self.assertNotIn("Traceback", log_output)
        self.assertIn("[DATA_VALIDATION]", log_output)
    
    def test_stacktrace_excluded_for_authentication_errors(self):
        """Test that authentication errors do not include stacktraces."""
        try:
            raise ValueError("Invalid credentials")
        except Exception as e:
            self.error_handler.log_error(
                error=e,
                context=ErrorContext(
                    category=ErrorCategory.AUTHENTICATION,
                    severity=ErrorSeverity.MEDIUM,
                    operation="user_login"
                )
            )
        
        log_output = self.log_capture_string.getvalue()
        self.assertNotIn("Traceback", log_output)
        self.assertIn("[AUTHENTICATION]", log_output)
    
    def test_stacktrace_excluded_for_4xx_api_errors_medium_severity(self):
        """Test that client-side API errors (4xx) with medium severity exclude stacktraces."""
        try:
            raise ValueError("Bad request")
        except Exception as e:
            self.error_handler.log_error(
                error=e,
                context=ErrorContext(
                    category=ErrorCategory.TIMR_API_ERROR,
                    severity=ErrorSeverity.MEDIUM,
                    operation="api_request",
                    api_status_code=400
                )
            )
        
        log_output = self.log_capture_string.getvalue()
        self.assertNotIn("Traceback", log_output)
        self.assertIn("[TIMR_API_ERROR]", log_output)
    
    def test_stacktrace_included_for_4xx_api_errors_high_severity(self):
        """Test that client-side API errors (4xx) with high severity include stacktraces."""
        try:
            raise ValueError("Critical validation failure")
        except Exception as e:
            self.error_handler.log_error(
                error=e,
                context=ErrorContext(
                    category=ErrorCategory.TIMR_API_ERROR,
                    severity=ErrorSeverity.HIGH,
                    operation="critical_api_request",
                    api_status_code=422
                )
            )
        
        log_output = self.log_capture_string.getvalue()
        self.assertIn("Traceback", log_output)
        self.assertIn("ValueError: Critical validation failure", log_output)
    
    def test_stacktrace_excluded_for_low_severity_info_logs(self):
        """Test that low severity errors logged as INFO exclude stacktraces."""
        try:
            raise ValueError("Minor validation issue")
        except Exception as e:
            self.error_handler.log_error(
                error=e,
                context=ErrorContext(
                    category=ErrorCategory.USER_INPUT,
                    severity=ErrorSeverity.LOW,
                    operation="input_validation"
                )
            )
        
        log_output = self.log_capture_string.getvalue()
        self.assertNotIn("Traceback", log_output)
        self.assertIn("INFO:", log_output)
    
    def test_explicit_stacktrace_override(self):
        """Test that explicit stacktrace parameter overrides automatic detection."""
        # Test explicit inclusion
        try:
            raise ValueError("Business rule with forced stacktrace")
        except Exception as e:
            self.error_handler.log_error(
                error=e,
                context=ErrorContext(
                    category=ErrorCategory.TIMR_BUSINESS_RULE,
                    severity=ErrorSeverity.MEDIUM,
                    operation="business_rule_debug"
                ),
                include_stacktrace=True  # Force inclusion
            )
        
        log_output = self.log_capture_string.getvalue()
        self.assertIn("Traceback", log_output)
        
        # Clear log for next test
        self.log_capture_string.truncate(0)
        self.log_capture_string.seek(0)
        
        # Test explicit exclusion
        try:
            raise RuntimeError("System error without stacktrace")
        except Exception as e:
            self.error_handler.log_error(
                error=e,
                context=ErrorContext(
                    category=ErrorCategory.SYSTEM,
                    severity=ErrorSeverity.HIGH,
                    operation="system_error_clean"
                ),
                include_stacktrace=False  # Force exclusion
            )
        
        log_output = self.log_capture_string.getvalue()
        self.assertNotIn("Traceback", log_output)
        self.assertIn("[SYSTEM]", log_output)
    
    def test_convenience_methods_use_appropriate_stacktrace_logic(self):
        """Test that convenience methods use the automatic stacktrace logic."""
        # Business rule violation should not include stacktrace
        self.error_handler.log_business_rule_violation(
            rule_type="test_rule",
            details="Test business rule violation",
            user_id="user_123"
        )
        
        log_output = self.log_capture_string.getvalue()
        self.assertNotIn("Traceback", log_output)
        self.assertIn("[TIMR_BUSINESS_RULE]", log_output)
        
        # Clear log for next test
        self.log_capture_string.truncate(0)
        self.log_capture_string.seek(0)
        
        # Validation error should not include stacktrace
        self.error_handler.log_validation_error(
            field="test_field",
            value="invalid_value",
            reason="test reason",
            user_id="user_123"
        )
        
        log_output = self.log_capture_string.getvalue()
        self.assertNotIn("Traceback", log_output)
        self.assertIn("[DATA_VALIDATION]", log_output)
    
    def test_stacktrace_contains_meaningful_call_stack(self):
        """Test that included stacktraces contain meaningful call stack information."""
        def inner_function():
            raise RuntimeError("Deep stack error")
        
        def middle_function():
            return inner_function()
        
        def outer_function():
            return middle_function()
        
        try:
            outer_function()
        except Exception as e:
            self.error_handler.log_error(
                error=e,
                context=ErrorContext(
                    category=ErrorCategory.SYSTEM,
                    severity=ErrorSeverity.CRITICAL,
                    operation="multi_level_operation"
                )
            )
        
        log_output = self.log_capture_string.getvalue()
        
        # Verify full call stack is present
        self.assertIn("Traceback", log_output)
        self.assertIn("outer_function", log_output)
        self.assertIn("middle_function", log_output)
        self.assertIn("inner_function", log_output)
        self.assertIn("RuntimeError: Deep stack error", log_output)


class TestStacktraceEdgeCases(unittest.TestCase):
    """Test edge cases in stacktrace handling."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.log_capture_string = StringIO()
        self.log_handler = logging.StreamHandler(self.log_capture_string)
        
        self.test_logger = logging.getLogger('test_edge_cases')
        self.test_logger.handlers.clear()
        self.test_logger.addHandler(self.log_handler)
        self.test_logger.setLevel(logging.DEBUG)
        
        self.error_handler = EnhancedErrorHandler('test_edge_cases')
        self.error_handler.logger = self.test_logger
    
    def tearDown(self):
        """Clean up test fixtures."""
        self.test_logger.removeHandler(self.log_handler)
        self.log_handler.close()
    
    def test_none_status_code_defaults_to_network_error(self):
        """Test that None status code in API errors defaults to network error behavior."""
        try:
            raise ConnectionError("Connection failed")
        except Exception as e:
            self.error_handler.log_api_error(
                error=e,
                endpoint="/test",
                status_code=None,  # No status code
                user_id="user_123"
            )
        
        log_output = self.log_capture_string.getvalue()
        self.assertIn("Traceback", log_output)  # Network errors should include stacktrace
        self.assertIn("[NETWORK]", log_output)
    
    def test_unknown_status_code_includes_stacktrace(self):
        """Test that unknown status codes default to including stacktrace."""
        try:
            raise ValueError("Unknown status error")
        except Exception as e:
            self.error_handler.log_error(
                error=e,
                context=ErrorContext(
                    category=ErrorCategory.TIMR_API_ERROR,
                    severity=ErrorSeverity.MEDIUM,
                    operation="unknown_status",
                    api_status_code=999  # Unknown status code
                )
            )
        
        log_output = self.log_capture_string.getvalue()
        self.assertIn("Traceback", log_output)  # Should include by default
    
    def test_missing_context_fields_handled_gracefully(self):
        """Test that missing context fields don't break stacktrace logic."""
        try:
            raise ValueError("Minimal context error")
        except Exception as e:
            self.error_handler.log_error(
                error=e,
                context=ErrorContext(
                    category=ErrorCategory.SYSTEM,
                    severity=ErrorSeverity.HIGH,
                    operation="minimal_context"
                    # No optional fields provided
                )
            )
        
        log_output = self.log_capture_string.getvalue()
        self.assertIn("Traceback", log_output)  # Should still work
        self.assertIn("[SYSTEM]", log_output)


if __name__ == '__main__':
    unittest.main()
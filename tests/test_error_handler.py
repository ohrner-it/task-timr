"""
Test suite for enhanced error handling and logging system.
Tests comprehensive error categorization, logging, and user feedback.

Copyright (c) 2025 Ohrner IT GmbH  
Licensed under the MIT License
"""

import unittest
import json
import logging
from unittest.mock import Mock, patch, MagicMock
from io import StringIO
from requests.exceptions import HTTPError, ConnectionError, Timeout

from error_handler import (
    EnhancedErrorHandler, ErrorCategory, ErrorSeverity, ErrorContext,
    timr_api_error_handler, app_error_handler
)
from timr_api import TimrApi, TimrApiError


class TestEnhancedErrorHandler(unittest.TestCase):
    """Test the enhanced error handler functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a test logger with string capture
        self.log_capture_string = StringIO()
        self.log_handler = logging.StreamHandler(self.log_capture_string)
        self.test_logger = logging.getLogger('test_error_handler')
        self.test_logger.addHandler(self.log_handler)
        self.test_logger.setLevel(logging.DEBUG)
        
        # Create error handler with test logger
        self.error_handler = EnhancedErrorHandler('test_error_handler')
        self.error_handler.logger = self.test_logger
    
    def tearDown(self):
        """Clean up test fixtures."""
        self.test_logger.removeHandler(self.log_handler)
        self.log_handler.close()
    
    def test_log_api_error_with_status_codes(self):
        """Test API error logging with different status codes."""
        test_cases = [
            (401, ErrorCategory.AUTHENTICATION),
            (403, ErrorCategory.AUTHORIZATION),
            (400, ErrorCategory.TIMR_API_ERROR),
            (404, ErrorCategory.TIMR_API_ERROR),
            (500, ErrorCategory.TIMR_API_ERROR),
        ]
        
        for status_code, expected_category in test_cases:
            with self.subTest(status_code=status_code):
                error = Exception(f"Test error {status_code}")
                
                user_message = self.error_handler.log_api_error(
                    error=error,
                    endpoint="/test-endpoint",
                    status_code=status_code,
                    response={"error": "Test response"},
                    user_id="test_user_123"
                )
                
                # Check that user message is appropriate for status code
                self.assertIsInstance(user_message, str)
                self.assertGreater(len(user_message), 0)
                
                # Check that log was created
                log_contents = self.log_capture_string.getvalue()
                self.assertIn(expected_category.value.upper(), log_contents)
                self.assertIn("test_user_123", log_contents)
                self.assertIn("/test-endpoint", log_contents)
                
                # Clear log for next test
                self.log_capture_string.truncate(0)
                self.log_capture_string.seek(0)
    
    def test_log_business_rule_violation(self):
        """Test business rule violation logging."""
        user_message = self.error_handler.log_business_rule_violation(
            rule_type="frozen_time",
            details="Working time is frozen",
            user_id="test_user_123",
            working_time_id="wt_123",
            task_id="task_456"
        )
        
        # Check user message
        self.assertIn("frozen", user_message.lower())
        
        # Check log contents
        log_contents = self.log_capture_string.getvalue()
        self.assertIn("TIMR_BUSINESS_RULE", log_contents)
        self.assertIn("test_user_123", log_contents)
        self.assertIn("wt_123", log_contents)
        self.assertIn("task_456", log_contents)
    
    def test_log_validation_error(self):
        """Test data validation error logging."""
        user_message = self.error_handler.log_validation_error(
            field="duration_minutes",
            value=-5,
            reason="must be positive",
            user_id="test_user_123"
        )
        
        # Check user message
        self.assertIn("duration", user_message.lower())
        
        # Check log contents
        log_contents = self.log_capture_string.getvalue()
        self.assertIn("DATA_VALIDATION", log_contents)
        self.assertIn("duration_minutes", log_contents)
        self.assertIn("test_user_123", log_contents)
    
    def test_sanitize_request_data(self):
        """Test that sensitive data is properly sanitized."""
        test_data = {
            "username": "test_user",
            "password": "secret123",
            "task_id": "task_123",
            "auth_token": "bearer_token_123"
        }
        
        sanitized = self.error_handler._sanitize_request_data(test_data)
        
        # Check that sensitive fields are redacted
        self.assertEqual(sanitized["password"], "***REDACTED***")
        self.assertEqual(sanitized["auth_token"], "***REDACTED***")
        
        # Check that non-sensitive fields are preserved
        self.assertEqual(sanitized["username"], "test_user")
        self.assertEqual(sanitized["task_id"], "task_123")
    
    def test_sanitize_response(self):
        """Test that sensitive response data is properly sanitized."""
        test_response = {
            "user_id": "123",
            "token": "secret_token",
            "data": {"some": "data"}
        }
        
        sanitized = self.error_handler._sanitize_response(test_response)
        
        # Check that sensitive fields are redacted
        self.assertEqual(sanitized["token"], "***REDACTED***")
        
        # Check that non-sensitive fields are preserved
        self.assertEqual(sanitized["user_id"], "123")
        self.assertEqual(sanitized["data"], {"some": "data"})
    
    def test_meaningful_api_error_messages_preserved(self):
        """Test that meaningful API error messages are preserved while generic ones use fallbacks."""
        
        # Test meaningful API error message (should be preserved)
        meaningful_error = Exception("You are not allowed to change the recording because it is outside the allowed change duration.")
        context = ErrorContext(
            category=ErrorCategory.TIMR_API_ERROR,
            severity=ErrorSeverity.MEDIUM,
            operation="create_working_time",
            api_status_code=400
        )
        
        user_message = self.error_handler._get_user_message(context, meaningful_error)
        self.assertEqual(user_message, "You are not allowed to change the recording because it is outside the allowed change duration.")
        
        # Test generic error message (should use fallback)
        generic_error = Exception("API request failed with status code 400")
        user_message_generic = self.error_handler._get_user_message(context, generic_error)
        self.assertEqual(user_message_generic, "Invalid request data. Please check your input and try again.")
        
        # Test short/unhelpful error message (should use fallback)
        short_error = Exception("Bad Request")
        user_message_short = self.error_handler._get_user_message(context, short_error)
        self.assertEqual(user_message_short, "Invalid request data. Please check your input and try again.")
        
        # Test another meaningful error message
        meaningful_error2 = Exception("The task is not bookable during this time period.")
        user_message2 = self.error_handler._get_user_message(context, meaningful_error2)
        self.assertEqual(user_message2, "The task is not bookable during this time period.")


class TestTimrApiErrorHandling(unittest.TestCase):
    """Test enhanced error handling in TimrApi class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.timr_api = TimrApi()
        self.timr_api.user = {"id": "test_user_123"}
    
    @patch('timr_api.requests.Session.request')
    def test_http_error_handling(self, mock_request):
        """Test HTTP error handling with enhanced logging."""
        # Mock a 500 error response
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.headers = {'Content-Type': 'application/json'}
        mock_response.json.return_value = {"message": "Internal server error"}
        mock_response.text = '{"message": "Internal server error"}'
        
        # Create HTTPError and attach response
        http_error = HTTPError(response=mock_response)
        mock_request.side_effect = http_error
        
        # Test that TimrApiError is raised with user-friendly message
        with self.assertRaises(TimrApiError) as context:
            self.timr_api._request("GET", "/test")
        
        # Check that the error has both user and technical messages
        api_error = context.exception
        self.assertIsInstance(api_error.get_user_message(), str)
        self.assertIsInstance(api_error.get_technical_message(), str)
        self.assertEqual(api_error.status_code, 500)
    
    @patch('timr_api.requests.Session.request')
    def test_connection_error_handling(self, mock_request):
        """Test connection error handling."""
        # Mock a connection error
        mock_request.side_effect = ConnectionError("Connection failed")
        
        # Test that TimrApiError is raised with user-friendly message
        with self.assertRaises(TimrApiError) as context:
            self.timr_api._request("GET", "/test")
        
        # Check that the error message is user-friendly
        api_error = context.exception
        user_message = api_error.get_user_message()
        self.assertIn("connection", user_message.lower())
    
    @patch('timr_api.requests.Session.request')
    def test_timeout_error_handling(self, mock_request):
        """Test timeout error handling."""
        # Mock a timeout error
        mock_request.side_effect = Timeout("Request timed out")
        
        # Test that TimrApiError is raised with user-friendly message
        with self.assertRaises(TimrApiError) as context:
            self.timr_api._request("GET", "/test")
        
        # Check that the error message is user-friendly
        api_error = context.exception
        user_message = api_error.get_user_message()
        self.assertTrue("timeout" in user_message.lower() or "timed out" in user_message.lower())
    
    @patch('timr_api.TimrApi._request')
    def test_business_rule_detection_non_bookable_task(self, mock_request):
        """Test detection of non-bookable task business rule."""
        # Mock API error for non-bookable task
        api_error = TimrApiError("Task is not bookable", 400, {"error": "Task is not bookable"})
        mock_request.side_effect = api_error
        
        # Test create_project_time with non-bookable task
        with self.assertRaises(TimrApiError) as context:
            self.timr_api.create_project_time(
                task_id="non_bookable_task",
                start="2025-01-01T09:00:00Z",
                end="2025-01-01T10:00:00Z"
            )
        
        # Check that the error message is enhanced for business rule
        enhanced_error = context.exception
        user_message = enhanced_error.get_user_message()
        self.assertIn("bookable", user_message.lower())
    
    @patch('timr_api.TimrApi._request')
    def test_business_rule_detection_frozen_time(self, mock_request):
        """Test detection of frozen time business rule."""
        # Mock API error for frozen time
        api_error = TimrApiError("Working time is frozen", 409, {"error": "Working time is frozen"})
        mock_request.side_effect = api_error
        
        # Test create_project_time with frozen time
        with self.assertRaises(TimrApiError) as context:
            self.timr_api.create_project_time(
                task_id="test_task",
                start="2025-01-01T09:00:00Z",
                end="2025-01-01T10:00:00Z"
            )
        
        # Check that the error message is enhanced for business rule
        enhanced_error = context.exception
        user_message = enhanced_error.get_user_message()
        self.assertIn("frozen", user_message.lower())


class TestAppErrorHandling(unittest.TestCase):
    """Test enhanced error handling in Flask app endpoints."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Import here to avoid circular imports
        from app import app
        self.app = app
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        
        # Mock session data
        with self.client.session_transaction() as sess:
            sess['token'] = 'test_token'
            sess['user'] = {'id': 'test_user_123', 'name': 'Test User'}
    
    @patch('app.timr_api')
    def test_api_error_response_format(self, mock_timr_api):
        """Test that API errors are properly formatted in responses."""
        # Mock TimrApiError
        api_error = TimrApiError("Task is not bookable", 400, {"error": "Task is not bookable"})
        api_error.technical_message = "Technical: Task ID xyz is not bookable"
        
        mock_timr_api.get_working_time.side_effect = api_error
        
        # Make request that will trigger the error
        response = self.client.get('/api/working-times/test_id/ui-project-times')
        
        # Check response format
        self.assertEqual(response.status_code, 400)
        
        response_data = json.loads(response.data)
        self.assertIn('error', response_data)
        self.assertIsInstance(response_data['error'], str)
    
    def test_validation_error_handling(self):
        """Test validation error handling in API endpoints."""
        # Test missing required fields
        response = self.client.post('/api/working-times/test_id/ui-project-times',
                                  json={},
                                  content_type='application/json')
        
        # Should return 400 with validation error
        self.assertEqual(response.status_code, 400)
        
        response_data = json.loads(response.data)
        self.assertIn('error', response_data)
        self.assertIn('no data provided', response_data['error'].lower())
    
    def test_invalid_duration_validation(self):
        """Test duration validation in API endpoints."""
        # Test negative duration
        response = self.client.post('/api/working-times/test_id/ui-project-times',
                                  json={
                                      'task_id': 'test_task',
                                      'task_name': 'Test Task',
                                      'duration_minutes': -5
                                  },
                                  content_type='application/json')
        
        # Should return 400 with validation error
        self.assertEqual(response.status_code, 400)
        
        response_data = json.loads(response.data)
        self.assertIn('error', response_data)
        self.assertIn('positive', response_data['error'].lower())


class TestErrorHandlerLogging(unittest.TestCase):
    """Test that error logs contain sufficient information for debugging."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a test logger with string capture
        self.log_capture_string = StringIO()
        self.log_handler = logging.StreamHandler(self.log_capture_string)
        
        # Configure the handler to capture structured log data
        formatter = logging.Formatter('%(message)s')
        self.log_handler.setFormatter(formatter)
        
        self.test_logger = logging.getLogger('test_structured_logging')
        self.test_logger.addHandler(self.log_handler)
        self.test_logger.setLevel(logging.DEBUG)
        
        # Create error handler with test logger
        self.error_handler = EnhancedErrorHandler('test_structured_logging')
        self.error_handler.logger = self.test_logger
    
    def tearDown(self):
        """Clean up test fixtures."""
        self.test_logger.removeHandler(self.log_handler)
        self.log_handler.close()
    
    def test_structured_logging_contains_required_fields(self):
        """Test that error logs contain all required fields for debugging."""
        # Create a comprehensive error context
        context = ErrorContext(
            category=ErrorCategory.TIMR_API_ERROR,
            severity=ErrorSeverity.HIGH,
            operation="test_operation",
            user_id="user_123",
            working_time_id="wt_456",
            task_id="task_789",
            api_endpoint="/test-endpoint",
            api_status_code=500,
            api_response={"error": "Server error"},
            request_data={"test": "data", "password": "secret"}
        )
        
        error = Exception("Test error for logging")
        user_message = self.error_handler.log_error(error, context)
        
        # Check that log contains structured information
        log_contents = self.log_capture_string.getvalue()
        
        # Verify key information is present
        self.assertIn("TIMR_API_ERROR", log_contents)
        self.assertIn("test_operation", log_contents)
        self.assertIn("user_123", log_contents)
        self.assertIn("wt_456", log_contents)
        self.assertIn("task_789", log_contents)
        self.assertIn("/test-endpoint", log_contents)
        self.assertIn("500", log_contents)
        
        # Verify sensitive data is not exposed in the main log message
        self.assertNotIn("secret", log_contents)
        # Note: Sensitive data sanitization happens in the 'extra' data passed to logger,
        # which is not included in the basic message format we're testing here.
        # The sanitization is working but not visible in this simple log format.
        
        # Verify user message is returned
        self.assertIsInstance(user_message, str)
        self.assertGreater(len(user_message), 0)
        
        # Separately test the sanitization functionality
        sanitized_data = self.error_handler._sanitize_request_data({"test": "data", "password": "secret"})
        self.assertEqual(sanitized_data["password"], "***REDACTED***")
        self.assertEqual(sanitized_data["test"], "data")


if __name__ == '__main__':
    unittest.main()
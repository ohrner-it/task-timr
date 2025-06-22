"""
Test suite for enhanced API error logging with detailed request/response information.
Tests the new functionality that logs complete request context for debugging API issues.

Copyright (c) 2025 Ohrner IT GmbH
Licensed under the MIT License
"""

import unittest
import json
import logging
from unittest.mock import Mock, patch
from io import StringIO
from requests.exceptions import HTTPError, ConnectionError, Timeout

from error_handler import (
    EnhancedErrorHandler, ErrorCategory, ErrorSeverity, ErrorContext,
    timr_api_error_handler
)
from timr_api import TimrApi, TimrApiError


class TestEnhancedRequestLogging(unittest.TestCase):
    """Test enhanced request/response logging functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a test logger with string capture
        self.log_capture_string = StringIO()
        self.log_handler = logging.StreamHandler(self.log_capture_string)
        
        # Use a formatter that captures the full message
        formatter = logging.Formatter('%(levelname)s:%(name)s:%(message)s')
        self.log_handler.setFormatter(formatter)
        
        self.test_logger = logging.getLogger('test_enhanced_logging')
        self.test_logger.addHandler(self.log_handler)
        self.test_logger.setLevel(logging.DEBUG)
        
        # Create error handler with test logger
        self.error_handler = EnhancedErrorHandler('test_enhanced_logging')
        self.error_handler.logger = self.test_logger
    
    def tearDown(self):
        """Clean up test fixtures."""
        self.test_logger.removeHandler(self.log_handler)
        self.log_handler.close()
    
    def test_enhanced_request_data_logging(self):
        """Test that enhanced request data is properly logged for API errors."""
        # Create enhanced request data structure as used in timr_api.py
        enhanced_request_data = {
            "method": "POST",
            "url": "https://api.timr.com/v0.2/project-times",
            "params": {"limit": 100, "user": "test-user"},
            "payload": {
                "task_id": "task-123",
                "start": "2025-06-17T10:00:00+00:00",
                "end": "2025-06-17T11:00:00+00:00",
                "password": "secret123"  # Should be masked
            }
        }
        
        error = Exception("Internal Server Error")
        user_message = self.error_handler.log_api_error(
            error=error,
            endpoint="/project-times",
            status_code=500,
            response={"error": "Database connection failed", "code": "DB_ERROR"},
            request_data=enhanced_request_data,
            user_id="user-456",
            operation="POST /project-times"
        )
        
        log_contents = self.log_capture_string.getvalue()
        
        # Verify basic error information is logged
        self.assertIn("TIMR_API_ERROR", log_contents)
        self.assertIn("Internal Server Error", log_contents)
        self.assertIn("user-456", log_contents)
        self.assertIn("status=500", log_contents)
        
        # Verify enhanced request details are logged
        self.assertIn("Request Details:", log_contents)
        self.assertIn("method=POST", log_contents)
        self.assertIn("url=https://api.timr.com/v0.2/project-times", log_contents)
        self.assertIn('"limit": 100', log_contents)
        self.assertIn('"user": "test-user"', log_contents)
        self.assertIn('"task_id": "task-123"', log_contents)
        self.assertIn('"start": "2025-06-17T10:00:00+00:00"', log_contents)
        
        # Verify sensitive data is masked
        self.assertIn('"password": "***REDACTED***"', log_contents)
        self.assertNotIn("secret123", log_contents)
        
        # Verify response details are logged
        self.assertIn("Response Details:", log_contents)
        self.assertIn('"error": "Database connection failed"', log_contents)
        self.assertIn('"code": "DB_ERROR"', log_contents)
        
        # Verify user-friendly message is returned
        self.assertEqual(user_message, "The Timr service is temporarily unavailable. Please try again later.")
    
    def test_nested_sensitive_data_sanitization(self):
        """Test that nested sensitive data is properly sanitized."""
        nested_request_data = {
            "method": "POST",
            "url": "https://api.timr.com/v0.2/login",
            "params": None,
            "payload": {
                "credentials": {
                    "username": "testuser",
                    "password": "topsecret"
                },
                "auth_info": {
                    "token": "bearer123",
                    "api_key": "key456"
                },
                "task_data": {
                    "task_id": "task-789",
                    "duration": 60
                }
            }
        }
        
        error = Exception("Authentication failed")
        self.error_handler.log_api_error(
            error=error,
            endpoint="/login",
            status_code=401,
            request_data=nested_request_data,
            operation="POST /login"
        )
        
        log_contents = self.log_capture_string.getvalue()
        
        # Verify nested sensitive data is masked
        self.assertIn('"password": "***REDACTED***"', log_contents)
        # auth_info is completely redacted because it contains "auth" in the key name
        self.assertIn('"auth_info": "***REDACTED***"', log_contents)
        
        # Verify non-sensitive nested data is preserved
        self.assertIn('"username": "testuser"', log_contents)
        self.assertIn('"task_id": "task-789"', log_contents)
        self.assertIn('"duration": 60', log_contents)
        
        # Verify actual secrets don't appear anywhere
        self.assertNotIn("topsecret", log_contents)
        # Note: bearer123 and key456 are inside auth_info which is completely redacted
    
    def test_logging_level_for_different_error_types(self):
        """Test that enhanced request details are logged at appropriate levels."""
        enhanced_request_data = {
            "method": "DELETE",
            "url": "https://api.timr.com/v0.2/project-times/123",
            "params": None,
            "payload": None
        }
        
        # Test 500 error (should be ERROR level)
        error_500 = Exception("Internal Server Error")
        self.error_handler.log_api_error(
            error=error_500,
            endpoint="/project-times/123",
            status_code=500,
            request_data=enhanced_request_data,
            operation="DELETE /project-times/123"
        )
        
        log_contents = self.log_capture_string.getvalue()
        self.assertIn("ERROR:test_enhanced_logging", log_contents)
        self.assertIn("Request Details:", log_contents)
        self.assertIn("method=DELETE", log_contents)
        
        # Clear log for next test
        self.log_capture_string.truncate(0)
        self.log_capture_string.seek(0)
        
        # Test 401 error (should be WARNING level but still include request details)
        error_401 = Exception("Unauthorized")
        self.error_handler.log_api_error(
            error=error_401,
            endpoint="/project-times/123",
            status_code=401,
            request_data=enhanced_request_data,
            operation="DELETE /project-times/123"
        )
        
        log_contents = self.log_capture_string.getvalue()
        self.assertIn("WARNING:test_enhanced_logging", log_contents)
        # Request details should still be logged for debugging even at WARNING level
        self.assertIn("Request Details:", log_contents)
    
    def test_response_details_logging(self):
        """Test detailed response logging for different response types."""
        enhanced_request_data = {
            "method": "GET",
            "url": "https://api.timr.com/v0.2/tasks",
            "params": {"active": True},
            "payload": None
        }
        
        # Test JSON response
        json_response = {
            "error": "Task not found",
            "error_code": "TASK_404",
            "details": {
                "task_id": "nonexistent-task",
                "suggestion": "Check task ID"
            },
            "auth_token": "should_be_masked"  # Should be masked
        }
        
        error = Exception("Not Found")
        self.error_handler.log_api_error(
            error=error,
            endpoint="/tasks",
            status_code=404,
            response=json_response,
            request_data=enhanced_request_data,
            operation="GET /tasks"
        )
        
        log_contents = self.log_capture_string.getvalue()
        
        # Verify response details are logged
        self.assertIn("Response Details:", log_contents)
        self.assertIn('"error": "Task not found"', log_contents)
        self.assertIn('"error_code": "TASK_404"', log_contents)
        self.assertIn('"task_id": "nonexistent-task"', log_contents)
        
        # Verify sensitive response data is masked
        self.assertIn('"auth_token": "***REDACTED***"', log_contents)
        self.assertNotIn("should_be_masked", log_contents)
        
        # Clear log for text response test
        self.log_capture_string.truncate(0)
        self.log_capture_string.seek(0)
        
        # Test text response
        text_response = "Server temporarily unavailable. Please try again later."
        self.error_handler.log_api_error(
            error=Exception("Service Unavailable"),
            endpoint="/tasks",
            status_code=503,
            response=text_response,
            request_data=enhanced_request_data,
            operation="GET /tasks"
        )
        
        log_contents = self.log_capture_string.getvalue()
        self.assertIn("Response Details: Server temporarily unavailable", log_contents)
    
    def test_legacy_request_data_compatibility(self):
        """Test that legacy request data format still works."""
        # Test with old-style request data (just the payload)
        legacy_request_data = {
            "task_id": "task-456",
            "start": "2025-06-17T14:00:00+00:00",
            "end": "2025-06-17T15:00:00+00:00"
        }
        
        error = Exception("Validation Error")
        self.error_handler.log_api_error(
            error=error,
            endpoint="/project-times",
            status_code=400,
            request_data=legacy_request_data,
            operation="POST /project-times"
        )
        
        log_contents = self.log_capture_string.getvalue()
        
        # Legacy request data should be available in the structured log data
        # but won't appear in the main log message since it lacks the enhanced structure
        self.assertIn("TIMR_API_ERROR", log_contents)
        self.assertIn("/project-times", log_contents)
        self.assertIn("Validation Error", log_contents)
        
        # Enhanced fields shouldn't be present since this is legacy format
        self.assertNotIn("method=", log_contents)
        self.assertNotIn("url=", log_contents)
        
        # But we can verify the sanitization works on legacy data
        sanitized = self.error_handler._sanitize_request_data(legacy_request_data)
        self.assertEqual(sanitized["task_id"], "task-456")


class TestTimrApiEnhancedErrorLogging(unittest.TestCase):
    """Test that TimrApi properly creates enhanced request data for error logging."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.timr_api = TimrApi()
        self.timr_api.user = {"id": "test_user_123"}
        
        # Set up log capture
        self.log_capture_string = StringIO()
        self.log_handler = logging.StreamHandler(self.log_capture_string)
        formatter = logging.Formatter('%(levelname)s:%(name)s:%(message)s')
        self.log_handler.setFormatter(formatter)
        
        # Attach to timr_api logger
        timr_api_logger = logging.getLogger('timr_api')
        timr_api_logger.addHandler(self.log_handler)
        timr_api_logger.setLevel(logging.DEBUG)
        
        self.original_handlers = timr_api_logger.handlers[:]
    
    def tearDown(self):
        """Clean up test fixtures."""
        timr_api_logger = logging.getLogger('timr_api')
        timr_api_logger.removeHandler(self.log_handler)
        self.log_handler.close()
    
    @patch('timr_api.requests.Session.request')
    def test_http_error_creates_enhanced_request_data(self, mock_request):
        """Test that HTTP errors generate enhanced request data."""
        # Mock a 500 error response
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.headers = {'Content-Type': 'application/json'}
        mock_response.json.return_value = {"error": "Database timeout"}
        mock_response.text = '{"error": "Database timeout"}'
        
        # Create HTTPError and attach response
        http_error = HTTPError(response=mock_response)
        mock_request.side_effect = http_error
        
        # Make a request that will fail
        with self.assertRaises(TimrApiError):
            self.timr_api._request(
                method="POST",
                endpoint="/project-times",
                data={"task_id": "task-789", "start": "2025-06-17T09:00:00+00:00"},
                params={"validate": True}
            )
        
        log_contents = self.log_capture_string.getvalue()
        
        # Verify enhanced request data is logged
        self.assertIn("Request Details:", log_contents)
        self.assertIn("method=POST", log_contents)
        self.assertIn("url=https://api.timr.com/v0.2/project-times", log_contents)
        self.assertIn('"validate": true', log_contents)  # JSON format for params
        self.assertIn('"task_id": "task-789"', log_contents)  # JSON format for payload
        
        # Verify response details are logged
        self.assertIn("Response Details:", log_contents)
        self.assertIn('"error": "Database timeout"', log_contents)
    
    @patch('timr_api.requests.Session.request')
    def test_connection_error_creates_enhanced_request_data(self, mock_request):
        """Test that connection errors generate enhanced request data."""
        # Mock a connection error
        mock_request.side_effect = ConnectionError("Name resolution failed")
        
        # Make a request that will fail
        with self.assertRaises(TimrApiError):
            self.timr_api._request(
                method="GET",
                endpoint="/tasks",
                params={"active": True, "search": "test task"}
            )
        
        log_contents = self.log_capture_string.getvalue()
        
        # Verify enhanced request data is logged even for network errors
        self.assertIn("method=GET", log_contents)
        self.assertIn("url=https://api.timr.com/v0.2/tasks", log_contents)
        self.assertIn('"active": true', log_contents)
        self.assertIn('"search": "test task"', log_contents)
    
    @patch('timr_api.requests.Session.request')
    def test_timeout_error_creates_enhanced_request_data(self, mock_request):
        """Test that timeout errors generate enhanced request data."""
        # Mock a timeout error
        mock_request.side_effect = Timeout("Request timeout after 30 seconds")
        
        # Make a request that will timeout
        with self.assertRaises(TimrApiError):
            self.timr_api._request(
                method="PATCH",
                endpoint="/working-times/wt-123",
                data={"end": "2025-06-17T17:00:00+00:00", "password": "secret"},
                params=None
            )
        
        log_contents = self.log_capture_string.getvalue()
        
        # Verify enhanced request data is logged for timeouts
        self.assertIn("method=PATCH", log_contents)
        self.assertIn("url=https://api.timr.com/v0.2/working-times/wt-123", log_contents)
        self.assertIn('"end": "2025-06-17T17:00:00+00:00"', log_contents)
        
        # Verify sensitive data is masked
        self.assertIn('"password": "***REDACTED***"', log_contents)
        self.assertNotIn("secret", log_contents)


if __name__ == '__main__':
    unittest.main()
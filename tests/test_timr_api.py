import unittest
import datetime
import pytz
from timr_api import TimrApi, TimrApiError


class TestTimrApi(unittest.TestCase):
    """Tests for the TimrApi class"""

    def setUp(self):
        """Set up test fixtures"""
        self.api = TimrApi(company_id="test_company")
        # Mock token for testing
        self.api.token = "test_token"
        self.api.user = {"id": "test_user"}

    def test_format_datetime_iso8601(self):
        """Test date formatting for API communication"""
        # Test with a datetime object
        dt = datetime.datetime(2025, 5, 1, 9, 0, 0, tzinfo=pytz.UTC)
        formatted = self.api._format_datetime_iso8601(dt)
        self.assertEqual(formatted, "2025-05-01T09:00:00+00:00")

        # Test with a string already in ISO format with Z
        dt_str = "2025-05-01T09:00:00Z"
        formatted = self.api._format_datetime_iso8601(dt_str)
        self.assertEqual(formatted, "2025-05-01T09:00:00+00:00")

        # Test with a string already in ISO format with timezone
        dt_str = "2025-05-01T09:00:00+00:00"
        formatted = self.api._format_datetime_iso8601(dt_str)
        self.assertEqual(formatted, "2025-05-01T09:00:00+00:00")

        # Test with a date-only string
        dt_str = "2025-05-01"
        formatted = self.api._format_datetime_iso8601(dt_str)
        self.assertEqual(formatted, "2025-05-01T00:00:00+00:00")

        # Test with a date object
        dt = datetime.date(2025, 5, 1)
        formatted = self.api._format_datetime_iso8601(dt)
        self.assertEqual(formatted, "2025-05-01T00:00:00+00:00")

    def test_format_date_for_query(self):
        """Test date formatting for query parameters"""
        # Test with a datetime object
        dt = datetime.datetime(2025, 5, 1, 9, 0, 0)
        formatted = self.api._format_date_for_query(dt)
        self.assertEqual(formatted, "2025-05-01")

        # Test with a date object
        dt = datetime.date(2025, 5, 1)
        formatted = self.api._format_date_for_query(dt)
        self.assertEqual(formatted, "2025-05-01")

        # Test with an ISO string
        dt_str = "2025-05-01T09:00:00Z"
        formatted = self.api._format_date_for_query(dt_str)
        self.assertEqual(formatted, "2025-05-01")

        # Test with a date-only string
        dt_str = "2025-05-01"
        formatted = self.api._format_date_for_query(dt_str)
        self.assertEqual(formatted, "2025-05-01")


class TestTimrApiError(unittest.TestCase):
    """Tests for the TimrApiError exception class"""
    
    def test_timr_api_error_with_status(self):
        """Test TimrApiError with status code"""
        error = TimrApiError("Test error", 404)
        
        self.assertEqual(str(error), "Test error")
        self.assertEqual(error.status_code, 404)

    def test_timr_api_error_without_status(self):
        """Test TimrApiError without status code"""
        error = TimrApiError("Test error")
        
        self.assertEqual(str(error), "Test error")
        self.assertIsNone(error.status_code)


if __name__ == '__main__':
    unittest.main()

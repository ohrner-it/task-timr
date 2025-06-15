import unittest
import datetime
import pytz
from unittest.mock import patch
from timr_api import TimrApi


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

    def test_get_project_times_in_work_time_without_end(self):
        """_get_project_times_in_work_time supports running sessions"""
        working_time = {
            "start": "2025-06-14T10:00:00+00:00",
            "end": None,
            "duration": {"minutes": 15},
        }

        sample_pt = {"id": "pt1", "start": "2025-06-14T10:05:00+00:00", "end": "2025-06-14T10:10:00+00:00"}

        with patch.object(self.api, "get_project_times", return_value=[sample_pt]) as mock_get:
            result = self.api._get_project_times_in_work_time(working_time)

        mock_get.assert_called_once()
        self.assertEqual(result, [sample_pt])


if __name__ == '__main__':
    unittest.main()

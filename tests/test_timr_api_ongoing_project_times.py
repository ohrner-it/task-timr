"""
Test module for project time retrieval with ongoing working times.
Tests the fix for _get_project_times_in_work_time method.
"""

import unittest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta
import pytz
import sys
import os

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from timr_api import TimrApi, _calculate_ongoing_working_time_end_for_api


class TestOngoingProjectTimeRetrieval(unittest.TestCase):
    """Test project time retrieval for ongoing working times"""

    def setUp(self):
        """Set up test fixtures"""
        self.api = TimrApi()
        self.api.user = {"id": "test-user-id"}
        
        # Standard ongoing working time
        self.ongoing_working_time = {
            "id": "ongoing-wt-id",
            "start": "2025-06-15T09:00:00+00:00",
            "end": None,  # Ongoing working time
            "duration": {
                "type": "ongoing",
                "minutes": 120,
                "minutes_rounded": 120
            },
            "break_time_total_minutes": 15
        }
        
        # Mock project times that should be found
        self.mock_project_times = [
            {
                "id": "pt1",
                "start": "2025-06-15T09:30:00+00:00",
                "end": "2025-06-15T10:00:00+00:00",
                "task": {"id": "task1", "name": "Task 1"}
            },
            {
                "id": "pt2", 
                "start": "2025-06-15T10:00:00+00:00",
                "end": "2025-06-15T10:30:00+00:00",
                "task": {"id": "task2", "name": "Task 2"}
            },
            {
                "id": "pt3",
                "start": "2025-06-15T12:00:00+00:00",  # Outside working time
                "end": "2025-06-15T12:30:00+00:00",
                "task": {"id": "task3", "name": "Task 3"}
            }
        ]

    def test_calculate_ongoing_working_time_end_for_api_with_duration(self):
        """Test utility function calculates end time from duration"""
        work_start = datetime(2025, 6, 15, 9, 0, 0, tzinfo=pytz.UTC)
        
        result = _calculate_ongoing_working_time_end_for_api(self.ongoing_working_time, work_start)
        
        expected_end = work_start + timedelta(minutes=120)
        self.assertEqual(result, expected_end)

    def test_calculate_ongoing_working_time_end_for_api_without_duration(self):
        """Test utility function fallback to current time"""
        ongoing_no_duration = {
            "id": "ongoing-wt-id",
            "start": "2025-06-15T09:00:00+00:00",
            "end": None,
            # No duration field
        }
        work_start = datetime(2025, 6, 15, 9, 0, 0, tzinfo=pytz.UTC)
        
        with patch('datetime.datetime') as mock_datetime:
            mock_now = datetime(2025, 6, 15, 10, 30, 0, tzinfo=pytz.UTC)
            mock_datetime.now.return_value = mock_now
            mock_datetime.fromisoformat = datetime.fromisoformat
            
            result = _calculate_ongoing_working_time_end_for_api(ongoing_no_duration, work_start)
            
            self.assertEqual(result, mock_now)

    @patch.object(TimrApi, 'get_project_times')
    def test_get_project_times_in_work_time_ongoing_working_time(self, mock_get_project_times):
        """Test that ongoing working times can retrieve their project times"""
        # Mock the API call to return project times
        mock_get_project_times.return_value = self.mock_project_times
        
        result = self.api._get_project_times_in_work_time(self.ongoing_working_time)
        
        # Should return project times that fall within the calculated working time
        # Working time: 09:00 + 120 minutes = 11:00
        # pt1 (09:30-10:00) and pt2 (10:00-10:30) should be included
        # pt3 (12:00-12:30) should be excluded as it's outside the calculated end time
        
        self.assertEqual(len(result), 2)
        project_time_ids = [pt["id"] for pt in result]
        self.assertIn("pt1", project_time_ids)
        self.assertIn("pt2", project_time_ids)
        self.assertNotIn("pt3", project_time_ids)

    @patch.object(TimrApi, 'get_project_times')
    def test_get_project_times_in_work_time_ongoing_no_duration_fallback(self, mock_get_project_times):
        """Test ongoing working time without duration uses current time fallback"""
        ongoing_no_duration = {
            "id": "ongoing-wt-id",
            "start": "2025-06-15T09:00:00+00:00",
            "end": None,
            # No duration field - should use current time
        }
        
        mock_get_project_times.return_value = self.mock_project_times
        
        with patch('datetime.datetime') as mock_datetime:
            # Mock current time to be 10:15 (75 minutes after start)
            mock_now = datetime(2025, 6, 15, 10, 15, 0, tzinfo=pytz.UTC)
            mock_datetime.now.return_value = mock_now
            mock_datetime.fromisoformat = datetime.fromisoformat
            
            result = self.api._get_project_times_in_work_time(ongoing_no_duration)
            
            # pt1 (09:30-10:00) and pt2 (10:00-10:30) should be included
            # pt2 starts at 10:00 which is before the current time 10:15, so it overlaps
            # pt3 is way outside the time range
            
            self.assertEqual(len(result), 2)
            project_time_ids = [pt["id"] for pt in result]
            self.assertIn("pt1", project_time_ids)
            self.assertIn("pt2", project_time_ids)

    @patch.object(TimrApi, 'get_project_times')
    def test_get_project_times_in_work_time_completed_working_time(self, mock_get_project_times):
        """Test that completed working times still work correctly"""
        completed_working_time = {
            "id": "completed-wt-id",
            "start": "2025-06-15T09:00:00+00:00",
            "end": "2025-06-15T11:00:00+00:00",  # 2 hour working time
            "break_time_total_minutes": 15
        }
        
        mock_get_project_times.return_value = self.mock_project_times
        
        result = self.api._get_project_times_in_work_time(completed_working_time)
        
        # Should return pt1 and pt2 (both within 09:00-11:00)
        # pt3 is outside (starts at 12:00)
        
        self.assertEqual(len(result), 2)
        project_time_ids = [pt["id"] for pt in result]
        self.assertIn("pt1", project_time_ids)
        self.assertIn("pt2", project_time_ids)
        self.assertNotIn("pt3", project_time_ids)

    @patch.object(TimrApi, 'get_project_times')
    def test_get_project_times_in_work_time_error_handling(self, mock_get_project_times):
        """Test error handling for malformed project times"""
        # Include malformed project times
        malformed_project_times = [
            {
                "id": "pt1",
                "start": "2025-06-15T09:30:00+00:00",
                "end": "2025-06-15T10:00:00+00:00",
                "task": {"id": "task1", "name": "Task 1"}
            },
            {
                "id": "pt_malformed",
                # Missing start time
                "end": "2025-06-15T10:30:00+00:00",
                "task": {"id": "task2", "name": "Task 2"}
            },
            {
                "id": "pt_malformed2",
                "start": "invalid-date",  # Invalid date format
                "end": "2025-06-15T10:30:00+00:00",
                "task": {"id": "task3", "name": "Task 3"}
            }
        ]
        
        mock_get_project_times.return_value = malformed_project_times
        
        result = self.api._get_project_times_in_work_time(self.ongoing_working_time)
        
        # Should only return the valid project time, skip malformed ones
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["id"], "pt1")

    def test_get_project_times_in_work_time_invalid_working_time(self):
        """Test error handling for invalid working time"""
        invalid_working_time = {
            "id": "invalid-wt",
            # Missing start time
            "end": None
        }
        
        with patch.object(self.api, 'get_project_times') as mock_get_project_times:
            mock_get_project_times.return_value = []
            
            result = self.api._get_project_times_in_work_time(invalid_working_time)
            
            # Should return empty list due to error handling
            self.assertEqual(result, [])


if __name__ == "__main__":
    unittest.main()
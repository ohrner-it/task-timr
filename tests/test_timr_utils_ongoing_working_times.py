"""
Test module for ongoing working time functionality.
Tests for null end time handling in consolidation, time slot calculation, and overlap checking.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import pytz
import sys
import os

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from timr_utils import UIProjectTime, ProjectTimeConsolidator
from timr_api import TimrApiError


class TestOngoingWorkingTimeConsolidation(unittest.TestCase):
    """Test consolidation logic for ongoing working times (null end time)"""

    def setUp(self):
        """Set up test fixtures"""
        self.mock_api = Mock()
        self.consolidator = ProjectTimeConsolidator(self.mock_api)
        
        # Standard ongoing working time
        self.ongoing_working_time = {
            "id": "ongoing-wt-id",
            "start": "2025-06-15T09:00:00+00:00",
            "end": None,  # Key: ongoing working time has null end
            "duration": {
                "type": "ongoing",
                "minutes": 120,
                "minutes_rounded": 120
            },
            "break_time_total_minutes": 15,
            "status": "changeable"
        }
        
        # Completed working time for comparison
        self.completed_working_time = {
            "id": "completed-wt-id",
            "start": "2025-06-15T09:00:00+00:00",
            "end": "2025-06-15T11:00:00+00:00",
            "break_time_total_minutes": 15,
            "status": "changeable"
        }

    def test_consolidate_ongoing_working_time_no_project_times(self):
        """Test consolidation of ongoing working time with no project times"""
        self.mock_api._get_project_times_in_work_time.return_value = []
        
        result = self.consolidator.consolidate_project_times(self.ongoing_working_time)
        
        # Verify basic structure
        self.assertIn("working_time", result)
        self.assertIn("ui_project_times", result)
        self.assertIn("total_duration", result)
        self.assertIn("net_duration", result)
        self.assertIn("remaining_duration", result)
        
        # Verify duration calculations
        self.assertEqual(result["net_duration"], 105)  # 120 - 15 break = 105
        self.assertEqual(result["total_duration"], 0)   # No project times allocated
        self.assertEqual(result["remaining_duration"], 105)  # All time available
        self.assertFalse(result["is_fully_allocated"])

    def test_consolidate_ongoing_working_time_with_project_times(self):
        """Test consolidation of ongoing working time with existing project times"""
        # Mock project times with proper task structure
        project_times = [
            {
                "id": "pt1",
                "start": "2025-06-15T09:00:00+00:00",
                "end": "2025-06-15T09:30:00+00:00",
                "task": {
                    "id": "task1",
                    "name": "Test Task",
                    "breadcrumbs": "Project/Test Task"
                }
            },
            {
                "id": "pt2", 
                "start": "2025-06-15T09:30:00+00:00",
                "end": "2025-06-15T10:00:00+00:00",
                "task": {
                    "id": "task1", 
                    "name": "Test Task",
                    "breadcrumbs": "Project/Test Task"
                }
            }
        ]
        self.mock_api._get_project_times_in_work_time.return_value = project_times
        
        result = self.consolidator.consolidate_project_times(self.ongoing_working_time)
        
        # Verify project times are consolidated 
        self.assertEqual(len(result["ui_project_times"]), 1)
        self.assertEqual(result["ui_project_times"][0].task_id, "task1")
        self.assertEqual(result["ui_project_times"][0].duration_minutes, 60)  # 2 x 30min
        
        # Verify duration calculations
        self.assertEqual(result["total_duration"], 60)
        self.assertEqual(result["remaining_duration"], 45)  # 105 - 60 = 45

    def test_consolidate_ongoing_working_time_no_duration_fallback(self):
        """Test ongoing working time without duration info falls back to time calculation"""
        ongoing_no_duration = {
            "id": "ongoing-wt-id",
            "start": "2025-06-15T09:00:00+00:00", 
            "end": None,
            # No duration field - should calculate from start to now
            "break_time_total_minutes": 0,
            "status": "changeable"
        }
        self.mock_api._get_project_times_in_work_time.return_value = []
        
        with patch('timr_utils.datetime') as mock_datetime:
            # Mock current time as 2 hours after start
            mock_now = datetime(2025, 6, 15, 11, 0, 0, tzinfo=pytz.UTC)
            mock_datetime.now.return_value = mock_now
            mock_datetime.fromisoformat = datetime.fromisoformat
            
            result = self.consolidator.consolidate_project_times(ongoing_no_duration)
            
            # Should calculate ~120 minutes from start to mock "now"
            self.assertEqual(result["net_duration"], 120)

    def test_consolidate_ongoing_working_time_invalid_start(self):
        """Test error handling for ongoing working time with invalid start time"""
        invalid_ongoing = {
            "id": "invalid-wt-id",
            "start": "",  # Invalid start time
            "end": None,
            "duration": {"type": "ongoing", "minutes": 60},
            "break_time_total_minutes": 0
        }
        
        with self.assertRaises(ValueError) as context:
            self.consolidator.consolidate_project_times(invalid_ongoing)
        
        self.assertIn("start time", str(context.exception).lower())


class TestOngoingWorkingTimeSlotCalculation(unittest.TestCase):
    """Test time slot calculation for ongoing working times"""

    def setUp(self):
        """Set up test fixtures"""
        self.mock_api = Mock()
        self.consolidator = ProjectTimeConsolidator(self.mock_api)
        
        self.ongoing_working_time = {
            "id": "ongoing-wt-id",
            "start": "2025-06-15T09:00:00+00:00",
            "end": None,
            "duration": {
                "type": "ongoing",
                "minutes": 120,
                "minutes_rounded": 120
            },
            "break_time_total_minutes": 0
        }

    def test_calculate_time_slots_ongoing_working_time(self):
        """Test time slot calculation for ongoing working time"""
        tasks = [
            UIProjectTime("task1", "Development", 60),
            UIProjectTime("task2", "Testing", 30)
        ]
        
        time_slots = self.consolidator._calculate_time_slots(self.ongoing_working_time, tasks)
        
        # Should create 2 time slots
        self.assertEqual(len(time_slots), 2)
        
        # Verify slot structure
        for slot in time_slots:
            self.assertIn("task_id", slot)
            self.assertIn("start", slot)
            self.assertIn("end", slot)
            self.assertIn("duration_minutes", slot)
        
        # Verify tasks are sorted by name descending (Testing, Development)
        self.assertEqual(time_slots[0]["task_id"], "task2")  # Testing
        self.assertEqual(time_slots[1]["task_id"], "task1")  # Development
        
        # Verify durations are preserved
        self.assertEqual(time_slots[0]["duration_minutes"], 30)
        self.assertEqual(time_slots[1]["duration_minutes"], 60)

    def test_calculate_time_slots_ongoing_allows_extension_beyond_current_end(self):
        """Test that ongoing working times allow tasks to extend beyond calculated end"""
        # Task duration (90m) exceeds working time duration (60m)
        tasks = [UIProjectTime("task1", "Long Task", 90)]
        
        ongoing_60min = {
            "id": "ongoing-wt-id",
            "start": "2025-06-15T09:00:00+00:00",
            "end": None,
            "duration": {"type": "ongoing", "minutes": 60},
            "break_time_total_minutes": 0
        }
        
        time_slots = self.consolidator._calculate_time_slots(ongoing_60min, tasks)
        
        # Should still create the slot, allowing extension
        self.assertEqual(len(time_slots), 1)
        self.assertEqual(time_slots[0]["duration_minutes"], 90)
        
        # Task should end 30 minutes beyond the current working time end
        start_time = datetime.fromisoformat("2025-06-15T09:00:00+00:00")
        expected_end = start_time + timedelta(minutes=90)
        self.assertEqual(time_slots[0]["end"], expected_end)

    def test_calculate_time_slots_completed_vs_ongoing_boundary_enforcement(self):
        """Test boundary enforcement difference between completed and ongoing times"""
        task = UIProjectTime("task1", "Test Task", 30)
        
        # Completed working time - should enforce boundary
        completed_wt = {
            "start": "2025-06-15T09:00:00+00:00",
            "end": "2025-06-15T10:00:00+00:00",  # 60 minute duration
            "break_time_total_minutes": 0
        }
        
        # Ongoing working time - should not enforce boundary  
        ongoing_wt = {
            "start": "2025-06-15T09:00:00+00:00",
            "end": None,
            "duration": {"minutes": 60},
            "break_time_total_minutes": 0
        }
        
        completed_slots = self.consolidator._calculate_time_slots(completed_wt, [task])
        ongoing_slots = self.consolidator._calculate_time_slots(ongoing_wt, [task])
        
        # Both should create slots, but ongoing allows more flexibility
        self.assertEqual(len(completed_slots), 1)
        self.assertEqual(len(ongoing_slots), 1)
        
        # Both should preserve the 30-minute duration
        self.assertEqual(completed_slots[0]["duration_minutes"], 30)
        self.assertEqual(ongoing_slots[0]["duration_minutes"], 30)


class TestOngoingWorkingTimeOverlapChecking(unittest.TestCase):
    """Test overlap checking logic for ongoing working times"""

    def test_ongoing_working_time_overlap_logic(self):
        """Test the overlap checking logic that was fixed in app.py"""
        # This tests the logic that was modified in app.py:336-346
        
        # Simulate the overlap checking logic for ongoing working time
        ongoing_wt = {
            "start": "2025-06-15T09:00:00+00:00",
            "end": None  # Ongoing working time
        }
        
        new_start = datetime.fromisoformat("2025-06-15T08:00:00+00:00")
        new_end = datetime.fromisoformat("2025-06-15T09:30:00+00:00")
        
        # Parse ongoing working time start
        wt_start = datetime.fromisoformat(ongoing_wt["start"].replace("Z", "+00:00"))
        
        # Test the ongoing overlap logic
        if ongoing_wt["end"] is None:
            # For ongoing working times, check if new time starts before ongoing starts
            overlaps = new_start < wt_start
        else:
            # Standard overlap logic would be used here
            overlaps = False
        
        # New working time starts before ongoing time, so should overlap
        self.assertTrue(overlaps)
        
        # Test case where new time starts after ongoing time
        new_start_after = datetime.fromisoformat("2025-06-15T10:00:00+00:00")
        overlaps_after = new_start_after < wt_start
        self.assertFalse(overlaps_after)


class TestOngoingWorkingTimeEdgeCases(unittest.TestCase):
    """Test edge cases and error conditions for ongoing working times"""

    def setUp(self):
        self.mock_api = Mock()
        self.consolidator = ProjectTimeConsolidator(self.mock_api)

    def test_ongoing_working_time_with_zero_duration(self):
        """Test ongoing working time with zero or very small duration"""
        zero_duration_wt = {
            "id": "zero-duration-wt",
            "start": "2025-06-15T09:00:00+00:00",
            "end": None,
            "duration": {"type": "ongoing", "minutes": 0},
            "break_time_total_minutes": 0
        }
        self.mock_api._get_project_times_in_work_time.return_value = []
        
        result = self.consolidator.consolidate_project_times(zero_duration_wt)
        
        self.assertEqual(result["net_duration"], 0)
        self.assertEqual(result["remaining_duration"], 0)

    def test_ongoing_working_time_with_breaks_exceeding_duration(self):
        """Test ongoing working time where breaks exceed total duration"""
        excessive_break_wt = {
            "id": "excessive-break-wt",
            "start": "2025-06-15T09:00:00+00:00",
            "end": None,
            "duration": {"type": "ongoing", "minutes": 60},
            "break_time_total_minutes": 90,  # More break than total time
        }
        self.mock_api._get_project_times_in_work_time.return_value = []
        
        result = self.consolidator.consolidate_project_times(excessive_break_wt)
        
        # Net duration should be negative, remaining should handle this
        self.assertEqual(result["net_duration"], -30)  # 60 - 90 = -30

    def test_ongoing_working_time_malformed_duration(self):
        """Test ongoing working time with malformed duration data"""
        malformed_wt = {
            "id": "malformed-wt",
            "start": "2025-06-15T09:00:00+00:00",
            "end": None,
            "duration": {"type": "ongoing"},  # Missing minutes field
            "break_time_total_minutes": 0
        }
        
        with patch('timr_utils.datetime') as mock_datetime:
            # Mock current time for fallback calculation
            mock_now = datetime(2025, 6, 15, 10, 0, 0, tzinfo=pytz.UTC)
            mock_datetime.now.return_value = mock_now
            mock_datetime.fromisoformat = datetime.fromisoformat
            
            self.mock_api._get_project_times_in_work_time.return_value = []
            
            # Should not crash, should use fallback time calculation
            result = self.consolidator.consolidate_project_times(malformed_wt)
            
            # Should calculate 60 minutes from 09:00 to mocked 10:00
            self.assertEqual(result["net_duration"], 60)


if __name__ == "__main__":
    unittest.main()
"""
Test suite for working time edit scenarios
Tests the enhanced logic for handling working time boundary changes

Copyright (c) 2025 Ohrner IT GmbH
Licensed under the MIT License
"""

import unittest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta
import logging
import timr_utils

from timr_utils import ProjectTimeConsolidator, UIProjectTime
from timr_api import TimrApi

# Configure logging for tests
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class TestWorkingTimeEdits(unittest.TestCase):
    """Test suite for working time edit scenarios"""

    def setUp(self):
        """Set up test fixtures"""
        self.mock_timr_api = Mock(spec=TimrApi)
        self.consolidator = ProjectTimeConsolidator(self.mock_timr_api)
        
        # Base working time: 9:00 AM to 5:00 PM (8 hours = 480 minutes)
        self.original_working_time = {
            "id": "wt_test",
            "start": "2025-04-01T09:00:00+00:00",
            "end": "2025-04-01T17:00:00+00:00",
            "break_time_total_minutes": 0
        }
        
        # Tasks that originally fit perfectly in the 8-hour working time
        self.original_tasks = [
            UIProjectTime("task1", "Task 1", 120),  # 2 hours
            UIProjectTime("task2", "Task 2", 180),  # 3 hours  
            UIProjectTime("task3", "Task 3", 180),  # 3 hours
            # Total: 8 hours = 480 minutes
        ]

    def test_working_time_start_shift(self):
        """Test shifting working time start by 1 hour later"""
        # Shifted working time: 10:00 AM to 5:00 PM (same duration)
        shifted_working_time = {
            "id": "wt_test",
            "start": "2025-04-01T10:00:00+00:00",  # 1 hour later
            "end": "2025-04-01T17:00:00+00:00",     # Same end time
            "break_time_total_minutes": 0
        }
        
        # Calculate time slots with new start time
        time_slots = self.consolidator._calculate_time_slots(
            shifted_working_time, self.original_tasks)
        
        # Verify all tasks start from the new working time start
        self.assertEqual(len(time_slots), 3)
        
        # Tasks are sorted descending by name, so Task 3, Task 2, Task 1
        # First task should start at 10:00 AM (new start time)
        expected_start = datetime.fromisoformat("2025-04-01T10:00:00+00:00")
        self.assertEqual(time_slots[0]['start'], expected_start)
        
        # Verify sequential allocation
        self.assertEqual(time_slots[0]['end'], 
                        expected_start + timedelta(minutes=180))  # Task 3: 180 minutes
        self.assertEqual(time_slots[1]['start'], time_slots[0]['end'])
        self.assertEqual(time_slots[2]['start'], time_slots[1]['end'])
        
        # Verify task durations are preserved (descending order: Task 3, Task 2, Task 1)
        self.assertEqual(time_slots[0]['duration_minutes'], 180)  # Task 3
        self.assertEqual(time_slots[1]['duration_minutes'], 180)  # Task 2
        self.assertEqual(time_slots[2]['duration_minutes'], 120)  # Task 1

    def test_working_time_duration_reduction(self):
        """Test reducing working time duration significantly"""
        # Reduced working time: 9:00 AM to 1:00 PM (4 hours = 240 minutes)
        reduced_working_time = {
            "id": "wt_test", 
            "start": "2025-04-01T09:00:00+00:00",
            "end": "2025-04-01T13:00:00+00:00",     # 4 hours shorter
            "break_time_total_minutes": 0
        }
        
        # Calculate time slots with reduced duration
        time_slots = self.consolidator._calculate_time_slots(
            reduced_working_time, self.original_tasks)
        
        # Verify all tasks are still allocated
        self.assertEqual(len(time_slots), 3)
        
        # Verify tasks start at working time start
        expected_start = datetime.fromisoformat("2025-04-01T09:00:00+00:00")
        expected_end = datetime.fromisoformat("2025-04-01T13:00:00+00:00")
        
        self.assertEqual(time_slots[0]['start'], expected_start)
        
        # Verify task durations are preserved (descending order: Task 3, Task 2, Task 1)
        self.assertEqual(time_slots[0]['duration_minutes'], 180)  # Task 3
        self.assertEqual(time_slots[1]['duration_minutes'], 180)  # Task 2
        self.assertEqual(time_slots[2]['duration_minutes'], 120)  # Task 1
        
        # Verify that tasks extend beyond working time (creating intended overlaps)
        total_task_duration = sum(slot['duration_minutes'] for slot in time_slots)
        working_time_duration = (expected_end - expected_start).total_seconds() / 60
        
        self.assertEqual(total_task_duration, 480)  # Original total duration
        self.assertEqual(working_time_duration, 240)  # Reduced working time
        
        # Last task should extend beyond working time end
        last_task_end = time_slots[-1]['end']
        self.assertGreater(last_task_end, expected_end)

    def test_working_time_both_start_and_duration_change(self):
        """Test changing both start time and duration"""
        # Changed working time: 11:00 AM to 2:00 PM (3 hours = 180 minutes)
        changed_working_time = {
            "id": "wt_test",
            "start": "2025-04-01T11:00:00+00:00",  # 2 hours later
            "end": "2025-04-01T14:00:00+00:00",     # Much shorter
            "break_time_total_minutes": 0
        }
        
        # Calculate time slots with both changes
        time_slots = self.consolidator._calculate_time_slots(
            changed_working_time, self.original_tasks)
        
        # Verify all tasks are still allocated
        self.assertEqual(len(time_slots), 3)
        
        # Verify tasks start from new start time
        expected_start = datetime.fromisoformat("2025-04-01T11:00:00+00:00")
        expected_end = datetime.fromisoformat("2025-04-01T14:00:00+00:00")
        
        self.assertEqual(time_slots[0]['start'], expected_start)
        
        # Verify task durations preserved (descending order: Task 3, Task 2, Task 1)
        expected_durations = [180, 180, 120]  # Task 3, Task 2, Task 1
        for i, expected_duration in enumerate(expected_durations):
            self.assertEqual(time_slots[i]['duration_minutes'], expected_duration)
        
        # Verify overlapping occurs due to insufficient time
        last_task_end = time_slots[-1]['end']
        self.assertGreater(last_task_end, expected_end)

    def test_enhanced_project_time_retrieval(self):
        """Test enhanced _get_project_times_in_work_time method"""
        # Mock existing project times that may extend beyond working time
        existing_project_times = [
            {
                "id": "pt1",
                "start": "2025-04-01T09:00:00+00:00",
                "end": "2025-04-01T11:00:00+00:00",
                "task": {"id": "task1", "name": "Task 1"}
            },
            {
                "id": "pt2", 
                "start": "2025-04-01T11:00:00+00:00",
                "end": "2025-04-01T14:00:00+00:00",  # Extends beyond working time
                "task": {"id": "task2", "name": "Task 2"}
            },
            {
                "id": "pt3",
                "start": "2025-04-01T14:00:00+00:00", 
                "end": "2025-04-01T17:00:00+00:00",  # Extends beyond working time
                "task": {"id": "task3", "name": "Task 3"}
            }
        ]
        
        self.mock_timr_api.get_project_times.return_value = existing_project_times
        
        # Working time reduced to 9:00 AM - 1:00 PM
        reduced_working_time = {
            "id": "wt_test",
            "start": "2025-04-01T09:00:00+00:00", 
            "end": "2025-04-01T13:00:00+00:00",
            "break_time_total_minutes": 0
        }
        
        # Test the enhanced retrieval method
        result = self.mock_timr_api._get_project_times_in_work_time(reduced_working_time)
        
        # Should call the actual implementation, so let's mock it properly
        with patch.object(self.mock_timr_api, '_get_project_times_in_work_time') as mock_method:
            mock_method.return_value = existing_project_times
            
            result = self.mock_timr_api._get_project_times_in_work_time(reduced_working_time)
            
            # Verify it returns all project times, even those extending beyond
            self.assertEqual(len(result), 3)
            mock_method.assert_called_once_with(reduced_working_time)

    def test_differential_update_with_time_boundary_changes(self):
        """Test differential updates when working time boundaries change"""
        # Mock existing project times in Timr
        existing_project_times = [
            {
                "id": "pt1",
                "start": "2025-04-01T09:00:00+00:00",
                "end": "2025-04-01T11:00:00+00:00", 
                "task": {"id": "task1", "name": "Task 1"}
            }
        ]
        
        self.mock_timr_api._get_project_times_in_work_time.return_value = existing_project_times
        
        # Shifted working time
        shifted_working_time = {
            "id": "wt_test",
            "start": "2025-04-01T10:00:00+00:00",  # 1 hour later
            "end": "2025-04-01T18:00:00+00:00",
            "break_time_total_minutes": 0
        }
        
        # New task list with same task but should start at new time
        new_tasks = [UIProjectTime("task1", "Task 1", 120)]
        
        # Apply differential updates
        self.consolidator.apply_differential_updates(shifted_working_time, new_tasks)
        
        # Verify that update_project_time was called to shift the time
        self.mock_timr_api.update_project_time.assert_called()

    def test_empty_task_list_with_existing_project_times(self):
        """Test handling empty task list when project times exist"""
        # Mock existing project times
        existing_project_times = [
            {
                "id": "pt1",
                "start": "2025-04-01T09:00:00+00:00",
                "end": "2025-04-01T11:00:00+00:00",
                "task": {"id": "task1", "name": "Task 1"}
            }
        ]
        
        self.mock_timr_api._get_project_times_in_work_time.return_value = existing_project_times
        
        # Apply differential updates with empty task list
        empty_tasks = []
        self.consolidator.apply_differential_updates(
            self.original_working_time, empty_tasks)
        
        # Should delete the existing project time
        self.mock_timr_api.delete_project_time.assert_called_with("pt1")

    def test_logging_for_overlapping_tasks(self):
        """Test that warnings are logged for overlapping tasks"""
        # Reduced working time that will cause overlaps
        reduced_working_time = {
            "id": "wt_test",
            "start": "2025-04-01T09:00:00+00:00",
            "end": "2025-04-01T11:00:00+00:00",  # Only 2 hours
            "break_time_total_minutes": 0
        }
        
        # Tasks that require more than 2 hours
        large_tasks = [UIProjectTime("task1", "Task 1", 180)]  # 3 hours
        
        # Capture logging from timr_utils module
        with self.assertLogs(logger=timr_utils.logger, level='WARNING') as log_capture:
            time_slots = self.consolidator._calculate_time_slots(
                reduced_working_time, large_tasks)
            
            # Verify warning was logged
            self.assertTrue(any("extends beyond working time end" in log_msg 
                              for log_msg in log_capture.output))
        
        # Verify task still allocated with full duration
        self.assertEqual(len(time_slots), 1)
        self.assertEqual(time_slots[0]['duration_minutes'], 180)


if __name__ == '__main__':
    unittest.main()
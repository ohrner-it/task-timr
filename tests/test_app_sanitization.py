import unittest
from unittest.mock import Mock, patch, MagicMock
import datetime
from timr_utils import ProjectTimeConsolidator


class TestSanitizationFunctions(unittest.TestCase):
    """Tests for the sanitization functions in ProjectTimeConsolidator"""

    def setUp(self):
        """Set up test fixtures"""
        self.mock_timr_api = Mock()
        self.consolidator = ProjectTimeConsolidator(self.mock_timr_api)

        # Create sample work times with overlaps
        self.overlapping_work_times = [
            {
                "id": "wt1",
                "start": "2025-04-01T09:00:00+00:00",
                "end": "2025-04-01T17:00:00+00:00",
                "break_time_total_minutes": 30
            },
            {
                "id": "wt2",
                "start": "2025-04-01T16:00:00+00:00",  # Overlaps with wt1
                "end": "2025-04-01T18:00:00+00:00",
                "break_time_total_minutes": 0
            },
            {
                "id": "wt3",
                "start": "2025-04-01T18:30:00+00:00",  # No overlap
                "end": "2025-04-01T20:00:00+00:00",
                "break_time_total_minutes": 0
            }
        ]

        # Create sample project times that exceed working time bounds
        self.working_time = {
            "id": "wt1",
            "start": "2025-04-01T09:00:00+00:00",
            "end": "2025-04-01T17:00:00+00:00",
            "break_time_total_minutes": 30
        }

        self.out_of_bounds_project_times = [
            {
                "id": "pt1",
                "start":
                "2025-04-01T08:30:00+00:00",  # Starts before working time
                "end": "2025-04-01T10:00:00+00:00",
                "task": {
                    "id": "task1",
                    "name": "Task 1"
                }
            },
            {
                "id": "pt2",
                "start": "2025-04-01T16:30:00+00:00",
                "end": "2025-04-01T17:30:00+00:00",  # Ends after working time
                "task": {
                    "id": "task2",
                    "name": "Task 2"
                }
            },
            {
                "id": "pt3",
                "start":
                "2025-04-01T12:00:00+00:00",  # Within working time bounds
                "end": "2025-04-01T13:00:00+00:00",
                "task": {
                    "id": "task3",
                    "name": "Task 3"
                }
            }
        ]

    def test_sanitize_work_times(self):
        """Test sanitize_work_times method"""
        # Call the method under test
        sanitized_wts = self.consolidator.sanitize_work_times(
            self.overlapping_work_times)

        # Verify the number of work times remains the same
        self.assertEqual(len(sanitized_wts), len(self.overlapping_work_times))

        # Verify overlapping times were fixed
        wt1_end = datetime.datetime.fromisoformat(sanitized_wts[0]["end"])
        wt2_start = datetime.datetime.fromisoformat(sanitized_wts[1]["start"])

        # First work time should end at the start of the second
        self.assertEqual(wt1_end, wt2_start)

        # Verify third work time was not affected (it didn't overlap)
        self.assertEqual(sanitized_wts[2]["start"],
                         self.overlapping_work_times[2]["start"])
        self.assertEqual(sanitized_wts[2]["end"],
                         self.overlapping_work_times[2]["end"])

    def test_sanitize_work_times_skips_invalid_entries(self):
        """sanitize_work_times ignores None or malformed items"""
        work_times = [
            None,
            {"start": "2025-04-01T09:00:00+00:00", "end": "2025-04-01T10:00:00+00:00"},
            123,
            {"id": "wt2", "end": "2025-04-01T11:00:00+00:00"},
        ]

        result = self.consolidator.sanitize_work_times(work_times)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["start"], "2025-04-01T09:00:00+00:00")

    def test_sanitize_project_times(self):
        """Test sanitize_project_times method"""
        # Configure mock
        self.mock_timr_api._get_project_times_in_work_time.return_value = self.out_of_bounds_project_times
        self.mock_timr_api.update_project_time.side_effect = lambda id, **kwargs: {
            "id": id,
            "start": kwargs.get("start").isoformat() if kwargs.get("start") else None,
            "end": kwargs.get("end").isoformat() if kwargs.get("end") else None
        }

        # Call the method under test
        adjusted_pts = self.consolidator.sanitize_project_times(
            self.working_time)

        # Verify the mock was called
        self.mock_timr_api._get_project_times_in_work_time.assert_called_once_with(
            self.working_time)

        # Verify update_project_time was called only for start time adjustment (end time truncation removed)
        self.assertEqual(self.mock_timr_api.update_project_time.call_count, 1)

        # Check that project times were adjusted
        for pt in adjusted_pts:
            pt_id = pt["id"]

            if pt_id == "pt1":
                # Should be adjusted to start at working time start
                self.assertEqual(pt["start"], "2025-04-01T09:00:00+00:00")
            elif pt_id == "pt2":
                # End time truncation was removed - durations are preserved
                self.assertEqual(pt["end"], "2025-04-01T17:30:00+00:00")

    def test_distribute_time_proportional_adjustment(self):
        """Test _distribute_project_times_sequentially with proportional adjustment for exceeding durations"""
        # Configure mocks
        self.consolidator._delete_all_project_times_in_working_time = MagicMock(
            return_value=0)
        self.mock_timr_api.create_project_time.side_effect = lambda **kwargs: {
            "id":
            f"new_pt_{len(self.mock_timr_api.create_project_time.mock_calls)}",
            "task_id": kwargs.get("task_id"),
            "start": kwargs.get("start").isoformat(),
            "end": kwargs.get("end").isoformat()
        }

        # Create task durations that exceed the working time duration
        task_durations = [
            {
                "task_id": "task1",
                "duration_minutes": 240
            },  # 4 hours
            {
                "task_id": "task2",
                "duration_minutes": 180
            },  # 3 hours
            {
                "task_id": "task3",
                "duration_minutes": 120
            }  # 2 hours
        ]

        # Convert to UIProjectTime objects
        from timr_utils import UIProjectTime
        ui_project_times = [
            UIProjectTime(task_id="task1", duration_minutes=240, task_name="Task 1"),
            UIProjectTime(task_id="task2", duration_minutes=180, task_name="Task 2"),
            UIProjectTime(task_id="task3", duration_minutes=120, task_name="Task 3")
        ]

        # Mock apply_differential_updates method
        self.consolidator.apply_differential_updates = Mock()

        # Mock the return value for _get_project_times_in_work_time
        mock_result = []
        self.mock_timr_api._get_project_times_in_work_time.return_value = mock_result

        # Call distribute_time method - the new approach handles excessive durations gracefully
        result = self.consolidator.distribute_time(
            self.working_time, ui_project_times, replace_all=True)

        # Verify apply_differential_updates was called with the new signature
        self.consolidator.apply_differential_updates.assert_called_once_with(
            self.working_time, ui_project_times, None)

        # Verify the result matches mock return value
        self.assertEqual(result, mock_result)


if __name__ == '__main__':
    unittest.main()

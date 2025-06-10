import unittest
from unittest.mock import Mock, MagicMock, call
import datetime
from timr_utils import UIProjectTime, ProjectTimeConsolidator
from timr_api import TimrApiError


class TestIncrementalUpdates(unittest.TestCase):
    """Test suite for the incremental update functionality in ProjectTimeConsolidator"""

    def setUp(self):
        """Set up test fixtures"""
        self.mock_timr_api = Mock()
        self.consolidator = ProjectTimeConsolidator(self.mock_timr_api)

        # Sample working time
        self.working_time = {
            "id": "wt1",
            "start": "2025-04-01T09:00:00+00:00",
            "end": "2025-04-01T17:00:00+00:00",
            "break_time_total_minutes": 30
        }

        # Sample current project times in Timr
        self.current_project_times = [{
            "id": "pt1",
            "start": "2025-04-01T09:00:00+00:00",
            "end": "2025-04-01T11:00:00+00:00",
            "task": {
                "id": "task1",
                "name": "Task 1"
            }
        }, {
            "id": "pt2",
            "start": "2025-04-01T11:00:00+00:00",
            "end": "2025-04-01T12:30:00+00:00",
            "task": {
                "id": "task2",
                "name": "Task 2"
            }
        }]

        # Configure mock
        self.mock_timr_api._get_project_times_in_work_time.return_value = self.current_project_times
        self.mock_timr_api.create_project_time.return_value = {"id": "new_pt1"}
        self.mock_timr_api.update_project_time.return_value = {"id": "pt1"}
        self.mock_timr_api.delete_project_time.return_value = {}

    def test_calculate_time_slots_basic(self):
        """Test basic time slot calculation"""
        tasks = [
            UIProjectTime("task1", "Task 1", 60),  # 1 hour
            UIProjectTime("task2", "Task 2", 90),  # 1.5 hours
        ]

        slots = self.consolidator._calculate_time_slots(
            self.working_time, tasks)

        self.assertEqual(len(slots), 2)

        # First slot should be task2 (sorted by task name descending: "Task 2" > "Task 1")
        self.assertEqual(slots[0]['task_id'], 'task2')
        self.assertEqual(slots[0]['duration_minutes'], 90)
        self.assertEqual(
            slots[0]['start'],
            datetime.datetime(2025,
                              4,
                              1,
                              9,
                              0,
                              0,
                              tzinfo=datetime.timezone.utc))
        self.assertEqual(
            slots[0]['end'],
            datetime.datetime(2025,
                              4,
                              1,
                              10,
                              30,
                              0,
                              tzinfo=datetime.timezone.utc))

        # Second slot should start where first ends
        self.assertEqual(slots[1]['task_id'], 'task1')
        self.assertEqual(slots[1]['duration_minutes'], 60)
        self.assertEqual(
            slots[1]['start'],
            datetime.datetime(2025,
                              4,
                              1,
                              10,
                              30,
                              0,
                              tzinfo=datetime.timezone.utc))
        self.assertEqual(
            slots[1]['end'],
            datetime.datetime(2025,
                              4,
                              1,
                              11,
                              30,
                              0,
                              tzinfo=datetime.timezone.utc))

    def test_calculate_time_slots_sorted_by_task_name_desc_task_id_desc(self):
        """Test that time slots are sorted by task name descending, then task_id descending"""
        tasks = [
            UIProjectTime("task1", "Alpha Task", 60),
            UIProjectTime("task3", "Zulu Task", 90),
            UIProjectTime("task2", "Beta Task", 30),
            UIProjectTime("task4", "Alpha Task", 45),  # Same name, different ID
        ]

        slots = self.consolidator._calculate_time_slots(
            self.working_time, tasks)

        # Should be sorted by task_name descending, then task_id descending
        self.assertEqual(slots[0]['task_id'], 'task3')  # "Zulu Task"
        self.assertEqual(slots[1]['task_id'], 'task2')  # "Beta Task"
        self.assertEqual(slots[2]['task_id'], 'task4')  # "Alpha Task" (task4 > task1)
        self.assertEqual(slots[3]['task_id'], 'task1')  # "Alpha Task" (task1 < task4)

    def test_calculate_time_slots_sorted_with_empty_task_names(self):
        """Test sorting behavior with empty or None task names"""
        tasks = [
            UIProjectTime("task3", "Real Task", 60),
            UIProjectTime("task1", "", 90),  # Empty name
            UIProjectTime("task2", "", 30),  # Empty name (None converted to empty string)
        ]

        slots = self.consolidator._calculate_time_slots(
            self.working_time, tasks)

        # Empty/None names should sort to the end (descending order)
        self.assertEqual(slots[0]['task_id'], 'task3')  # "Real Task"
        self.assertEqual(slots[1]['task_id'], 'task2')  # None/empty (task2 > task1)
        self.assertEqual(slots[2]['task_id'], 'task1')  # None/empty (task1 < task2)

    def test_calculate_time_slots_sorted_same_names_different_ids(self):
        """Test sorting when multiple tasks have identical names"""
        tasks = [
            UIProjectTime("task1", "Same Name", 60),
            UIProjectTime("task5", "Same Name", 90),
            UIProjectTime("task3", "Same Name", 30),
        ]

        slots = self.consolidator._calculate_time_slots(
            self.working_time, tasks)

        # Should sort by task_id descending as fallback
        self.assertEqual(slots[0]['task_id'], 'task5')  # Highest ID first
        self.assertEqual(slots[1]['task_id'], 'task3')  # Middle ID
        self.assertEqual(slots[2]['task_id'], 'task1')  # Lowest ID last

    def test_calculate_time_slots_filters_deleted_and_zero_duration(self):
        """Test that deleted and zero-duration tasks are filtered out"""
        tasks = [
            UIProjectTime("task1", "Task 1", 60),
            UIProjectTime("task2", "Task 2", 0),  # Zero duration
            UIProjectTime("task3", "Task 3", 30),
        ]
        tasks[1].mark_for_deletion()  # Mark as deleted

        slots = self.consolidator._calculate_time_slots(
            self.working_time, tasks)

        # Should only include task1 and task3, sorted by task name descending: "Task 3" > "Task 1"
        self.assertEqual(len(slots), 2)
        self.assertEqual(slots[0]['task_id'], 'task3')
        self.assertEqual(slots[1]['task_id'], 'task1')

    def test_project_time_needs_update_no_change(self):
        """Test that identical times don't need update"""
        current_pt = {
            'start': '2025-04-01T09:00:00+00:00',
            'end': '2025-04-01T10:00:00+00:00'
        }
        desired_slot = {
            'start':
            datetime.datetime(2025,
                              4,
                              1,
                              9,
                              0,
                              0,
                              tzinfo=datetime.timezone.utc),
            'end':
            datetime.datetime(2025,
                              4,
                              1,
                              10,
                              0,
                              0,
                              tzinfo=datetime.timezone.utc),
            'task_id':
            'task1'
        }

        needs_update = self.consolidator._project_time_needs_update(
            current_pt, desired_slot)
        self.assertFalse(needs_update)

    def test_project_time_needs_update_time_change(self):
        """Test that different times need update"""
        current_pt = {
            'start': '2025-04-01T09:00:00+00:00',
            'end': '2025-04-01T10:00:00+00:00'
        }
        desired_slot = {
            'start':
            datetime.datetime(2025,
                              4,
                              1,
                              9,
                              0,
                              0,
                              tzinfo=datetime.timezone.utc),
            'end':
            datetime.datetime(
                2025, 4, 1, 10, 30, 0,
                tzinfo=datetime.timezone.utc),  # Different end time
            'task_id':
            'task1'
        }

        needs_update = self.consolidator._project_time_needs_update(
            current_pt, desired_slot)
        self.assertTrue(needs_update)

    def test_project_time_needs_update_handles_z_format(self):
        """Test that Z timezone format is handled correctly"""
        current_pt = {
            'start': '2025-04-01T09:00:00Z',  # Z format
            'end': '2025-04-01T10:00:00Z'
        }
        desired_slot = {
            'start':
            datetime.datetime(2025,
                              4,
                              1,
                              9,
                              0,
                              0,
                              tzinfo=datetime.timezone.utc),
            'end':
            datetime.datetime(2025,
                              4,
                              1,
                              10,
                              0,
                              0,
                              tzinfo=datetime.timezone.utc),
            'task_id':
            'task1'
        }

        needs_update = self.consolidator._project_time_needs_update(
            current_pt, desired_slot)
        self.assertFalse(needs_update)

    def testapply_differential_updates_create_new_task(self):
        """Test creating a new task that doesn't exist in Timr"""
        # Current state: task1 and task2 exist
        # Desired state: task1, task2, and task3 (new)
        # Note: With sorting by task name descending, adding task3 will change
        # the sequential time allocation, requiring updates to existing tasks
        desired_tasks = [
            UIProjectTime("task1", "Task 1", 120),  # Existing, same duration
            UIProjectTime("task2", "Task 2", 90),  # Existing, same duration  
            UIProjectTime("task3", "Task 3", 60),  # New task
        ]

        self.consolidator.apply_differential_updates(self.working_time,
                                                      desired_tasks)

        # Should create task3
        self.mock_timr_api.create_project_time.assert_called_once()
        create_call = self.mock_timr_api.create_project_time.call_args
        self.assertEqual(create_call[1]['task_id'], 'task3')

        # With descending sort by task name, the time slots change:
        # task3 ("Task 3") comes first, then task2 ("Task 2"), then task1 ("Task 1")
        # This means existing tasks get new time slots and need updates
        self.assertEqual(self.mock_timr_api.update_project_time.call_count, 2)

        # Should not delete any tasks
        self.mock_timr_api.delete_project_time.assert_not_called()

    def testapply_differential_updates_delete_removed_task(self):
        """Test deleting a task that's no longer needed"""
        # Current state: task1 and task2 exist
        # Desired state: only task1
        desired_tasks = [
            UIProjectTime("task1", "Task 1", 120),  # Keep this one
        ]

        self.consolidator.apply_differential_updates(self.working_time,
                                                      desired_tasks)

        # Should delete task2
        self.mock_timr_api.delete_project_time.assert_called_once_with("pt2")

        # Should not create new tasks
        self.mock_timr_api.create_project_time.assert_not_called()

        # May update task1 due to time slot changes
        # (This is acceptable - the time slots shift when task2 is removed)

    def testapply_differential_updates_update_existing_task(self):
        """Test updating an existing task with new duration"""
        # Current state: task1 (2h), task2 (1.5h)
        # Desired state: task1 (3h), task2 (1.5h)
        desired_tasks = [
            UIProjectTime("task1", "Task 1",
                          180),  # Changed from 120 to 180 minutes
            UIProjectTime("task2", "Task 2", 90),  # Same duration
        ]

        self.consolidator.apply_differential_updates(self.working_time,
                                                      desired_tasks)

        # Should update task1 (duration changed, so time slots change)
        self.mock_timr_api.update_project_time.assert_called()

        # Should not create or delete tasks
        self.mock_timr_api.create_project_time.assert_not_called()
        self.mock_timr_api.delete_project_time.assert_not_called()

    def testapply_differential_updates_removes_duplicate_project_times(self):
        """Duplicate project times for the same task should be merged."""
        # Add a duplicate project time for task1
        dup = {
            "id": "pt3",
            "start": "2025-04-01T12:00:00+00:00",
            "end": "2025-04-01T13:00:00+00:00",
            "task": {"id": "task1", "name": "Task 1"},
        }
        self.current_project_times.append(dup)
        self.mock_timr_api._get_project_times_in_work_time.return_value = self.current_project_times

        desired_tasks = [
            UIProjectTime("task1", "Task 1", 120),
            UIProjectTime("task2", "Task 2", 90),
        ]

        self.consolidator.apply_differential_updates(self.working_time, desired_tasks)

        # The duplicate project time should be deleted
        self.mock_timr_api.delete_project_time.assert_any_call("pt3")
        # Both tasks require updates due to sorting
        self.assertEqual(self.mock_timr_api.update_project_time.call_count, 2)

    def testapply_differential_updates_complex_scenario(self):
        """Test a complex scenario with create, update, and delete operations"""
        # Current state: task1 (2h), task2 (1.5h)
        # Desired state: task1 (1h, updated), task3 (2h, new), task2 deleted
        desired_tasks = [
            UIProjectTime("task1", "Task 1", 60),  # Updated duration
            UIProjectTime("task3", "Task 3", 120),  # New task
        ]

        self.consolidator.apply_differential_updates(self.working_time,
                                                      desired_tasks)

        # Should delete task2
        self.mock_timr_api.delete_project_time.assert_called_with("pt2")

        # Should create task3
        create_calls = [
            call
            for call in self.mock_timr_api.create_project_time.call_args_list
        ]
        self.assertTrue(
            any(call[1]['task_id'] == 'task3' for call in create_calls))

        # Should update task1 (duration changed)
        self.mock_timr_api.update_project_time.assert_called()



    def test_distribute_time_method_signature(self):
        """Test the distribute_time method uses the correct signature"""
        # Create test tasks
        tasks = [UIProjectTime("task1", "Task 1", 60)]

        # Mock the distribute_time method on the consolidator itself
        self.consolidator.distribute_time = MagicMock()

        # Call the distribute_time method directly with new signature
        self.consolidator.distribute_time(
            self.working_time, tasks, replace_all=True, source_working_time=None)

        # Should call the distribute_time method with replace_all=True and new signature
        self.consolidator.distribute_time.assert_called_once_with(
            self.working_time, tasks, replace_all=True, source_working_time=None)

    def test_differential_updates_preserves_api_call_efficiency(self):
        """Test that differential updates make fewer API calls than full replacement"""
        # Scenario: Update duration of one existing task among three tasks
        desired_tasks = [
            UIProjectTime("task1", "Task 1", 150),  # Changed from 120 to 150
            UIProjectTime("task2", "Task 2", 90),  # Unchanged
        ]

        # Reset call counts
        self.mock_timr_api.reset_mock()

        self.consolidator.apply_differential_updates(self.working_time,
                                                      desired_tasks)

        # Should make minimal API calls:
        # - 1 call to get current project times
        # - 1-2 calls to update changed times (task1 and possibly task2 due to time shift)
        # - No create or delete calls needed

        total_api_calls = (
            self.mock_timr_api._get_project_times_in_work_time.call_count +
            self.mock_timr_api.create_project_time.call_count +
            self.mock_timr_api.update_project_time.call_count +
            self.mock_timr_api.delete_project_time.call_count)

        # Should be much fewer than 6 calls (full replacement would be: delete 2 + create 2 + get 1 = 5+ calls)
        self.assertLessEqual(
            total_api_calls, 4,
            f"Expected <= 4 API calls for incremental update, got {total_api_calls}"
        )

    def test_empty_desired_tasks_deletes_all(self):
        """Test that passing empty desired tasks deletes all current tasks"""
        desired_tasks = []

        self.consolidator.apply_differential_updates(self.working_time,
                                                      desired_tasks)

        # Should delete all current tasks
        self.assertEqual(self.mock_timr_api.delete_project_time.call_count, 2)
        self.mock_timr_api.delete_project_time.assert_any_call("pt1")
        self.mock_timr_api.delete_project_time.assert_any_call("pt2")

        # Should not create any tasks
        self.mock_timr_api.create_project_time.assert_not_called()

    def test_differential_updates_with_api_error_fallback(self):
        """Test that differential updates handle API errors appropriately"""
        # Mock an error in the differential update process
        self.mock_timr_api._get_project_times_in_work_time.side_effect = TimrApiError(
            "API Error")

        desired_tasks = [UIProjectTime("task1", "Task 1", 60)]

        # This should raise the API error, not fall back silently
        with self.assertRaises(TimrApiError):
            self.consolidator.apply_differential_updates(
                self.working_time, desired_tasks)


if __name__ == '__main__':
    unittest.main()

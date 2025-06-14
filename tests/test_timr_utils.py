import unittest
from unittest.mock import Mock, patch, MagicMock, call
import datetime
from timr_utils import UIProjectTime, ProjectTimeConsolidator


class TestUIProjectTime(unittest.TestCase):
    """Tests for the UIProjectTime class"""

    def test_initialization(self):
        """Test that UIProjectTime initializes correctly"""
        ui_pt = UIProjectTime(task_id="task123",
                              task_name="Test Task",
                              duration_minutes=60,
                              task_breadcrumbs="Project/Feature")

        self.assertEqual(ui_pt.task_id, "task123")
        self.assertEqual(ui_pt.task_name, "Test Task")
        self.assertEqual(ui_pt.duration_minutes, 60)
        self.assertEqual(ui_pt.task_breadcrumbs, "Project/Feature")
        self.assertFalse(ui_pt.deleted)
        self.assertEqual(ui_pt.project_time_ids, [])
        self.assertEqual(ui_pt.source_project_times, [])

    def test_mark_for_deletion(self):
        """Test mark_for_deletion method"""
        ui_pt = UIProjectTime("task123", "Test Task")
        self.assertFalse(ui_pt.deleted)

        ui_pt.mark_for_deletion()
        self.assertTrue(ui_pt.deleted)

    def test_add_project_time(self):
        """Test add_project_time method"""
        ui_pt = UIProjectTime("task123", "Test Task")

        # Add a project time
        project_time = {"id": "pt1", "start": "2025-04-01T09:00:00+00:00"}
        ui_pt.add_project_time(project_time)

        self.assertEqual(len(ui_pt.project_time_ids), 1)
        self.assertEqual(ui_pt.project_time_ids[0], "pt1")
        self.assertEqual(len(ui_pt.source_project_times), 1)
        self.assertEqual(ui_pt.source_project_times[0], project_time)

        # Try adding a project time without ID
        ui_pt.add_project_time({})
        # Should not be added
        self.assertEqual(len(ui_pt.project_time_ids), 1)

    def test_to_dict(self):
        """Test to_dict method"""
        ui_pt = UIProjectTime(task_id="task123",
                              task_name="Test Task",
                              duration_minutes=60,
                              task_breadcrumbs="Project/Feature")
        ui_pt.project_time_ids = ["pt1", "pt2"]

        result = ui_pt.to_dict()

        self.assertEqual(result["task_id"], "task123")
        self.assertEqual(result["task_name"], "Test Task")
        self.assertEqual(result["duration_minutes"], 60)
        self.assertEqual(result["task_breadcrumbs"], "Project/Feature")
        self.assertFalse(result["deleted"])
        self.assertEqual(result["project_time_ids"], ["pt1", "pt2"])

    def test_from_dict(self):
        """Test from_dict method"""
        data = {
            "task_id": "task123",
            "task_name": "Test Task",
            "duration_minutes": 60,
            "task_breadcrumbs": "Project/Feature",
            "deleted": True,
            "project_time_ids": ["pt1", "pt2"]
        }

        ui_pt = UIProjectTime.from_dict(data)

        self.assertEqual(ui_pt.task_id, "task123")
        self.assertEqual(ui_pt.task_name, "Test Task")
        self.assertEqual(ui_pt.duration_minutes, 60)
        self.assertEqual(ui_pt.task_breadcrumbs, "Project/Feature")
        self.assertTrue(ui_pt.deleted)
        self.assertEqual(ui_pt.project_time_ids, ["pt1", "pt2"])

        # Test with minimal data
        minimal_data = {
            "task_id": "task123",
        }

        minimal_ui_pt = UIProjectTime.from_dict(minimal_data)
        self.assertEqual(minimal_ui_pt.task_id, "task123")
        self.assertEqual(minimal_ui_pt.task_name, "")
        self.assertEqual(minimal_ui_pt.duration_minutes, 0)
        self.assertEqual(minimal_ui_pt.task_breadcrumbs, "")
        self.assertFalse(minimal_ui_pt.deleted)
        self.assertEqual(minimal_ui_pt.project_time_ids, [])


class TestProjectTimeConsolidator(unittest.TestCase):
    """Tests for the ProjectTimeConsolidator class"""

    def setUp(self):
        """Set up test fixtures"""
        self.mock_timr_api = Mock()
        self.consolidator = ProjectTimeConsolidator(self.mock_timr_api)

        # Create a sample working time
        self.working_time = {
            "id": "wt1",
            "start": "2025-04-01T09:00:00+00:00",
            "end": "2025-04-01T17:00:00+00:00",
            "break_time_total_minutes": 30
        }

        # Create sample project times
        self.project_times = [{
            "id": "pt1",
            "start": "2025-04-01T09:00:00+00:00",
            "end": "2025-04-01T10:30:00+00:00",
            "task": {
                "id": "task1",
                "name": "Task 1",
                "breadcrumbs": "Project A/Task 1"
            }
        }, {
            "id": "pt2",
            "start": "2025-04-01T10:30:00+00:00",
            "end": "2025-04-01T12:00:00+00:00",
            "task": {
                "id": "task2",
                "name": "Task 2",
                "breadcrumbs": "Project B/Task 2"
            }
        }, {
            "id": "pt3",
            "start": "2025-04-01T13:00:00+00:00",
            "end": "2025-04-01T15:00:00+00:00",
            "task": {
                "id": "task1",
                "name": "Task 1",
                "breadcrumbs": "Project A/Task 1"
            }
        }]

        # Configure mock to return sample project times
        self.mock_timr_api._get_project_times_in_work_time.return_value = self.project_times

    def test_consolidate_project_times_basic(self):
        """Test basic consolidation of project times"""
        result = self.consolidator.consolidate_project_times(self.working_time)
        
        # Verify the structure of the result
        self.assertIn('ui_project_times', result)
        self.assertIn('working_time', result)
        self.assertIn('net_duration', result)
        self.assertIn('remaining_duration', result)
        self.assertIn('is_fully_allocated', result)
        
        # Check that the mock was called
        self.mock_timr_api._get_project_times_in_work_time.assert_called_once_with(self.working_time)

    def test_consolidate_project_times_groups_by_task(self):
        """Test that project times are properly grouped by task"""
        result = self.consolidator.consolidate_project_times(self.working_time)
        
        ui_project_times = result['ui_project_times']
        
        # Should have 2 unique tasks (task1 appears twice, task2 once)
        self.assertEqual(len(ui_project_times), 2)
        
        # Find the task1 and task2 entries
        task1_entry = next((pt for pt in ui_project_times if pt.task_id == "task1"), None)
        task2_entry = next((pt for pt in ui_project_times if pt.task_id == "task2"), None)
        
        self.assertIsNotNone(task1_entry)
        self.assertIsNotNone(task2_entry)
        
        # task1 should have 2 project time IDs (pt1 and pt3)
        self.assertEqual(len(task1_entry.project_time_ids), 2)
        self.assertIn("pt1", task1_entry.project_time_ids)
        self.assertIn("pt3", task1_entry.project_time_ids)
        
        # task2 should have 1 project time ID (pt2)
        self.assertEqual(len(task2_entry.project_time_ids), 1)
        self.assertIn("pt2", task2_entry.project_time_ids)

    def test_consolidate_project_times_calculates_durations(self):
        """Test that durations are calculated correctly"""
        result = self.consolidator.consolidate_project_times(self.working_time)
        
        # Working time is 8 hours (480 minutes) with 30 minutes break = 450 minutes net
        self.assertEqual(result['net_duration'], 450)
        
        # Total project time: pt1=90min, pt2=90min, pt3=120min = 300min
        total_allocated = sum(pt.duration_minutes for pt in result['ui_project_times'])
        self.assertEqual(total_allocated, 300)
        
        # Remaining should be 450 - 300 = 150 minutes
        self.assertEqual(result['remaining_duration'], 150)
        
        # Should not be fully allocated
        self.assertFalse(result['is_fully_allocated'])

    def test_consolidate_project_times_empty_project_times(self):
        """Test consolidation with no project times"""
        self.mock_timr_api._get_project_times_in_work_time.return_value = []
        
        result = self.consolidator.consolidate_project_times(self.working_time)
        
        self.assertEqual(len(result['ui_project_times']), 0)
        self.assertEqual(result['net_duration'], 450)
        self.assertEqual(result['remaining_duration'], 450)
        self.assertFalse(result['is_fully_allocated'])

    def test_consolidate_project_times_fully_allocated(self):
        """Test consolidation when time is fully allocated"""
        # Create project times that exactly match the working time
        full_project_times = [{
            "id": "pt_full",
            "start": "2025-04-01T09:00:00+00:00",
            "end": "2025-04-01T16:30:00+00:00",  # 7.5 hours = 450 minutes (matches net duration)
            "task": {
                "id": "task_full",
                "name": "Full Task",
                "breadcrumbs": "Project/Full Task"
            }
        }]
        
        self.mock_timr_api._get_project_times_in_work_time.return_value = full_project_times
        
        result = self.consolidator.consolidate_project_times(self.working_time)
        
        self.assertEqual(result['remaining_duration'], 0)
        self.assertTrue(result['is_fully_allocated'])

    def test_consolidate_project_times_handles_missing_task_data(self):
        """Test consolidation handles project times with missing task data"""
        incomplete_project_times = [{
            "id": "pt_incomplete",
            "start": "2025-04-01T09:00:00+00:00",
            "end": "2025-04-01T10:00:00+00:00",
            "task": {
                "id": "task_incomplete"
                # Missing name and breadcrumbs
            }
        }]
        
        self.mock_timr_api._get_project_times_in_work_time.return_value = incomplete_project_times
        
        result = self.consolidator.consolidate_project_times(self.working_time)
        
        self.assertEqual(len(result['ui_project_times']), 1)
        ui_pt = result['ui_project_times'][0]
        self.assertEqual(ui_pt.task_id, "task_incomplete")
        # Should handle missing fields gracefully

    def test_consolidate_project_times_handles_api_error(self):
        """Test consolidation handles API errors gracefully"""
        from timr_api import TimrApiError
        self.mock_timr_api._get_project_times_in_work_time.side_effect = TimrApiError("API Error")
        
        with self.assertRaises(TimrApiError):
            self.consolidator.consolidate_project_times(self.working_time)


class TestUIProjectTimeEdgeCases(unittest.TestCase):
    """Additional tests for UIProjectTime edge cases"""

    def test_initialization_with_none_values(self):
        """Test UIProjectTime handles None values gracefully"""
        ui_pt = UIProjectTime(task_id=None, task_name=None)
        
        # Should not crash and should handle None values
        self.assertIsNone(ui_pt.task_id)
        self.assertIsNone(ui_pt.task_name)
        self.assertEqual(ui_pt.duration_minutes, 0)
        self.assertEqual(ui_pt.task_breadcrumbs, "")

    def test_add_project_time_with_none(self):
        """Test add_project_time with None input"""
        ui_pt = UIProjectTime("task123", "Test Task")
        
        ui_pt.add_project_time(None)
        self.assertEqual(len(ui_pt.project_time_ids), 0)
        self.assertEqual(len(ui_pt.source_project_times), 0)

    def test_add_project_time_without_id(self):
        """Test add_project_time with dict missing ID"""
        ui_pt = UIProjectTime("task123", "Test Task")
        
        ui_pt.add_project_time({"name": "project without id"})
        self.assertEqual(len(ui_pt.project_time_ids), 0)
        self.assertEqual(len(ui_pt.source_project_times), 0)

    def test_toJSON_method(self):
        """Test the toJSON method"""
        ui_pt = UIProjectTime(task_id="task123",
                              task_name="Test Task",
                              duration_minutes=60,
                              task_breadcrumbs="Project/Feature")
        
        json_str = ui_pt.toJSON()
        self.assertIsInstance(json_str, str)
        
        # Should be valid JSON
        import json
        parsed = json.loads(json_str)
        self.assertEqual(parsed["task_id"], "task123")
        self.assertEqual(parsed["task_name"], "Test Task")

    def test_from_dict_with_invalid_data(self):
        """Test from_dict with missing or invalid data"""
        # Test with empty dict
        ui_pt = UIProjectTime.from_dict({})
        self.assertEqual(ui_pt.task_id, "")
        
        # Test with partial data
        partial_data = {
            "task_id": "task123",
            "duration_minutes": "invalid_number"  # Invalid type
        }
        
        ui_pt = UIProjectTime.from_dict(partial_data)
        self.assertEqual(ui_pt.task_id, "task123")
        # Should handle invalid duration gracefully

    def test_duration_edge_cases(self):
        """Test UIProjectTime with edge case durations"""
        # Negative duration
        ui_pt_negative = UIProjectTime("task1", "Task", -30)
        self.assertEqual(ui_pt_negative.duration_minutes, -30)
        
        # Zero duration
        ui_pt_zero = UIProjectTime("task2", "Task", 0)
        self.assertEqual(ui_pt_zero.duration_minutes, 0)
        
        # Very large duration
        ui_pt_large = UIProjectTime("task3", "Task", 99999)
        self.assertEqual(ui_pt_large.duration_minutes, 99999)


class TestProjectTimeConsolidatorEdgeCases(unittest.TestCase):
    """Additional tests for ProjectTimeConsolidator edge cases"""

    def setUp(self):
        """Set up test fixtures"""
        self.mock_timr_api = Mock()
        self.consolidator = ProjectTimeConsolidator(self.mock_timr_api)
        
        # Create a sample working time for tests that need it
        self.working_time = {
            "id": "wt1",
            "start": "2025-04-01T09:00:00+00:00",
            "end": "2025-04-01T17:00:00+00:00",
            "break_time_total_minutes": 30
        }

    def test_consolidate_with_invalid_working_time(self):
        """Test consolidation with invalid working time data"""
        invalid_working_time = {}
        
        # Should handle missing fields gracefully
        self.mock_timr_api._get_project_times_in_work_time.return_value = []
        
        # This might raise an exception or handle gracefully depending on implementation
        try:
            result = self.consolidator.consolidate_project_times(invalid_working_time)
            # If it doesn't raise an exception, verify it handles it gracefully
            self.assertIn('ui_project_times', result)
        except (KeyError, ValueError):
            # This is also acceptable behavior for invalid input
            pass

    def test_consolidate_with_malformed_project_times(self):
        """Test consolidation with malformed project time data"""
        working_time = {
            "id": "wt1",
            "start": "2025-04-01T09:00:00+00:00",
            "end": "2025-04-01T17:00:00+00:00",
            "break_time_total_minutes": 30
        }
        
        malformed_project_times = [
            {"id": "pt1"},  # Missing required fields
            {"start": "invalid_date", "end": "invalid_date"},  # Invalid dates
            None,  # None entry
            {}  # Empty dict
        ]
        
        self.mock_timr_api._get_project_times_in_work_time.return_value = malformed_project_times
        
        # Should handle malformed data gracefully
        result = self.consolidator.consolidate_project_times(working_time)
        self.assertIn('ui_project_times', result)

    def test_consolidate_with_overlapping_project_times(self):
        """Test consolidation with overlapping project times"""
        working_time = {
            "id": "wt1",
            "start": "2025-04-01T09:00:00+00:00",
            "end": "2025-04-01T17:00:00+00:00",
            "break_time_total_minutes": 30
        }
        
        overlapping_project_times = [{
            "id": "pt1",
            "start": "2025-04-01T09:00:00+00:00",
            "end": "2025-04-01T11:00:00+00:00",  # 2 hours
            "task": {"id": "task1", "name": "Task 1", "breadcrumbs": "Project/Task 1"}
        }, {
            "id": "pt2",
            "start": "2025-04-01T10:00:00+00:00",  # Overlaps with pt1
            "end": "2025-04-01T12:00:00+00:00",  # 2 hours
            "task": {"id": "task2", "name": "Task 2", "breadcrumbs": "Project/Task 2"}
        }]
        
        self.mock_timr_api._get_project_times_in_work_time.return_value = overlapping_project_times
        
        result = self.consolidator.consolidate_project_times(working_time)
        
        # Should handle overlapping times (behavior depends on implementation)
        self.assertEqual(len(result['ui_project_times']), 2)
        
        # Total duration might be more than net duration due to overlap
        total_allocated = sum(pt.duration_minutes for pt in result['ui_project_times'])
        # This tests the behavior - it might handle overlap or sum them up

        # Configure distribute_time to return created project times
        self.mock_timr_api.distribute_time.return_value = [{
            "id": "new_pt1",
            "task_id": "task1"
        }, {
            "id": "new_pt2",
            "task_id": "task2"
        }]

    def test_consolidate_project_times(self):
        """Test consolidate_project_times method"""
        # Set up mock return value - empty list means no project times
        self.mock_timr_api._get_project_times_in_work_time.return_value = []
        
        # Call the method under test
        result = self.consolidator.consolidate_project_times(self.working_time)

        # Verify the mock was called
        self.mock_timr_api._get_project_times_in_work_time.assert_called_once_with(
            self.working_time)

        # Check result structure
        self.assertEqual(result["working_time"], self.working_time)
        self.assertIn("ui_project_times", result)

        # Check UI project times - with empty input, should have 0 tasks
        ui_project_times = result["ui_project_times"]
        self.assertEqual(len(ui_project_times), 0)  # Empty input = empty output

        # Verify basic structure is correct
        self.assertIn("net_duration", result)
        self.assertIn("remaining_duration", result)
        self.assertIn("is_fully_allocated", result)

    def test_get_ui_project_times(self):
        """Test get_ui_project_times method"""
        # Set up mock return value - empty list
        self.mock_timr_api._get_project_times_in_work_time.return_value = []
        
        # Call the method under test
        result = self.consolidator.get_ui_project_times(self.working_time)

        # Verify result is a list of UIProjectTime objects
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 0)  # Empty input = empty output

    def test_add_ui_project_time(self):
        """Test add_ui_project_time method with new incremental logic"""
        # Create existing UIProjectTime objects
        ui_pt1 = UIProjectTime("task1", "Task 1", 210, "Project A/Task 1")
        ui_pt2 = UIProjectTime("task2", "Task 2", 90, "Project B/Task 2")

        # Mock get_ui_project_times to return existing tasks
        self.consolidator.get_ui_project_times = MagicMock(
            return_value=[ui_pt1, ui_pt2])

        # Mock consolidate_project_times to return updated state after operation
        updated_ui_pt3 = UIProjectTime("task3", "Task 3", 60,
                                       "Project C/Task 3")
        self.consolidator.consolidate_project_times = MagicMock(
            return_value={
                "ui_project_times": [ui_pt1, ui_pt2, updated_ui_pt3],
                "total_duration": 360,
                "net_duration": 450,
                "remaining_duration": 90,
                "is_fully_allocated": False
            })

        # Mock the differential updates method
        self.consolidator.apply_differential_updates = MagicMock()

        # Call the method under test - add a new task
        result = self.consolidator.add_ui_project_time(self.working_time,
                                                       "task3", "Task 3", 60)

        # Verify differential updates was called
        self.consolidator.apply_differential_updates.assert_called_once()

        # Verify the result structure
        self.assertIn("ui_project_times", result)
        self.assertEqual(len(result["ui_project_times"]), 3)
        self.assertEqual(result["total_duration"], 360)

    def test_update_ui_project_time(self):
        """Test update_ui_project_time method with new incremental logic"""
        # Create UIProjectTime objects for the get_ui_project_times result
        ui_pt1 = UIProjectTime("task1", "Task 1", 210, "Project A/Task 1")
        ui_pt2 = UIProjectTime("task2", "Task 2", 90, "Project B/Task 2")

        # Configure mock methods
        self.consolidator.get_ui_project_times = MagicMock(
            return_value=[ui_pt1, ui_pt2])

        # Mock consolidate_project_times to return updated state
        ui_pt1_updated = UIProjectTime("task1", "Updated Task 1", 120,
                                       "Project A/Task 1")
        self.consolidator.consolidate_project_times = MagicMock(
            return_value={
                "ui_project_times": [ui_pt1_updated, ui_pt2],
                "total_duration": 210,
                "net_duration": 450,
                "remaining_duration": 240,
                "is_fully_allocated": False
            })

        # Mock the differential updates method
        self.consolidator.apply_differential_updates = MagicMock()

        # Call the method under test - update task1
        result = self.consolidator.update_ui_project_time(
            self.working_time, "task1", 120, "Updated Task 1")

        # Verify differential updates was called
        self.consolidator.apply_differential_updates.assert_called_once()

        # Verify the result
        self.assertIn("ui_project_times", result)
        self.assertEqual(result["total_duration"], 210)

    def test_delete_ui_project_time(self):
        """Test delete_ui_project_time method with new incremental logic"""
        # Create UIProjectTime objects for the get_ui_project_times result
        ui_pt1 = UIProjectTime("task1", "Task 1", 210, "Project A/Task 1")
        ui_pt2 = UIProjectTime("task2", "Task 2", 90, "Project B/Task 2")

        # Configure mock methods
        self.consolidator.get_ui_project_times = MagicMock(
            return_value=[ui_pt1, ui_pt2])

        # Mock consolidate_project_times to return updated state (task1 removed)
        self.consolidator.consolidate_project_times = MagicMock(
            return_value={
                "ui_project_times": [ui_pt2],
                "total_duration": 90,
                "net_duration": 450,
                "remaining_duration": 360,
                "is_fully_allocated": False
            })

        # Mock the differential updates method
        self.consolidator.apply_differential_updates = MagicMock()

        # Call the method under test - delete task1
        result = self.consolidator.delete_ui_project_time(
            self.working_time, "task1")

        # Verify differential updates was called
        self.consolidator.apply_differential_updates.assert_called_once()

        # Verify the result
        self.assertIn("ui_project_times", result)
        self.assertEqual(len(result["ui_project_times"]), 1)
        self.assertEqual(result["total_duration"], 90)

    def test_replace_ui_project_times(self):
        """Test replace_ui_project_times method"""
        # Create replacement UI project times
        new_ui_pt1 = UIProjectTime("task4", "Task 4", 120, "Project C/Task 4")
        new_ui_pt2 = UIProjectTime("task5", "Task 5", 180, "Project D/Task 5")

        # Mock the distribute_time method and consolidate_project_times
        self.consolidator.distribute_time = MagicMock()
        self.consolidator.consolidate_project_times = MagicMock(
            return_value={
                "ui_project_times": [new_ui_pt1, new_ui_pt2],
                "total_duration": 300,
                "net_duration": 450,
                "remaining_duration": 150,
                "is_fully_allocated": False
            })

        # Call the method under test
        result = self.consolidator.replace_ui_project_times(
            self.working_time, [new_ui_pt1, new_ui_pt2])

        # Verify distribute_time was called with replace_all=True
        self.consolidator.distribute_time.assert_called_once_with(
            work_time_entry=self.working_time,
            ui_project_times=[new_ui_pt1, new_ui_pt2],
            replace_all=True)

        # Verify consolidate_project_times was called
        self.consolidator.consolidate_project_times.assert_called_once_with(
            self.working_time)

    def test_distribute_time(self):
        """Test distribute_time method with UIProjectTime objects"""
        # Create UIProjectTime objects
        ui_pt1 = UIProjectTime("task1", "Task 1", 120)
        ui_pt2 = UIProjectTime("task2", "Task 2", 180)

        # Configure mock to delete existing project times
        self.mock_timr_api._delete_existing_project_times.return_value = 3

        # Configure mock to create new project times
        self.mock_timr_api.create_project_time.side_effect = [{
            "id":
            "new_pt1",
            "task_id":
            "task1",
            "start":
            "2025-04-01T09:00:00+00:00",
            "end":
            "2025-04-01T11:00:00+00:00"
        }, {
            "id":
            "new_pt2",
            "task_id":
            "task2",
            "start":
            "2025-04-01T11:00:00+00:00",
            "end":
            "2025-04-01T14:00:00+00:00"
        }]

        # Mock apply_differential_updates method
        self.consolidator.apply_differential_updates = Mock()

        # Mock the return value for _get_project_times_in_work_time
        mock_result = [{
            "id": "new_pt1",
            "task_id": "task1",
            "start": "2025-04-01T09:00:00+00:00",
            "end": "2025-04-01T11:00:00+00:00"
        }, {
            "id": "new_pt2",
            "task_id": "task2",
            "start": "2025-04-01T11:00:00+00:00",
            "end": "2025-04-01T14:00:00+00:00"
        }]
        self.mock_timr_api._get_project_times_in_work_time.return_value = mock_result

        # Call the method under test
        result = self.consolidator.distribute_time(self.working_time,
                                                   [ui_pt1, ui_pt2],
                                                   replace_all=True)

        # Verify apply_differential_updates was called
        self.consolidator.apply_differential_updates.assert_called_once_with(
            self.working_time, [ui_pt1, ui_pt2], None)

        # Verify the result matches mock return value
        self.assertEqual(result, mock_result)

    def test_distribute_project_times_sequentially(self):
        """Test distribute_time method with UIProjectTime objects (replaces old sequential method)"""
        # Create UIProjectTime objects instead of raw task durations
        from timr_utils import UIProjectTime
        ui_pt1 = UIProjectTime(task_id="task1", duration_minutes=120, task_name="Task 1")
        ui_pt2 = UIProjectTime(task_id="task2", duration_minutes=180, task_name="Task 2")

        # Mock apply_differential_updates method
        self.consolidator.apply_differential_updates = Mock()

        # Mock the return value for _get_project_times_in_work_time
        mock_result = [{
            "id": "new_pt1",
            "task_id": "task1", 
            "start": "2025-04-01T09:00:00+00:00",
            "end": "2025-04-01T11:00:00+00:00"
        }, {
            "id": "new_pt2",
            "task_id": "task2",
            "start": "2025-04-01T11:00:00+00:00", 
            "end": "2025-04-01T14:00:00+00:00"
        }]
        self.mock_timr_api._get_project_times_in_work_time.return_value = mock_result

        # Call the distribute_time method (new unified approach)
        result = self.consolidator.distribute_time(
            self.working_time, [ui_pt1, ui_pt2], replace_all=True)

        # Verify apply_differential_updates was called
        self.consolidator.apply_differential_updates.assert_called_once_with(
            self.working_time, [ui_pt1, ui_pt2], None)

        # Verify the result matches mock return value
        self.assertEqual(result, mock_result)

    def test_consolidate_running_working_time(self):
        """consolidate_project_times handles working times without end"""
        working_time = {
            "id": "wt-running",
            "start": "2025-06-14T22:51:00+00:00",
            "end": None,
            "duration": {"type": "ongoing", "minutes": 30},
            "break_time_total_minutes": 0,
        }

        self.mock_timr_api._get_project_times_in_work_time.return_value = []

        result = self.consolidator.consolidate_project_times(working_time)

        self.assertEqual(result["net_duration"], 30)
        self.assertEqual(result["remaining_duration"], 30)


if __name__ == '__main__':
    unittest.main()

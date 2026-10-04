import unittest
import datetime
import logging
from timr_api import TimrApiError
from timr_utils import ProjectTimeConsolidator
from tests.utils.integration import create_integration_api, get_attendance_working_time_type_id

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class EnhancedTimrIntegrationTest(unittest.TestCase):
    """
    Enhanced integration tests for incremental update functionality.

    These tests verify that the incremental update logic of the
    ProjectTimeConsolidator works correctly with the real Timr.com API.

    All tests use the same time slot, so each test removes the working time and
    project times it created before the next test starts.

    IMPORTANT: These tests use the real Timr API and will make actual changes.
    See tests/utils/integration.py for the required environment variables.
    """

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures for all tests."""
        # Initialize API client and consolidator
        cls.api = create_integration_api()
        cls.user_id = cls.api.user["id"]
        cls.working_time_type_id = get_attendance_working_time_type_id(cls.api)
        cls.consolidator = ProjectTimeConsolidator(cls.api)

        # Test date (yesterday to avoid API restrictions)
        yesterday = datetime.date.today() - datetime.timedelta(days=1)
        cls.test_date = yesterday
        cls.test_date_str = yesterday.strftime("%Y-%m-%d")

    def setUp(self):
        """Start each test without tracked test data."""
        self.test_working_times = []

    def tearDown(self):
        """Delete the working times created by the test and all project times within them."""
        for working_time in self.test_working_times:
            for pt in self.api._get_project_times_in_work_time(working_time):
                try:
                    self.api.delete_project_time(pt["id"])
                except TimrApiError as e:
                    logger.warning(f"Could not delete test project time {pt['id']}: {e}")
            try:
                self.api.delete_working_time(working_time["id"])
            except TimrApiError as e:
                logger.warning(f"Could not delete test working time {working_time['id']}: {e}")

    def test_01_incremental_add_single_task(self):
        """Test adding a single task using incremental updates."""
        # Create a working time for testing
        working_time = self._create_test_working_time()
        bookable_task = self._get_bookable_tasks(1)[0]

        # Add a single task using incremental update
        result = self.consolidator.add_ui_project_time(
            working_time=working_time,
            task_id=bookable_task["id"],
            task_name=bookable_task["name"],
            duration_minutes=120  # 2 hours
        )

        # Verify the result
        self.assertIn('ui_project_times', result)
        self.assertEqual(len(result['ui_project_times']), 1)
        self.assertEqual(result['ui_project_times'][0].task_id,
                         bookable_task["id"])
        self.assertEqual(result['ui_project_times'][0].duration_minutes, 120)

        # The total_duration should match our single task duration
        self.assertEqual(
            result['total_duration'], 120,
            f"Expected total_duration of 120, got {result['total_duration']}")

        # Verify it was actually created in Timr
        project_times = self.api._get_project_times_in_work_time(working_time)
        self.assertGreater(len(project_times), 0)

    def test_02_incremental_update_existing_task(self):
        """Test updating an existing task using incremental updates."""
        # Create a working time with an initial task
        working_time = self._create_test_working_time()
        bookable_task = self._get_bookable_tasks(1)[0]

        # Add initial task
        self.consolidator.add_ui_project_time(
            working_time=working_time,
            task_id=bookable_task["id"],
            task_name=bookable_task["name"],
            duration_minutes=60  # 1 hour initially
        )

        # Update the task duration
        result = self.consolidator.update_ui_project_time(
            working_time=working_time,
            task_id=bookable_task["id"],
            duration_minutes=180,  # Change to 3 hours
            task_name=bookable_task["name"])

        # Verify the update
        self.assertEqual(len(result['ui_project_times']), 1)
        self.assertEqual(result['ui_project_times'][0].duration_minutes, 180)

        # Verify in Timr
        project_times = self.api._get_project_times_in_work_time(working_time)
        total_duration = sum(
            self._calculate_project_time_duration(pt) for pt in project_times
            if pt.get('task', {}).get('id') == bookable_task["id"])
        self.assertEqual(total_duration, 180)

    def test_03_incremental_delete_task(self):
        """Test deleting a task using incremental updates."""
        # Create a working time with a task
        working_time = self._create_test_working_time()
        bookable_task = self._get_bookable_tasks(1)[0]

        # Add the task
        result = self.consolidator.add_ui_project_time(
            working_time=working_time,
            task_id=bookable_task["id"],
            task_name=bookable_task["name"],
            duration_minutes=120  # 2 hours
        )

        # Verify it was added
        self.assertEqual(len(result['ui_project_times']), 1)
        self.assertEqual(result['ui_project_times'][0].task_id, bookable_task["id"])

        # Delete the task
        result = self.consolidator.delete_ui_project_time(
            working_time=working_time, task_id=bookable_task["id"])

        # Verify deletion - should have no project times
        self.assertEqual(len(result['ui_project_times']), 0)

        # Verify in Timr - should have no project times
        project_times = self.api._get_project_times_in_work_time(working_time)
        task_ids = [pt.get('task', {}).get('id') for pt in project_times]
        self.assertNotIn(bookable_task["id"], task_ids)

    def test_05_complex_incremental_scenario(self):
        """Test a complex scenario with multiple incremental operations."""
        # Create working time
        working_time = self._create_test_working_time()
        bookable_tasks = self._get_bookable_tasks(4)

        # Phase 1: Add three tasks
        for i, task in enumerate(bookable_tasks[:3]):
            self.consolidator.add_ui_project_time(
                working_time=working_time,
                task_id=task["id"],
                task_name=task["name"],
                duration_minutes=60 * (i + 1)  # 1h, 2h, 3h
            )

        # Phase 2: Update middle task duration
        self.consolidator.update_ui_project_time(
            working_time=working_time,
            task_id=bookable_tasks[1]["id"],
            duration_minutes=90  # Change from 2h to 1.5h
        )

        # Phase 3: Delete first task
        self.consolidator.delete_ui_project_time(
            working_time=working_time, task_id=bookable_tasks[0]["id"])

        # Phase 4: Add new task
        result = self.consolidator.add_ui_project_time(
            working_time=working_time,
            task_id=bookable_tasks[3]["id"],
            task_name=bookable_tasks[3]["name"],
            duration_minutes=45  # 45 minutes
        )

        # Verify final state
        self.assertEqual(len(result['ui_project_times']), 3)

        # Check that we have the expected tasks
        final_task_ids = [
            ui_pt.task_id for ui_pt in result['ui_project_times']
        ]
        self.assertNotIn(bookable_tasks[0]["id"], final_task_ids)  # Deleted
        self.assertIn(bookable_tasks[1]["id"], final_task_ids)  # Updated
        self.assertIn(bookable_tasks[2]["id"], final_task_ids)  # Unchanged
        self.assertIn(bookable_tasks[3]["id"], final_task_ids)  # Added

        # Verify durations
        task1_duration = next(ui_pt.duration_minutes
                              for ui_pt in result['ui_project_times']
                              if ui_pt.task_id == bookable_tasks[1]["id"])
        self.assertEqual(task1_duration, 90)  # Updated duration

    def test_06_incremental_updates_preserve_data_integrity(self):
        """Test that incremental updates maintain data integrity."""
        # Create working time
        working_time = self._create_test_working_time()
        bookable_tasks = self._get_bookable_tasks(2)

        # Add tasks with specific durations
        durations = [90, 120]  # 1.5h, 2h
        for task, duration in zip(bookable_tasks, durations):
            self.consolidator.add_ui_project_time(working_time=working_time,
                                                  task_id=task["id"],
                                                  task_name=task["name"],
                                                  duration_minutes=duration)

        # Get the consolidated view
        consolidated = self.consolidator.consolidate_project_times(
            working_time)

        # Verify total duration matches sum of individual durations
        expected_total = sum(durations)
        self.assertEqual(consolidated['total_duration'], expected_total)

        # Verify individual task durations are preserved
        for ui_pt in consolidated['ui_project_times']:
            expected_duration = durations[bookable_tasks.index(
                next(task for task in bookable_tasks
                     if task["id"] == ui_pt.task_id))]
            self.assertEqual(ui_pt.duration_minutes, expected_duration)

        # Verify project times in Timr match expected durations
        project_times = self.api._get_project_times_in_work_time(working_time)
        timr_total_duration = sum(
            self._calculate_project_time_duration(pt) for pt in project_times)
        self.assertEqual(timr_total_duration, expected_total)

    def test_07_error_recovery_in_incremental_updates(self):
        """Test error recovery mechanisms in incremental updates."""
        # Create working time
        working_time = self._create_test_working_time()
        bookable_task = self._get_bookable_tasks(1)[0]

        # Add a valid task first
        self.consolidator.add_ui_project_time(working_time=working_time,
                                              task_id=bookable_task["id"],
                                              task_name=bookable_task["name"],
                                              duration_minutes=60)

        # Try to add an invalid task (non-existent task ID)
        # This should either fail gracefully or fall back to full replacement
        try:
            self.consolidator.add_ui_project_time(
                working_time=working_time,
                task_id="non-existent-task-id",
                task_name="Non-existent Task",
                duration_minutes=30)
            # If it succeeds, the API might be more permissive than expected
            logger.info("API allowed non-existent task ID - checking result")
        except Exception as e:
            logger.info(f"Expected error when adding non-existent task: {e}")
            # This is expected behavior - verify original task is still there
            consolidated = self.consolidator.consolidate_project_times(
                working_time)
            self.assertEqual(len(consolidated['ui_project_times']), 1)
            self.assertEqual(consolidated['ui_project_times'][0].task_id,
                             bookable_task["id"])

    # Helper methods
    def _create_test_working_time(self):
        """Create a test working time and track it for cleanup."""
        start = f"{self.test_date_str}T09:00:00+00:00"
        end = f"{self.test_date_str}T17:00:00+00:00"
        pause_duration = 30

        wt = self.api.create_working_time(start=start,
                                          end=end,
                                          pause_duration=pause_duration,
                                          working_time_type_id=self.working_time_type_id)

        self.test_working_times.append(wt)
        return wt

    def _get_bookable_tasks(self, count):
        """Return `count` tasks the test user can book on, or skip the test."""
        tasks = self.api.get_bookable_tasks()
        if len(tasks) < count:
            self.skipTest(f"Test user needs at least {count} bookable tasks, found {len(tasks)}")
        return tasks[:count]

    def _calculate_project_time_duration(self, project_time):
        """Calculate duration of a project time in minutes."""
        try:
            if 'duration' in project_time and project_time[
                    'duration'] and 'minutes' in project_time['duration']:
                return int(project_time['duration']['minutes'])
            else:
                start_str = project_time.get("start",
                                             "").replace('Z', '+00:00')
                end_str = project_time.get("end", "").replace('Z', '+00:00')
                start = datetime.datetime.fromisoformat(start_str)
                end = datetime.datetime.fromisoformat(end_str)
                return int((end - start).total_seconds() / 60)
        except (ValueError, TypeError, KeyError):
            return 0


if __name__ == '__main__':
    unittest.main()

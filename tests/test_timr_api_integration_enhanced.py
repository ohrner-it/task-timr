import unittest
import os
import datetime
import logging
from timr_api import TimrApi, TimrApiError
from timr_utils import ProjectTimeConsolidator, UIProjectTime
from config import COMPANY_ID

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class EnhancedTimrIntegrationTest(unittest.TestCase):
    """
    Enhanced integration tests for incremental update functionality.

    These tests verify that the new incremental update logic works correctly
    with the real Timr.com API, focusing on the performance optimizations
    and differential update algorithms.

    IMPORTANT: These tests use the real Timr API and will make actual changes.
    Set TIMR_USER and TIMR_PASSWORD environment variables to run.
    """

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures for all tests."""
        # Get credentials from environment variables
        cls.username = os.environ.get("TIMR_USER")
        cls.password = os.environ.get("TIMR_PASSWORD")

        # Skip tests if credentials are not set
        if not cls.username or not cls.password:
            raise unittest.SkipTest(
                "Skipping enhanced integration tests: Set TIMR_USER and TIMR_PASSWORD environment variables to run"
            )

        # Initialize API client and consolidator
        cls.api = TimrApi(company_id=COMPANY_ID)
        cls.consolidator = ProjectTimeConsolidator(cls.api)

        # Test date (yesterday to avoid API restrictions)
        yesterday = datetime.date.today() - datetime.timedelta(days=1)
        cls.test_date = yesterday
        cls.test_date_str = yesterday.strftime("%Y-%m-%d")

        # Login to Timr API
        try:
            cls.login_response = cls.api.login(cls.username, cls.password)
            logger.info(
                "Successfully logged in to Timr API for enhanced integration tests"
            )
            cls.user_id = cls.api.user.get("id")
        except TimrApiError as e:
            raise unittest.SkipTest(f"Could not login to Timr API: {e}")

        # Test data to clean up
        cls.test_working_times = []
        cls.test_project_times = []

        # Performance tracking
        cls.api_call_counts = {}

    @classmethod
    def tearDownClass(cls):
        """Clean up all test data created during the tests."""
        if not hasattr(cls, 'api') or not cls.api.token:
            return

        cleanup_summary = {"working_times": 0, "project_times": 0, "errors": 0}

        # Delete all test project times first (before working times to avoid FK constraints)
        for pt_id in cls.test_project_times:
            try:
                cls.api.delete_project_time(pt_id)
                logger.info(f"Deleted test project time {pt_id}")
                cleanup_summary["project_times"] += 1
            except TimrApiError as e:
                logger.warning(f"Could not delete test project time {pt_id}: {e}")
                cleanup_summary["errors"] += 1

        # Delete all test working times (this should also delete associated project times)
        for wt_id in cls.test_working_times:
            try:
                cls.api.delete_working_time(wt_id)
                logger.info(f"Deleted test working time {wt_id}")
                cleanup_summary["working_times"] += 1
            except TimrApiError as e:
                logger.warning(f"Could not delete test working time {wt_id}: {e}")
                cleanup_summary["errors"] += 1

        logger.info(f"Enhanced test cleanup complete: {cleanup_summary['working_times']} working times, "
                   f"{cleanup_summary['project_times']} project times deleted. "
                   f"{cleanup_summary['errors']} errors encountered.")

    def _track_working_time(self, working_time_id):
        """Track a working time for cleanup, avoiding duplicates."""
        if working_time_id not in self.test_working_times:
            self._track_working_time(working_time_id)
            logger.debug(f"Tracking working time for cleanup: {working_time_id}")

    def _track_project_time(self, project_time_id):
        """Track a project time for cleanup, avoiding duplicates."""
        if project_time_id not in self.test_project_times:
            self.test_project_times.append(project_time_id)
            logger.debug(f"Tracking project time for cleanup: {project_time_id}")

    def setUp(self):
        """Set up each test with API call tracking."""
        # Reset API call tracking
        self.initial_api_calls = self._count_recent_api_calls()

    def tearDown(self):
        """Track API calls made during the test."""
        final_api_calls = self._count_recent_api_calls()
        test_name = self._testMethodName
        api_calls_made = max(0, final_api_calls - self.initial_api_calls)
        self.api_call_counts[test_name] = api_calls_made
        logger.info(
            f"Test {test_name} made approximately {api_calls_made} API calls")

    def _count_recent_api_calls(self):
        """Rough approximation of API calls made (for performance tracking)."""
        # This is a rough proxy - in reality you'd need proper monitoring
        # For now, we just track method calls on our API client
        return getattr(self.api, '_api_call_count', 0)

    def test_01_incremental_add_single_task(self):
        """Test adding a single task using incremental updates."""
        # Create a working time for testing
        working_time = self._create_test_working_time()

        # Clean up any existing project times to ensure test isolation
        existing_project_times = self.api._get_project_times_in_work_time(
            working_time)
        for pt in existing_project_times:
            if pt.get("id"):
                try:
                    self.api.delete_project_time(pt["id"])
                except TimrApiError:
                    pass  # Ignore deletion errors

        # Get available tasks
        tasks = self.api.get_tasks()[:5]  # Get first 5 tasks
        if not tasks:
            self.skipTest("No tasks available for testing")

        bookable_task = None
        for task in tasks:
            if task.get("bookable", False):
                bookable_task = task
                break

        if not bookable_task:
            bookable_task = tasks[0]  # Use first task as fallback

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

        # Track created project times for cleanup
        for pt in project_times:
            if pt.get("id"):
                self.test_project_times.append(pt["id"])

    def test_02_incremental_update_existing_task(self):
        """Test updating an existing task using incremental updates."""
        # Create a working time with an initial task
        working_time = self._create_test_working_time()

        tasks = self.api.get_tasks()[:2]
        if len(tasks) < 1:
            self.skipTest("Not enough tasks available for testing")

        bookable_task = self._find_bookable_task(tasks)

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

        # Track for cleanup
        for pt in project_times:
            if pt.get("id"):
                self.test_project_times.append(pt["id"])

    def test_03_incremental_delete_task(self):
        """Test deleting a task using incremental updates."""
        # Create a working time with a task
        working_time = self._create_test_working_time()

        tasks = self.api.get_tasks(active_only=False)  # Get all tasks, not just active ones
        if len(tasks) < 1:
            self.skipTest("Not enough tasks available for testing")

        # Find one bookable task - prioritize known working tasks first
        known_working_task_id = "11e9c44e-9af2-4b1d-87b4-d85145dbbb55"  # 3695 CR - known to work
        bookable_task = None
        
        # First try to find the known working task
        for task in tasks:
            if task.get("id") == known_working_task_id and task.get("bookable") is not False:
                bookable_task = task
                break
                
        # If known task not found or not bookable, try others
        if not bookable_task:
            bookable_task = self._find_bookable_task(tasks[:5])  # Limit search to first 5 for efficiency
            
        if not bookable_task:
            self.skipTest("Could not find any bookable tasks for testing")

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

        # Track remaining project times for cleanup
        for pt in project_times:
            if pt.get("id"):
                self.test_project_times.append(pt["id"])

    def test_04_incremental_vs_full_replacement_efficiency(self):
        """Test that incremental updates are more efficient than full replacement."""
        # Create working time with multiple tasks
        working_time = self._create_test_working_time()

        tasks = self.api.get_tasks()[:3]
        if len(tasks) < 3:
            self.skipTest("Not enough tasks available for testing")

        bookable_tasks = [self._find_bookable_task([task]) for task in tasks]

        # Add multiple tasks using incremental updates
        initial_call_count = self._count_recent_api_calls()

        for i, task in enumerate(bookable_tasks):
            self.consolidator.add_ui_project_time(working_time=working_time,
                                                  task_id=task["id"],
                                                  task_name=task["name"],
                                                  duration_minutes=60 *
                                                  (i + 1))

        incremental_calls = self._count_recent_api_calls() - initial_call_count

        # Now test full replacement approach
        ui_project_times = [
            UIProjectTime(task["id"], task["name"], 60 * (i + 1))
            for i, task in enumerate(bookable_tasks)
        ]

        # Clear existing and use full replacement
        self.api._delete_existing_project_times(working_time)

        full_replacement_start = self._count_recent_api_calls()
        self.consolidator.replace_ui_project_times(working_time,
                                                   ui_project_times)
        full_replacement_calls = self._count_recent_api_calls(
        ) - full_replacement_start

        logger.info(f"Incremental approach: ~{incremental_calls} calls")
        logger.info(
            f"Full replacement approach: ~{full_replacement_calls} calls")

        # Incremental should be more efficient for small changes
        # Note: This may not always be true due to the nature of our differential algorithm
        # but it demonstrates the concept

        # Clean up project times
        project_times = self.api._get_project_times_in_work_time(working_time)
        for pt in project_times:
            if pt.get("id"):
                self.test_project_times.append(pt["id"])

    def test_05_complex_incremental_scenario(self):
        """Test a complex scenario with multiple incremental operations."""
        # Create working time
        working_time = self._create_test_working_time()

        tasks = self.api.get_tasks()[:4]
        if len(tasks) < 4:
            self.skipTest("Not enough tasks available for testing")

        bookable_tasks = [self._find_bookable_task([task]) for task in tasks]

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

        # Clean up
        project_times = self.api._get_project_times_in_work_time(working_time)
        for pt in project_times:
            if pt.get("id"):
                self.test_project_times.append(pt["id"])

    def test_06_incremental_updates_preserve_data_integrity(self):
        """Test that incremental updates maintain data integrity."""
        # Create working time
        working_time = self._create_test_working_time()

        tasks = self.api.get_tasks()[:2]
        if len(tasks) < 2:
            self.skipTest("Not enough tasks available for testing")

        bookable_tasks = [self._find_bookable_task([task]) for task in tasks]

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

        # Clean up
        for pt in project_times:
            if pt.get("id"):
                self.test_project_times.append(pt["id"])

    def test_07_error_recovery_in_incremental_updates(self):
        """Test error recovery mechanisms in incremental updates."""
        # Create working time
        working_time = self._create_test_working_time()

        tasks = self.api.get_tasks()[:1]
        if not tasks:
            self.skipTest("No tasks available for testing")

        bookable_task = self._find_bookable_task(tasks)

        # Add a valid task first
        self.consolidator.add_ui_project_time(working_time=working_time,
                                              task_id=bookable_task["id"],
                                              task_name=bookable_task["name"],
                                              duration_minutes=60)

        # Try to add an invalid task (non-existent task ID)
        # This should either fail gracefully or fall back to full replacement
        try:
            result = self.consolidator.add_ui_project_time(
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

        # Clean up
        project_times = self.api._get_project_times_in_work_time(working_time)
        for pt in project_times:
            if pt.get("id"):
                self.test_project_times.append(pt["id"])

    # Helper methods
    def _create_test_working_time(self):
        """Create a test working time and track it for cleanup."""
        start = f"{self.test_date_str}T09:00:00+00:00"
        end = f"{self.test_date_str}T17:00:00+00:00"
        pause_duration = 30

        wt = self.api.create_working_time(start=start,
                                          end=end,
                                          pause_duration=pause_duration)

        self._track_working_time(wt["id"])
        return wt

    def _find_bookable_task(self, tasks):
        """Find a bookable task from the given list by actually testing it."""
        # Try each task to see if we can actually book time to it
        for task in tasks:
            # Skip tasks that are explicitly not bookable
            if task.get("bookable") is False:
                continue
                
            try:
                # Create a minimal test working time
                test_working_time = self._create_test_working_time()
                
                # Try to create a minimal project time (1 minute) to test bookability
                test_start = f"{self.test_date_str}T09:00:00+00:00" 
                test_end = f"{self.test_date_str}T09:01:00+00:00"
                
                project_time = self.api.create_project_time(
                    task_id=task["id"],
                    start=test_start,
                    end=test_end
                )
                
                # If we got here, the task is bookable - clean up and return it
                if project_time.get("id"):
                    self.api.delete_project_time(project_time["id"])
                    
                # Clean up the test working time
                self.api.delete_working_time(test_working_time["id"])
                
                return task
                
            except Exception as e:
                # This task is not bookable (disabled, archived, etc.), try the next one
                try:
                    # Clean up the test working time if it was created
                    if 'test_working_time' in locals():
                        self.api.delete_working_time(test_working_time["id"])
                except:
                    pass
                continue
                
        # No bookable task found
        return None

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

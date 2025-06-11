import unittest
import os
import datetime
import logging
from timr_api import TimrApi, TimrApiError
from config import COMPANY_ID

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class TimrAPIIntegrationTest(unittest.TestCase):
    """
    Integration tests for the Timr API client against the real Timr API.

    IMPORTANT: These tests will use the real Timr.com API service, not mocks.

    To run these tests:
    1. Set the environment variables TIMR_USER and TIMR_PASSWORD
    2. The test will use the company ID from config.py (default: "ohrnerit")

    These tests will:
    1. Login to the real Timr API
    2. Create real working times and project times 
    3. Validate the responses and behavior 
    4. Clean up any test data created

    WARNING: These tests WILL make changes to your Timr.com account!
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
                "Skipping integration tests: Set TIMR_USER and TIMR_PASSWORD environment variables to run"
            )

        # Initialize API client
        cls.api = TimrApi(company_id=COMPANY_ID)

        # Test date (yesterday to work with API restrictions on future dates)
        yesterday = datetime.date.today() - datetime.timedelta(days=1)
        cls.test_date = yesterday
        cls.test_date_str = yesterday.strftime("%Y-%m-%d")

        # Login to Timr API
        try:
            cls.login_response = cls.api.login(cls.username, cls.password)
            logger.info("Successfully logged in to Timr API")
            cls.user_id = cls.api.user.get("id")
        except TimrApiError as e:
            raise unittest.SkipTest(f"Could not login to Timr API: {e}")

        # Test data to clean up
        cls.test_working_times = []
        cls.test_project_times = []

    @classmethod
    def tearDownClass(cls):
        """Clean up all test data created during the tests."""
        if not hasattr(cls, 'api') or not cls.api.token:
            return  # Skip if setup failed

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

        # Delete all test working times
        for wt_id in cls.test_working_times:
            try:
                cls.api.delete_working_time(wt_id)
                logger.info(f"Deleted test working time {wt_id}")
                cleanup_summary["working_times"] += 1
            except TimrApiError as e:
                logger.warning(f"Could not delete test working time {wt_id}: {e}")
                cleanup_summary["errors"] += 1

        logger.info(f"Cleanup complete: {cleanup_summary['working_times']} working times, "
                   f"{cleanup_summary['project_times']} project times deleted. "
                   f"{cleanup_summary['errors']} errors encountered.")

    def _track_working_time(self, working_time_id):
        """Track a working time for cleanup, avoiding duplicates."""
        if working_time_id not in self.test_working_times:
            self.test_working_times.append(working_time_id)
            logger.debug(f"Tracking working time for cleanup: {working_time_id}")

    def _track_project_time(self, project_time_id):
        """Track a project time for cleanup, avoiding duplicates."""
        if project_time_id not in self.test_project_times:
            self.test_project_times.append(project_time_id)
            logger.debug(f"Tracking project time for cleanup: {project_time_id}")

    def tearDown(self):
        """Clean up after each individual test method if needed."""
        # This allows individual test cleanup if a test fails midway
        pass

    def test_01_login_success(self):
        """Test that login works correctly with valid credentials."""
        # This login is already done in setUpClass, just verify the response
        self.assertIsNotNone(self.login_response)
        self.assertIn("token", self.login_response)
        self.assertIn("user", self.login_response)

    def test_02_login_failure(self):
        """Test that login fails with invalid credentials."""
        # Create a new API client for this test to avoid affecting other tests
        bad_api = TimrApi(company_id=COMPANY_ID)

        # Try login with invalid credentials
        with self.assertRaises(TimrApiError):
            bad_api.login("wrong_username", "wrong_password")

    def test_03_create_working_time(self):
        """Test creating a working time."""
        # Create test data
        start = f"{self.test_date_str}T09:00:00+00:00"
        end = f"{self.test_date_str}T17:00:00+00:00"
        pause_duration = 30

        # Create working time
        wt = self.api.create_working_time(start=start,
                                          end=end,
                                          pause_duration=pause_duration)

        # Track for cleanup
        self._track_working_time(wt["id"])

        # Verify working time was created correctly
        self.assertIn("id", wt)
        self.assertIn("start", wt)
        self.assertIn("end", wt)
        self.assertEqual(wt["break_time_total_minutes"], pause_duration)

    def test_04_get_working_times(self):
        """Test getting working times for a date."""
        # Create a working time for the test date if one doesn't exist
        if not self.test_working_times:
            self.test_03_create_working_time()

        # Get working times for the test date
        working_times = self.api.get_working_times(start_date=self.test_date,
                                                   end_date=self.test_date,
                                                   user_id=self.user_id)

        # Verify we got at least one working time
        self.assertGreaterEqual(len(working_times), 1)

        # Verify the working time we created is in the results
        wt_ids = [wt.get("id") for wt in working_times]
        for test_wt_id in self.test_working_times:
            self.assertIn(test_wt_id, wt_ids)

    def test_05_update_working_time(self):
        """Test updating a working time."""
        # Create a working time for testing
        start = f"{self.test_date_str}T09:00:00+00:00"
        end = f"{self.test_date_str}T17:00:00+00:00"
        pause_duration = 30

        wt = self.api.create_working_time(start=start,
                                          end=end,
                                          pause_duration=pause_duration)
        self._track_working_time(wt["id"])

        # Prepare update data
        new_end = f"{self.test_date_str}T18:00:00+00:00"
        new_pause = 45

        logger.info(f"TEST_05: Original working time: {wt}")
        logger.info(
            f"TEST_05: Updating with new_end={new_end}, new_pause={new_pause}")

        # Update working time
        updated_wt = self.api.update_working_time(working_time_id=wt["id"],
                                                  end=new_end,
                                                  pause_duration=new_pause)

        logger.info(f"TEST_05: Updated working time: {updated_wt}")

        # Verify working time was updated correctly
        self.assertEqual(updated_wt["id"], wt["id"])

        # Verify the pause duration was updated
        self.assertEqual(updated_wt["break_time_total_minutes"], new_pause)

        # The API calculates the end time differently when breaks are included
        # So we verify the total working duration instead of the exact end time
        expected_working_minutes = 9 * 60 - new_pause  # 9 hours minus break
        actual_duration = updated_wt.get("duration", {}).get("minutes", 0)

        # Allow some flexibility in the duration calculation
        self.assertAlmostEqual(
            actual_duration,
            expected_working_minutes,
            delta=5,
            msg=
            f"Expected working duration around {expected_working_minutes} minutes, got {actual_duration}"
        )

    def test_06_get_tasks(self):
        """Test getting tasks."""
        # Get tasks (limit to first 10)
        tasks = self.api.get_tasks()[:10]

        # Verify we got at least one task
        self.assertGreaterEqual(len(tasks), 1)

        # Verify task structure
        for task in tasks:
            self.assertIn("id", task)
            self.assertIn("name", task)

    def test_07_search_tasks(self):
        """Test searching for tasks."""
        # Get tasks to find one to search for
        tasks = self.api.get_tasks()[:10]
        self.assertGreaterEqual(len(tasks), 1)

        task = tasks[0]  # Use first task for search test

        # Extract a search term from the task name (first 3 characters)
        search_term = task["name"][:3]

        # Search for tasks
        search_results = self.api.get_tasks(search=search_term)

        # Verify we got at least one result
        self.assertGreaterEqual(len(search_results), 1)

        # Verify the task we searched for is in the results
        task_ids = [t.get("id") for t in search_results]
        self.assertIn(task["id"], task_ids)

    def test_08_create_project_time(self):
        """Test creating a project time."""
        # Create a working time for testing
        start = f"{self.test_date_str}T09:00:00+00:00"
        end = f"{self.test_date_str}T17:00:00+00:00"
        pause_duration = 30

        wt = self.api.create_working_time(start=start,
                                          end=end,
                                          pause_duration=pause_duration)
        self._track_working_time(wt["id"])

        # Get a task for testing
        tasks = self.api.get_tasks()[:10]
        self.assertGreaterEqual(len(tasks), 1)

        # Find a bookable task or use the first one
        task = None
        for t in tasks:
            if t.get("bookable", False):
                task = t
                break
        if not task:
            task = tasks[0]

        # Create project time data
        start = wt["start"]
        # Make the project time 1 hour long
        start_dt = datetime.datetime.fromisoformat(start.replace(
            'Z', '+00:00'))
        end_dt = start_dt + datetime.timedelta(hours=1)
        end = end_dt.isoformat()

        # Create project time
        pt = self.api.create_project_time(task_id=task["id"],
                                          start=start,
                                          end=end)

        # Track for cleanup
        self._track_project_time(pt["id"])

        # Verify project time was created correctly
        self.assertIn("id", pt)
        self.assertEqual(pt["task"]["id"], task["id"])

        # Check start time, handling both Z and +00:00 formats
        self.assertTrue(
            pt["start"] == start
            or pt["start"] == start.replace('+00:00', 'Z')
            or pt["start"].replace('Z', '+00:00') == start,
            f"Expected {start} or alternative format, got {pt['start']}")

        # Check end time, handling both Z and +00:00 formats
        self.assertTrue(
            pt["end"] == end or pt["end"] == end.replace('+00:00', 'Z')
            or pt["end"].replace('Z', '+00:00') == end,
            f"Expected {end} or alternative format, got {pt['end']}")

    def test_09_get_project_times(self):
        """Test getting project times."""
        # Create a project time for testing if we don't have one
        if not self.test_project_times:
            self.test_08_create_project_time()

        # Get project times for the test date
        project_times = self.api.get_project_times(start_date=self.test_date,
                                                   end_date=self.test_date,
                                                   user_id=self.user_id)

        # Verify we got at least one project time
        self.assertGreaterEqual(len(project_times), 1)

        # Verify the project time we created is in the results
        pt_ids = [pt.get("id") for pt in project_times]
        for test_pt_id in self.test_project_times:
            self.assertIn(test_pt_id, pt_ids)

    def test_10_update_project_time(self):
        """Test updating a project time."""
        # Create a project time for testing if we don't have one
        if not self.test_project_times:
            self.test_08_create_project_time()
            pt = self.test_project_time
        else:
            pt_id = self.test_project_times[0]
            pt = self.api.get_project_time(pt_id)

        # Prepare update data - extend by 30 minutes
        end_dt = datetime.datetime.fromisoformat(pt["end"].replace(
            'Z', '+00:00'))
        new_end_dt = end_dt + datetime.timedelta(minutes=30)
        new_end = new_end_dt.isoformat()

        # Update project time
        updated_pt = self.api.update_project_time(project_time_id=pt["id"],
                                                  end=new_end)

        # Verify project time was updated correctly
        self.assertEqual(updated_pt["id"], pt["id"])

        # Check end time with handling for both Z and +00:00 formats
        self.assertTrue(
            updated_pt["end"] == new_end
            or updated_pt["end"] == new_end.replace('+00:00', 'Z')
            or updated_pt["end"].replace('Z', '+00:00') == new_end,
            f"Expected {new_end} or alternative format, got {updated_pt['end']}"
        )

    def test_11_delete_project_time(self):
        """Test deleting a project time."""
        # Create a project time for testing if we don't have one
        if not self.test_project_times:
            self.test_08_create_project_time()
            pt_id = self.test_project_time["id"]
        else:
            pt_id = self.test_project_times[0]

        # Delete project time
        response = self.api.delete_project_time(pt_id)

        # Remove from test data to clean up
        self.test_project_times.remove(pt_id)

        # Verify deletion
        with self.assertRaises(TimrApiError):
            self.api.get_project_time(pt_id)

    def test_12_delete_working_time(self):
        """Test deleting a working time."""
        # Create a working time for testing if we don't have one
        if not self.test_working_times:
            self.test_03_create_working_time()
            wt_id = self.test_working_time["id"]
        else:
            wt_id = self.test_working_times[0]

        # Delete working time
        response = self.api.delete_working_time(wt_id)

        # Remove from test data to clean up
        self.test_working_times.remove(wt_id)

        # Verify deletion
        with self.assertRaises(TimrApiError):
            self.api.get_working_time(wt_id)

    def test_13_overlapping_project_times(self):
        """Test how the API handles overlapping project times.

        This is an important test to understand the real API behavior regarding overlapping project times.
        """
        # Get a working time for testing
        if not self.test_working_times:
            self.test_03_create_working_time()
            wt = self.test_working_time
        else:
            wt_id = self.test_working_times[0]
            wt = self.api.get_working_time(wt_id)

        # Get a task for testing
        if not hasattr(self.__class__,
                       'bookable_task') or not self.bookable_task:
            self.test_06_get_tasks()

        task = self.bookable_task

        # Create first project time
        start1 = wt["start"]
        start1_dt = datetime.datetime.fromisoformat(
            start1.replace('Z', '+00:00'))
        end1_dt = start1_dt + datetime.timedelta(hours=2)  # 2 hour duration
        end1 = end1_dt.isoformat()

        pt1 = self.api.create_project_time(task_id=task["id"],
                                           start=start1,
                                           end=end1)
        self.test_project_times.append(pt1["id"])

        # Create second project time that overlaps with the first
        start2_dt = start1_dt + datetime.timedelta(
            hours=1)  # Start in the middle of the first project time
        end2_dt = start2_dt + datetime.timedelta(hours=2)  # 2 hour duration
        start2 = start2_dt.isoformat()
        end2 = end2_dt.isoformat()

        # Create the overlapping project time and see how the API responds
        try:
            pt2 = self.api.create_project_time(task_id=task["id"],
                                               start=start2,
                                               end=end2)
            self.test_project_times.append(pt2["id"])

            # If we get here, the API allowed overlapping project times!
            logger.info("API allows overlapping project times")

            # Verify both project times exist
            pt1_check = self.api.get_project_time(pt1["id"])
            pt2_check = self.api.get_project_time(pt2["id"])

            self.assertEqual(pt1_check["id"], pt1["id"])
            self.assertEqual(pt2_check["id"], pt2["id"])

        except TimrApiError as e:
            # If we get here, the API rejected the overlapping project time
            logger.info(f"API rejected overlapping project time: {e}")

            # The assumption in our implementation is that the API allows overlapping times
            # but we want to protect users from creating them. If the API actually rejects
            # overlapping times, we might need to reconsider our approach.
            self.fail(
                "Unexpected behavior: Timr API rejected overlapping project times. "
                "Our implementation assumes the API allows overlapping times.")

    def test_14_project_times_outside_working_time(self):
        """Test how the API handles project times outside working time bounds.

        This is an important test to understand the real API behavior regarding project times
        that start before or end after their working time.
        """
        # Get a working time for testing
        if not self.test_working_times:
            self.test_03_create_working_time()
            wt = self.test_working_time
        else:
            wt_id = self.test_working_times[0]
            wt = self.api.get_working_time(wt_id)

        # Get a task for testing
        if not hasattr(self.__class__,
                       'bookable_task') or not self.bookable_task:
            self.test_06_get_tasks()

        task = self.bookable_task

        # Parse working time start/end
        wt_start_dt = datetime.datetime.fromisoformat(wt["start"].replace(
            'Z', '+00:00'))
        wt_end_dt = datetime.datetime.fromisoformat(wt["end"].replace(
            'Z', '+00:00'))

        # Create project time that starts before working time
        pt_start_dt = wt_start_dt - datetime.timedelta(
            hours=1)  # 1 hour before working time
        pt_end_dt = wt_start_dt + datetime.timedelta(
            hours=1)  # 1 hour into working time
        pt_start = pt_start_dt.isoformat()
        pt_end = pt_end_dt.isoformat()

        # Try to create the out-of-bounds project time
        try:
            early_pt = self.api.create_project_time(task_id=task["id"],
                                                    start=pt_start,
                                                    end=pt_end)
            self.test_project_times.append(early_pt["id"])

            # If we get here, the API allowed the early project time!
            logger.info(
                "API allows project times starting before working time")

            # Verify the project time was created as requested, handling timezone format differences
            self.assertTrue(
                early_pt["start"] == pt_start
                or early_pt["start"] == pt_start.replace('+00:00', 'Z')
                or early_pt["start"].replace('Z', '+00:00') == pt_start,
                f"Expected {pt_start} or alternative format, got {early_pt['start']}"
            )

            self.assertTrue(
                early_pt["end"] == pt_end
                or early_pt["end"] == pt_end.replace('+00:00', 'Z')
                or early_pt["end"].replace('Z', '+00:00') == pt_end,
                f"Expected {pt_end} or alternative format, got {early_pt['end']}"
            )

        except TimrApiError as e:
            # If we get here, the API rejected the out-of-bounds project time
            logger.info(
                f"API rejected project time starting before working time: {e}")

            # This is important information for our implementation
            pass

        # Create project time that ends after working time
        pt_start_dt = wt_end_dt - datetime.timedelta(
            hours=1)  # 1 hour before working time end
        pt_end_dt = wt_end_dt + datetime.timedelta(
            hours=1)  # 1 hour after working time
        pt_start = pt_start_dt.isoformat()
        pt_end = pt_end_dt.isoformat()

        # Try to create the out-of-bounds project time
        try:
            late_pt = self.api.create_project_time(task_id=task["id"],
                                                   start=pt_start,
                                                   end=pt_end)
            self.test_project_times.append(late_pt["id"])

            # If we get here, the API allowed the late project time!
            logger.info("API allows project times ending after working time")

            # Verify the project time was created as requested, handling timezone format differences
            self.assertTrue(
                late_pt["start"] == pt_start
                or late_pt["start"] == pt_start.replace('+00:00', 'Z')
                or late_pt["start"].replace('Z', '+00:00') == pt_start,
                f"Expected {pt_start} or alternative format, got {late_pt['start']}"
            )

            self.assertTrue(
                late_pt["end"] == pt_end
                or late_pt["end"] == pt_end.replace('+00:00', 'Z')
                or late_pt["end"].replace('Z', '+00:00') == pt_end,
                f"Expected {pt_end} or alternative format, got {late_pt['end']}"
            )

        except TimrApiError as e:
            # If we get here, the API rejected the out-of-bounds project time
            logger.info(
                f"API rejected project time ending after working time: {e}")

            # This is important information for our implementation
            pass

    def test_15_pagination_functionality(self):
        """Test centralized pagination implementation with cursor pagination.
        
        This test validates that the _request_paginated method correctly handles
        Timr's cursor pagination and retrieves unique data on each page.
        """
        logger.info("Testing centralized pagination functionality")

        # Define test constants to avoid magic numbers
        MAX_API_LIMIT = 500  # Maximum limit per Timr API specification
        SMALL_TEST_LIMIT = 50  # Smaller limit for multi-page testing
        MIN_TASKS_FOR_MULTIPAGE_TEST = SMALL_TEST_LIMIT * 2  # Need at least 2 pages worth

        # Test basic pagination with maximum API limit
        all_tasks = self.api._request_paginated("/tasks",
                                                params={},
                                                limit=MAX_API_LIMIT)

        self.assertIsInstance(all_tasks, list)
        self.assertGreater(len(all_tasks), 0,
                           "Should retrieve at least some tasks")

        logger.info(
            f"Retrieved {len(all_tasks)} total tasks via pagination with limit={MAX_API_LIMIT}"
        )

        # Verify no duplicate tasks in the full result set
        all_task_ids = {task["id"] for task in all_tasks}
        self.assertEqual(
            len(all_task_ids), len(all_tasks),
            f"Found {len(all_tasks) - len(all_task_ids)} duplicate tasks in paginated results"
        )
        logger.info(f"✓ No duplicates found in {len(all_tasks)} tasks")

        # Test pagination with search
        search_results = self.api.get_tasks(search="test", active_only=False)
        self.assertIsInstance(search_results, list)
        logger.info(
            f"Search pagination test: found {len(search_results)} tasks with 'test' in name"
        )

        # Test other paginated endpoints
        working_times = self.api.get_working_times()
        self.assertIsInstance(working_times, list)
        logger.info(f"Working times pagination: {len(working_times)} items")

        working_time_types = self.api.get_working_time_types()
        self.assertIsInstance(working_time_types, list)
        self.assertGreater(len(working_time_types), 0,
                           "Should have at least some working time types")
        logger.info(
            f"Working time types pagination: {len(working_time_types)} items")

        # Test edge case: empty parameters
        project_times = self.api.get_project_times()
        self.assertIsInstance(project_times, list)
        logger.info(f"Project times pagination: {len(project_times)} items")

    def test_16_pagination_data_integrity(self):
        """Test that pagination maintains data integrity and consistency."""
        logger.info("Testing pagination data integrity")

        # Get all tasks with large limit (should be single page for most cases)
        single_page_tasks = self.api._request_paginated("/tasks",
                                                        params={},
                                                        limit=500)

        # Get all tasks with small limit (should require multiple pages)
        multi_page_tasks = self.api._request_paginated("/tasks",
                                                       params={},
                                                       limit=10)

        # Should get the same total number of tasks
        self.assertEqual(
            len(single_page_tasks), len(multi_page_tasks),
            f"Different pagination limits should return same total count: "
            f"{len(single_page_tasks)} vs {len(multi_page_tasks)}")

        # Convert to sets of IDs for comparison
        single_page_ids = {task["id"] for task in single_page_tasks}
        multi_page_ids = {task["id"] for task in multi_page_tasks}

        # Should contain exactly the same tasks
        self.assertEqual(
            single_page_ids, multi_page_ids,
            "Different pagination approaches should return identical task sets"
        )

        logger.info(
            f"✓ Data integrity verified: {len(single_page_tasks)} tasks consistent across pagination methods"
        )

        # Test that we're not getting duplicate tasks within a single pagination call
        all_ids = [task["id"] for task in multi_page_tasks]
        unique_ids = set(all_ids)
        self.assertEqual(
            len(all_ids), len(unique_ids),
            f"Found {len(all_ids) - len(unique_ids)} duplicate tasks in paginated results"
        )

        logger.info("✓ No duplicate tasks found in paginated results")

    def test_17_overlapping_working_times(self):
        """Test how the API handles overlapping working times.

        This is an important test to understand the real API behavior regarding overlapping working times.
        """
        # Create first working time
        start1 = f"{self.test_date_str}T10:00:00+00:00"
        end1 = f"{self.test_date_str}T14:00:00+00:00"

        wt1 = self.api.create_working_time(start=start1, end=end1)
        self.test_working_times.append(wt1["id"])

        # Create second working time that overlaps with the first
        start2 = f"{self.test_date_str}T12:00:00+00:00"  # Start in the middle of the first working time
        end2 = f"{self.test_date_str}T16:00:00+00:00"  # End after the first working time

        # Try to create the overlapping working time
        try:
            wt2 = self.api.create_working_time(start=start2, end=end2)
            self.test_working_times.append(wt2["id"])

            # If we get here, the API allowed overlapping working times!
            logger.info("API allows overlapping working times")

            # Verify both working times exist
            wt1_check = self.api.get_working_time(wt1["id"])
            wt2_check = self.api.get_working_time(wt2["id"])

            self.assertEqual(wt1_check["id"], wt1["id"])
            self.assertEqual(wt2_check["id"], wt2["id"])

        except TimrApiError as e:
            # If we get here, the API rejected the overlapping working time
            logger.info(f"API rejected overlapping working time: {e}")

            # This information validates our approach of preventing overlapping working times
            pass


if __name__ == '__main__':
    unittest.main()

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

        # Test date (yesterday to avoid API restrictions)
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

        # Test data tracking for cleanup - use sets to avoid duplicates
        cls.created_working_times = set()
        cls.created_project_times = set()
        
        # Note: No automatic cleanup of potentially leftover entries to protect user data
        # Manual cleanup should be performed only when specifically needed

    @classmethod
    def tearDownClass(cls):
        """Clean up all test data created during the tests."""
        if not hasattr(cls, 'api') or not cls.api.token:
            return

        cleanup_summary = {"working_times": 0, "project_times": 0, "errors": 0}

        # Delete all test project times first (before working times to avoid FK constraints)
        for pt_id in cls.created_project_times.copy():
            try:
                cls.api.delete_project_time(pt_id)
                logger.info(f"Deleted test project time {pt_id}")
                cls.created_project_times.discard(pt_id)
                cleanup_summary["project_times"] += 1
            except TimrApiError as e:
                logger.warning(f"Could not delete test project time {pt_id}: {e}")
                cleanup_summary["errors"] += 1

        # Delete all test working times
        for wt_id in cls.created_working_times.copy():
            try:
                cls.api.delete_working_time(wt_id)
                logger.info(f"Deleted test working time {wt_id}")
                cls.created_working_times.discard(wt_id)
                cleanup_summary["working_times"] += 1
            except TimrApiError as e:
                logger.warning(f"Could not delete test working time {wt_id}: {e}")
                cleanup_summary["errors"] += 1

        logger.info(f"Cleanup complete: {cleanup_summary['working_times']} working times, "
                   f"{cleanup_summary['project_times']} project times deleted. "
                   f"{cleanup_summary['errors']} errors encountered.")

    def _track_working_time(self, working_time_id):
        """Track a working time for cleanup."""
        self.created_working_times.add(working_time_id)
        logger.debug(f"Tracking working time for cleanup: {working_time_id}")

    def _track_project_time(self, project_time_id):
        """Track a project time for cleanup."""
        self.created_project_times.add(project_time_id)
        logger.debug(f"Tracking project time for cleanup: {project_time_id}")

    def _immediate_cleanup(self):
        """Perform immediate cleanup of all tracked data."""
        cleanup_summary = {"working_times": 0, "project_times": 0, "errors": 0}
        
        # Delete project times first to avoid FK constraints
        for pt_id in list(self.created_project_times):
            try:
                self.api.delete_project_time(pt_id)
                self.created_project_times.discard(pt_id)
                cleanup_summary["project_times"] += 1
                logger.debug(f"Immediate cleanup deleted project time {pt_id}")
            except TimrApiError as e:
                cleanup_summary["errors"] += 1
                logger.warning(f"Immediate cleanup failed for project time {pt_id}: {e}")
        
        # Delete working times
        for wt_id in list(self.created_working_times):
            try:
                self.api.delete_working_time(wt_id)
                self.created_working_times.discard(wt_id)
                cleanup_summary["working_times"] += 1
                logger.debug(f"Immediate cleanup deleted working time {wt_id}")
            except TimrApiError as e:
                cleanup_summary["errors"] += 1
                logger.warning(f"Immediate cleanup failed for working time {wt_id}: {e}")
        
        if cleanup_summary["working_times"] > 0 or cleanup_summary["project_times"] > 0:
            logger.info(f"Immediate cleanup: {cleanup_summary['working_times']} working times, "
                       f"{cleanup_summary['project_times']} project times deleted. "
                       f"{cleanup_summary['errors']} errors encountered.")

    def _get_or_create_working_time(self):
        """Get an existing test working time or create a new one."""
        if self.created_working_times:
            # Use existing working time
            wt_id = next(iter(self.created_working_times))
            return self.api.get_working_time(wt_id)
        else:
            # Create new working time
            start = f"{self.test_date_str}T09:00:00+00:00"
            end = f"{self.test_date_str}T17:00:00+00:00"
            pause_duration = 30
            
            wt = self.api.create_working_time(start=start, end=end, pause_duration=pause_duration)
            self._track_working_time(wt["id"])
            return wt

    def _get_bookable_task(self):
        """Get a bookable task for testing."""
        tasks = self.api.get_tasks()[:10]
        self.assertGreaterEqual(len(tasks), 1)
        
        # Find a bookable task or use the first one
        for task in tasks:
            if task.get("bookable", False):
                return task
        return tasks[0]

    def test_01_login_success(self):
        """Test that login works correctly with valid credentials."""
        # This login is already done in setUpClass, just verify the response
        self.assertIsNotNone(self.login_response)
        self.assertIn("token", self.login_response)
        self.assertIsNotNone(self.user_id)
        logger.info(f"Login successful, user ID: {self.user_id}")

    def test_02_login_failure(self):
        """Test that login fails with invalid credentials."""
        # Create a new API instance for testing bad credentials
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
        wt = self.api.create_working_time(start=start, end=end, pause_duration=pause_duration)

        # Track for cleanup
        self._track_working_time(wt["id"])

        # Verify working time was created correctly
        self.assertIn("id", wt)
        self.assertIn("start", wt)
        self.assertIn("end", wt)
        self.assertEqual(wt["break_time_total_minutes"], pause_duration)

        logger.info(f"Created working time: {wt['id']}")

    def test_04_get_working_times(self):
        """Test getting working times for a date."""
        # Ensure we have a working time
        self._get_or_create_working_time()

        # Get working times for the test date
        working_times = self.api.get_working_times(start_date=self.test_date,
                                                  end_date=self.test_date,
                                                  user_id=self.user_id)

        # Verify we got at least one working time
        self.assertGreaterEqual(len(working_times), 1)

        # Verify at least one of our test working times is in the results
        wt_ids = [wt.get("id") for wt in working_times]
        test_wt_found = any(wt_id in wt_ids for wt_id in self.created_working_times)
        self.assertTrue(test_wt_found, "At least one test working time should be found")

    def test_05_update_working_time(self):
        """Test updating a working time."""
        # Create a working time for testing
        start = f"{self.test_date_str}T09:00:00+00:00"
        end = f"{self.test_date_str}T17:00:00+00:00"
        pause_duration = 30

        wt = self.api.create_working_time(start=start, end=end, pause_duration=pause_duration)
        self._track_working_time(wt["id"])

        # Prepare update data
        new_end = f"{self.test_date_str}T18:00:00+00:00"
        new_pause = 45

        logger.info(f"TEST_05: Original working time: {wt}")
        logger.info(f"TEST_05: Updating with new_end={new_end}, new_pause={new_pause}")

        # Update working time
        updated_wt = self.api.update_working_time(working_time_id=wt["id"],
                                                 end=new_end,
                                                 pause_duration=new_pause)

        logger.info(f"TEST_05: Updated working time: {updated_wt}")

        # Verify working time was updated correctly
        self.assertEqual(updated_wt["id"], wt["id"])
        self.assertEqual(updated_wt["break_time_total_minutes"], new_pause)

    def test_06_create_project_time(self):
        """Test creating a project time."""
        # Get or create a working time for testing
        wt = self._get_or_create_working_time()

        # Get a task for testing
        task = self._get_bookable_task()

        # Create project time data
        start = wt["start"]
        end_dt = datetime.datetime.fromisoformat(start.replace('Z', '+00:00')) + datetime.timedelta(hours=1)
        end = end_dt.isoformat()

        # Create project time
        pt = self.api.create_project_time(task_id=task["id"],
                                         start=start,
                                         end=end)

        # Track for cleanup
        self._track_project_time(pt["id"])

        # Verify project time was created correctly
        self.assertIn("id", pt)
        self.assertIn("start", pt)
        self.assertIn("end", pt)
        self.assertEqual(pt["task"]["id"], task["id"])

        logger.info(f"Created project time: {pt['id']}")

    def test_07_get_tasks(self):
        """Test getting tasks."""
        # Get tasks (limit to first 10)
        tasks = self.api.get_tasks()[:10]

        # Verify we got at least one task
        self.assertGreaterEqual(len(tasks), 1)

        # Verify task structure
        for task in tasks:
            self.assertIn("id", task)
            self.assertIn("name", task)

    def test_08_search_tasks(self):
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

    def test_09_get_project_times(self):
        """Test getting project times."""
        # Create a project time for testing if we don't have one
        if not self.created_project_times:
            self.test_06_create_project_time()

        # Get project times for the test date
        project_times = self.api.get_project_times(start_date=self.test_date,
                                                   end_date=self.test_date,
                                                   user_id=self.user_id)

        # Verify we got at least one project time
        self.assertGreaterEqual(len(project_times), 1)

        # Verify at least one of our test project times is in the results
        pt_ids = [pt.get("id") for pt in project_times]
        test_pt_found = any(pt_id in pt_ids for pt_id in self.created_project_times)
        self.assertTrue(test_pt_found, "At least one test project time should be found")

    def test_10_update_project_time(self):
        """Test updating a project time."""
        # Create a project time for testing if we don't have one
        if not self.created_project_times:
            self.test_06_create_project_time()

        pt_id = next(iter(self.created_project_times))
        pt = self.api.get_project_time(pt_id)

        # Prepare update data - extend by 30 minutes
        end_dt = datetime.datetime.fromisoformat(pt["end"].replace('Z', '+00:00'))
        new_end_dt = end_dt + datetime.timedelta(minutes=30)
        new_end = new_end_dt.isoformat()

        # Update project time
        updated_pt = self.api.update_project_time(project_time_id=pt["id"],
                                                  end=new_end)

        # Verify project time was updated correctly
        self.assertEqual(updated_pt["id"], pt["id"])
        # Note: end time comparison is tricky due to timezone handling

    def test_11_delete_project_time(self):
        """Test deleting a project time."""
        # Create a project time for testing
        wt = self._get_or_create_working_time()
        task = self._get_bookable_task()

        start = wt["start"]
        end_dt = datetime.datetime.fromisoformat(start.replace('Z', '+00:00')) + datetime.timedelta(minutes=30)
        end = end_dt.isoformat()

        pt = self.api.create_project_time(task_id=task["id"], start=start, end=end)
        self._track_project_time(pt["id"])

        # Delete project time
        response = self.api.delete_project_time(pt["id"])

        # Remove from test data since we deleted it
        self.created_project_times.discard(pt["id"])

        # Verify deletion
        with self.assertRaises(TimrApiError):
            self.api.get_project_time(pt["id"])

    def test_12_delete_working_time(self):
        """Test deleting a working time."""
        # Create a working time specifically for deletion testing
        start = f"{self.test_date_str}T10:00:00+00:00"
        end = f"{self.test_date_str}T16:00:00+00:00"
        pause_duration = 30

        wt = self.api.create_working_time(start=start, end=end, pause_duration=pause_duration)
        self._track_working_time(wt["id"])

        # Delete working time
        response = self.api.delete_working_time(wt["id"])

        # Remove from test data since we deleted it
        self.created_working_times.discard(wt["id"])

        # Verify deletion
        with self.assertRaises(TimrApiError):
            self.api.get_working_time(wt["id"])

    def test_13_overlapping_project_times(self):
        """Test how the API handles overlapping project times.

        This is an important test to understand the real API behavior regarding overlapping project times.
        """
        # Get a working time for testing
        wt = self._get_or_create_working_time()

        # Get a task for testing
        task = self._get_bookable_task()

        # Create first project time
        start1 = wt["start"]
        end1_dt = datetime.datetime.fromisoformat(start1.replace('Z', '+00:00')) + datetime.timedelta(hours=2)
        end1 = end1_dt.isoformat()

        pt1 = self.api.create_project_time(task_id=task["id"], start=start1, end=end1)
        self._track_project_time(pt1["id"])

        # Create second project time that overlaps with the first
        start2_dt = datetime.datetime.fromisoformat(start1.replace('Z', '+00:00')) + datetime.timedelta(hours=1)
        start2 = start2_dt.isoformat()
        end2_dt = start2_dt + datetime.timedelta(hours=2)
        end2 = end2_dt.isoformat()

        # Try to create the overlapping project time
        try:
            pt2 = self.api.create_project_time(task_id=task["id"], start=start2, end=end2)
            self._track_project_time(pt2["id"])

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
            # This is acceptable behavior - just verify the first project time still exists
            pt1_check = self.api.get_project_time(pt1["id"])
            self.assertEqual(pt1_check["id"], pt1["id"])
        
        # Immediate cleanup to prevent accumulation during timeout interruptions
        self._immediate_cleanup()

    def test_14_project_times_outside_working_time(self):
        """Test how the API handles project times outside working time bounds.

        This is an important test to understand the real API behavior regarding project times
        that start before or end after their working time.
        """
        # Get a working time for testing
        wt = self._get_or_create_working_time()

        # Get a task for testing
        task = self._get_bookable_task()

        # Try to create a project time that starts before the working time
        wt_start = datetime.datetime.fromisoformat(wt["start"].replace('Z', '+00:00'))
        early_start = (wt_start - datetime.timedelta(hours=1)).isoformat()
        early_end = wt_start.isoformat()

        try:
            early_pt = self.api.create_project_time(task_id=task["id"], start=early_start, end=early_end)
            self._track_project_time(early_pt["id"])
            logger.info("API allows project times starting before working time")
        except TimrApiError as e:
            logger.info(f"API rejected project time starting before working time: {e}")

        # Try to create a project time that ends after the working time
        wt_end = datetime.datetime.fromisoformat(wt["end"].replace('Z', '+00:00'))
        late_start = wt_end.isoformat()
        late_end = (wt_end + datetime.timedelta(hours=1)).isoformat()

        try:
            late_pt = self.api.create_project_time(task_id=task["id"], start=late_start, end=late_end)
            self._track_project_time(late_pt["id"])
            logger.info("API allows project times ending after working time")
        except TimrApiError as e:
            logger.info(f"API rejected project time ending after working time: {e}")
        
        # Immediate cleanup to prevent accumulation during timeout interruptions
        self._immediate_cleanup()

    def test_15_pagination_functionality(self):
        """Test centralized pagination implementation with cursor pagination.
        
        This test validates that the _request_paginated method correctly handles
        Timr's cursor pagination and retrieves unique data on each page.
        """
        # Test pagination with tasks (usually has many results)
        all_tasks = self.api.get_tasks()
        
        # Verify we got some tasks
        self.assertGreater(len(all_tasks), 0, "Should retrieve at least one task")
        
        # Test that pagination is working by checking if we have unique IDs
        task_ids = [task["id"] for task in all_tasks]
        unique_task_ids = set(task_ids)
        
        self.assertEqual(
            len(task_ids), 
            len(unique_task_ids), 
            "Pagination should not return duplicate task IDs"
        )
        
        logger.info(f"Pagination test: Retrieved {len(all_tasks)} unique tasks")

    def test_16_pagination_data_integrity(self):
        """Test that pagination maintains data integrity and consistency."""
        # Get working times with pagination
        working_times = self.api.get_working_times(
            start_date=self.test_date - datetime.timedelta(days=7),
            end_date=self.test_date,
            user_id=self.user_id
        )
        
        # Verify data integrity
        for wt in working_times:
            self.assertIn("id", wt, "Working time should have an ID")
            self.assertIn("start", wt, "Working time should have a start time")
            self.assertIn("end", wt, "Working time should have an end time")
        
        logger.info(f"Data integrity test: {len(working_times)} working times validated")

    def test_17_overlapping_working_times(self):
        """Test how the API handles overlapping working times.

        This is an important test to understand the real API behavior regarding overlapping working times.
        """
        # Create first working time
        start1 = f"{self.test_date_str}T10:00:00+00:00"
        end1 = f"{self.test_date_str}T14:00:00+00:00"

        wt1 = self.api.create_working_time(start=start1, end=end1)
        self._track_working_time(wt1["id"])

        # Create second working time that overlaps with the first
        start2 = f"{self.test_date_str}T12:00:00+00:00"  # Start in the middle of the first working time
        end2 = f"{self.test_date_str}T16:00:00+00:00"  # End after the first working time

        # Try to create the overlapping working time
        try:
            wt2 = self.api.create_working_time(start=start2, end=end2)
            self._track_working_time(wt2["id"])

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
            # This is acceptable behavior - just verify the first working time still exists
            wt1_check = self.api.get_working_time(wt1["id"])
            self.assertEqual(wt1_check["id"], wt1["id"])
        
        # Immediate cleanup to prevent accumulation during timeout interruptions
        self._immediate_cleanup()

if __name__ == '__main__':
    unittest.main()
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
        pt = self.api.create_project_time(working_time_id=wt["id"],
                                         task_id=task["id"],
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

if __name__ == '__main__':
    unittest.main()
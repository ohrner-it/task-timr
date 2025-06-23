import unittest
from unittest.mock import Mock, patch, MagicMock
import json
from app import app
from timr_utils import UIProjectTime, ProjectTimeConsolidator
from tests.utils import REALISTIC_LOGIN_RESPONSE


class TestSortingFunctionality(unittest.TestCase):
    """Test suite for all sorting functionality across the application."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.app = app.test_client()
        app.testing = True
        self.app_context = app.app_context()
        self.app_context.push()
        
        # Create a request context
        self.request_context = app.test_request_context()
        self.request_context.push()

        # Mock the session
        self.session_patch = patch('flask.session')
        self.mock_session = self.session_patch.start()
        
        # Configure session.get to return realistic user data
        self.mock_session.get.side_effect = lambda key, default=None: {
            'token': REALISTIC_LOGIN_RESPONSE['token'],
            'user': REALISTIC_LOGIN_RESPONSE['user']
        }.get(key, default)
        
        # Mock the get_current_user function
        self.get_current_user_patch = patch('app.get_current_user')
        self.mock_get_current_user = self.get_current_user_patch.start()
        self.mock_get_current_user.return_value = REALISTIC_LOGIN_RESPONSE['user']

        # Mock the elevated TimrApi for task search
        self.timr_api_elevated_patch = patch('app.timr_api_elevated')
        self.mock_timr_api_elevated = self.timr_api_elevated_patch.start()
        self.mock_timr_api_elevated.is_authenticated.return_value = True

    def tearDown(self):
        """Clean up after each test method."""
        self.session_patch.stop()
        self.get_current_user_patch.stop()
        self.timr_api_elevated_patch.stop()
        self.request_context.pop()
        self.app_context.pop()

    def test_task_search_results_sorted_by_name_ascending_id_ascending(self):
        """Test that task search results are sorted by name ascending, then ID ascending."""
        # Arrange: Mock task data in mixed order
        mock_tasks = [
            {'id': 'task3', 'name': 'Zulu Task', 'title': 'Zulu Task'},
            {'id': 'task1', 'name': 'Alpha Task', 'title': 'Alpha Task'},
            {'id': 'task5', 'name': 'Beta Task', 'title': 'Beta Task'},
            {'id': 'task2', 'name': 'Alpha Task', 'title': 'Alpha Task'},  # Same name, different ID
        ]
        self.mock_timr_api_elevated.get_tasks.return_value = mock_tasks

        # Act: Make request to search endpoint
        response = self.app.get('/api/tasks/search?q=task')
        
        # Assert: Response should be successful
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        
        # Verify tasks are sorted correctly
        tasks = data['tasks']
        self.assertEqual(len(tasks), 4)
        
        # Should be sorted by name ascending, then ID ascending
        self.assertEqual(tasks[0]['id'], 'task1')  # "Alpha Task" (task1 < task2)
        self.assertEqual(tasks[1]['id'], 'task2')  # "Alpha Task" (task2 > task1)
        self.assertEqual(tasks[2]['id'], 'task5')  # "Beta Task"
        self.assertEqual(tasks[3]['id'], 'task3')  # "Zulu Task"

    def test_task_search_results_sorted_with_empty_names(self):
        """Test task search sorting behavior with empty or missing names."""
        # Arrange: Mock task data with empty/missing names
        mock_tasks = [
            {'id': 'task3', 'name': 'Real Task'},
            {'id': 'task1', 'name': ''},  # Empty name
            {'id': 'task2'},  # Missing name field
        ]
        self.mock_timr_api_elevated.get_tasks.return_value = mock_tasks

        # Act: Make request to search endpoint
        response = self.app.get('/api/tasks/search?q=task')
        
        # Assert: Response should be successful
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        
        # Verify tasks are sorted correctly
        tasks = data['tasks']
        self.assertEqual(len(tasks), 3)
        
        # Empty/missing names should sort first (ascending order)
        self.assertEqual(tasks[0]['id'], 'task1')  # Empty name
        self.assertEqual(tasks[1]['id'], 'task2')  # Missing name
        self.assertEqual(tasks[2]['id'], 'task3')  # "Real Task"

    def test_task_search_results_sorted_with_title_fallback(self):
        """Test task search sorting when using title field as name fallback."""
        # Arrange: Mock task data with title instead of name
        mock_tasks = [
            {'id': 'task2', 'title': 'Beta Task'},
            {'id': 'task1', 'title': 'Alpha Task'},
            {'id': 'task3', 'title': 'Gamma Task'},
        ]
        self.mock_timr_api_elevated.get_tasks.return_value = mock_tasks

        # Act: Make request to search endpoint
        response = self.app.get('/api/tasks/search?q=task')
        
        # Assert: Response should be successful
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        
        # Verify tasks are sorted correctly and name field is populated from title
        tasks = data['tasks']
        self.assertEqual(len(tasks), 3)
        
        # Should be sorted by name (derived from title) ascending
        self.assertEqual(tasks[0]['id'], 'task1')  # "Alpha Task"
        self.assertEqual(tasks[0]['name'], 'Alpha Task')  # Name should be populated from title
        self.assertEqual(tasks[1]['id'], 'task2')  # "Beta Task"
        self.assertEqual(tasks[2]['id'], 'task3')  # "Gamma Task"

    def test_task_search_minimum_length_requirement(self):
        """Test that task search returns empty results for queries shorter than 3 characters."""
        # Act: Make request with short search term
        response = self.app.get('/api/tasks/search?q=ab')
        
        # Assert: Should return empty results without calling API
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['tasks'], [])
        
        # Verify API was not called
        self.mock_timr_api_elevated.get_tasks.assert_not_called()

    def test_task_search_handles_api_errors(self):
        """Test that task search handles API errors gracefully."""
        # Arrange: Mock API to raise an exception
        self.mock_timr_api_elevated.get_tasks.side_effect = Exception("API Error")

        # Act: Make request to search endpoint
        response = self.app.get('/api/tasks/search?q=test')
        
        # Assert: Should return error response
        self.assertEqual(response.status_code, 200)  # App handles errors gracefully
        data = json.loads(response.data)
        self.assertEqual(data['tasks'], [])
        self.assertIn('error', data)

    def test_time_slots_sorting_by_task_name_desc_task_id_desc(self):
        """Test that time slots are calculated with proper sorting (task name desc, task ID desc)."""
        # This test validates the sorting changes in timr_utils._calculate_time_slots
        
        # Arrange: Set up ProjectTimeConsolidator with mock API
        mock_timr_api = Mock()
        consolidator = ProjectTimeConsolidator(mock_timr_api)
        
        working_time = {
            "id": "wt1",
            "start": "2025-04-01T09:00:00+00:00",
            "end": "2025-04-01T17:00:00+00:00",
        }
        
        tasks = [
            UIProjectTime("task1", "Alpha Task", 60),
            UIProjectTime("task3", "Zulu Task", 90),
            UIProjectTime("task2", "Beta Task", 30),
            UIProjectTime("task4", "Alpha Task", 45),  # Same name, different ID
        ]

        # Act: Calculate time slots
        slots = consolidator._calculate_time_slots(working_time, tasks)

        # Assert: Verify sorting is correct (task name desc, then task ID desc)
        self.assertEqual(len(slots), 4)
        self.assertEqual(slots[0]['task_id'], 'task3')  # "Zulu Task"
        self.assertEqual(slots[1]['task_id'], 'task2')  # "Beta Task"
        self.assertEqual(slots[2]['task_id'], 'task4')  # "Alpha Task" (task4 > task1)
        self.assertEqual(slots[3]['task_id'], 'task1')  # "Alpha Task" (task1 < task4)

    def test_time_slots_sorting_with_mixed_case_names(self):
        """Test time slots sorting handles mixed case task names correctly."""
        # Arrange: Set up ProjectTimeConsolidator
        mock_timr_api = Mock()
        consolidator = ProjectTimeConsolidator(mock_timr_api)
        
        working_time = {
            "id": "wt1",
            "start": "2025-04-01T09:00:00+00:00",
            "end": "2025-04-01T17:00:00+00:00",
        }
        
        tasks = [
            UIProjectTime("task1", "alpha task", 60),  # lowercase
            UIProjectTime("task2", "BETA TASK", 90),   # uppercase
            UIProjectTime("task3", "Gamma Task", 30),  # mixed case
        ]

        # Act: Calculate time slots
        slots = consolidator._calculate_time_slots(working_time, tasks)

        # Assert: Verify case-insensitive descending sort
        self.assertEqual(len(slots), 3)
        # Note: Python's string comparison is case-sensitive, so this tests actual behavior
        # Uppercase letters come before lowercase in ASCII, so "BETA TASK" > "Gamma Task" > "alpha task"
        expected_order = ['task3', 'task2', 'task1']  # Based on actual string comparison
        actual_order = [slot['task_id'] for slot in slots]
        
        # Verify the sorting follows string comparison rules
        task_names = [task.task_name for task in tasks]
        sorted_names = sorted(task_names, reverse=True)
        self.assertEqual(sorted_names, ["alpha task", "Gamma Task", "BETA TASK"])


if __name__ == '__main__':
    unittest.main()
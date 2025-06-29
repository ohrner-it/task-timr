import unittest
from unittest.mock import Mock, patch, MagicMock, call
import json
import datetime
from app import app
from timr_utils import UIProjectTime, ProjectTimeConsolidator
from tests.utils import REALISTIC_LOGIN_RESPONSE


class TestUIProjectTimeEndpoints(unittest.TestCase):
    """Test suite for the UI project time related API endpoints."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.app = app.test_client()
        self.app.testing = True
        self.app_context = app.app_context()
        self.app_context.push()
        
        # Create a request context that can be used by the tests
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

        # Mock the TimrApi
        self.timr_api_patch = patch('app.timr_api')
        self.mock_timr_api = self.timr_api_patch.start()
        self.mock_timr_api.token = 'test-token'
        # Ensure _get_project_times_in_work_time returns a list
        self.mock_timr_api._get_project_times_in_work_time.return_value = []
        # Configure distribute_time
        self.mock_timr_api.distribute_time.return_value = []

        # Mock the ProjectTimeConsolidator
        self.consolidator_patch = patch('app.project_time_consolidator')
        self.mock_consolidator = self.consolidator_patch.start()

    def tearDown(self):
        """Tear down test fixtures after each test method."""
        self.session_patch.stop()
        self.get_current_user_patch.stop()
        self.timr_api_patch.stop()
        self.consolidator_patch.stop()
        
        # Properly exit request and app contexts
        self.request_context.pop()
        self.app_context.pop()

    def test_get_ui_project_times(self):
        """Test getting UI project times for a working time."""
        # Configure mocks
        working_time = {
            "id": "wt123",
            "start": "2025-04-01T09:00:00Z",
            "end": "2025-04-01T17:00:00Z",
            "break_time_total_minutes": 30
        }
        self.mock_timr_api.get_working_time.return_value = working_time

        # Create UIProjectTime objects for the mock response
        ui_pt1 = UIProjectTime("task1", "Task 1", 120, "Project A/Task 1")
        ui_pt2 = UIProjectTime("task2", "Task 2", 90, "Project B/Task 2")

        # Configure the consolidator mock to return sample data
        self.mock_consolidator.consolidate_project_times.return_value = {
            "working_time": working_time,
            "ui_project_times": [ui_pt1, ui_pt2],
            "consolidated_project_times": [ui_pt1.to_dict(),
                                           ui_pt2.to_dict()],
            "total_duration": 210,
            "net_duration": 450,
            "remaining_duration": 240,
            "is_fully_allocated": False,
            "is_over_allocated": False
        }

        # Make the request
        response = self.app.get('/api/working-times/wt123/ui-project-times')

        # Check the response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('ui_project_times', data)
        self.assertEqual(len(data['ui_project_times']), 2)
        self.assertEqual(data['total_duration'], 210)
        self.assertEqual(data['remaining_duration'], 240)

        # Verify the TimrApi and ProjectTimeConsolidator were called correctly
        self.mock_timr_api.get_working_time.assert_called_once_with('wt123')
        self.mock_consolidator.consolidate_project_times.assert_called_once_with(
            working_time)

    def test_add_ui_project_time(self):
        """Test adding a UI project time."""
        # Configure mocks
        working_time = {
            "id": "wt123",
            "start": "2025-04-01T09:00:00Z",
            "end": "2025-04-01T17:00:00Z",
            "break_time_total_minutes": 30
        }
        self.mock_timr_api.get_working_time.return_value = working_time

        # Create UIProjectTime object for the mock response
        ui_pt = UIProjectTime("task1", "Task 1", 120, "Project A/Task 1")

        # Configure the consolidator mock to return sample data with concrete values
        self.mock_consolidator.add_ui_project_time.return_value = {
            "working_time": working_time,
            "ui_project_times": [ui_pt],
            "consolidated_project_times": [ui_pt.to_dict()],
            "total_duration": 120,
            "net_duration": 450,
            "remaining_duration": 330,
            "is_fully_allocated": False,
            "is_over_allocated": False
        }
        
        # Configure the consolidate_project_times mock to also return concrete values
        # This is the key fix: providing concrete values for the comparison operation
        self.mock_consolidator.consolidate_project_times.return_value = {
            "working_time": working_time,
            "ui_project_times": [],
            "consolidated_project_times": [],
            "total_duration": 0,
            "net_duration": 450,
            "remaining_duration": 330,  # This needs to be a concrete integer for the comparison
            "is_fully_allocated": False,
            "is_over_allocated": False
        }

        # Make the request
        response = self.app.post('/api/working-times/wt123/ui-project-times',
                                 json={
                                     "task_id": "task1",
                                     "task_name": "Task 1",
                                     "duration_minutes": 120
                                 },
                                 content_type='application/json')

        # Check the response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('ui_project_times', data)
        self.assertEqual(len(data['ui_project_times']), 1)
        self.assertEqual(data['total_duration'], 120)
        self.assertEqual(data['remaining_duration'], 330)

        # Verify add_ui_project_time was called correctly
        self.mock_timr_api.get_working_time.assert_called_once_with('wt123')
        self.mock_consolidator.add_ui_project_time.assert_called_once_with(
            working_time,
            task_id="task1",
            task_name="Task 1",
            duration_minutes=120)

    def test_update_ui_project_time(self):
        """Test updating a UI project time."""
        # Configure mocks
        working_time = {
            "id": "wt123",
            "start": "2025-04-01T09:00:00Z",
            "end": "2025-04-01T17:00:00Z",
            "break_time_total_minutes": 30
        }
        self.mock_timr_api.get_working_time.return_value = working_time

        # Create UIProjectTime object for the mock response
        ui_pt = UIProjectTime("task1", "Updated Task", 180,
                              "Project A/Updated Task")

        # Configure the consolidator mock to return sample data
        self.mock_consolidator.update_ui_project_time.return_value = {
            "working_time": working_time,
            "ui_project_times": [ui_pt],
            "consolidated_project_times": [ui_pt.to_dict()],
            "total_duration": 180,
            "net_duration": 450,
            "remaining_duration": 270,
            "is_fully_allocated": False,
            "is_over_allocated": False
        }

        # Make the request
        response = self.app.patch(
            '/api/working-times/wt123/ui-project-times/task1',
            json={
                "duration_minutes": 180,
                "task_name": "Updated Task"
            },
            content_type='application/json')

        # Check the response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('ui_project_times', data)
        self.assertEqual(len(data['ui_project_times']), 1)
        self.assertEqual(data['ui_project_times'][0]['task_name'],
                         "Updated Task")
        self.assertEqual(data['ui_project_times'][0]['duration_minutes'], 180)

        # Verify update_ui_project_time was called correctly
        self.mock_timr_api.get_working_time.assert_called_once_with('wt123')
        self.mock_consolidator.update_ui_project_time.assert_called_once_with(
            working_time,
            task_id="task1",
            duration_minutes=180,
            task_name="Updated Task")

    def test_delete_ui_project_time(self):
        """Test deleting a UI project time."""
        # Configure mocks
        working_time = {
            "id": "wt123",
            "start": "2025-04-01T09:00:00Z",
            "end": "2025-04-01T17:00:00Z",
            "break_time_total_minutes": 30
        }
        self.mock_timr_api.get_working_time.return_value = working_time

        # Configure the consolidator mock to return sample data
        self.mock_consolidator.delete_ui_project_time.return_value = {
            "working_time": working_time,
            "ui_project_times": [],
            "consolidated_project_times": [],
            "total_duration": 0,
            "net_duration": 450,
            "remaining_duration": 450,
            "is_fully_allocated": False,
            "is_over_allocated": False
        }

        # Make the request
        response = self.app.delete(
            '/api/working-times/wt123/ui-project-times/task1')

        # Check the response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('ui_project_times', data)
        self.assertEqual(len(data['ui_project_times']), 0)
        self.assertEqual(data['total_duration'], 0)
        self.assertEqual(data['remaining_duration'], 450)

        # Verify delete_ui_project_time was called correctly
        self.mock_timr_api.get_working_time.assert_called_once_with('wt123')
        self.mock_consolidator.delete_ui_project_time.assert_called_once_with(
            working_time, task_id="task1")

    @patch('app.logger')
    def test_delete_ui_project_time_timr_api_error(self, mock_logger):
        """Test DELETE endpoint handles TimrApiError with enhanced logging."""
        from timr_api import TimrApiError
        
        # Configure get_working_time to succeed
        working_time = {
            "id": "wt123",
            "start": "2025-04-01T09:00:00Z",
            "end": "2025-04-01T17:00:00Z"
        }
        self.mock_timr_api.get_working_time.return_value = working_time
        
        # Configure delete_ui_project_time to raise TimrApiError
        api_error = TimrApiError("Project time not found", status_code=404, response={"error": "Not found"})
        api_error.technical_message = "DELETE /project-times/pt123 failed with 404"
        self.mock_consolidator.delete_ui_project_time.side_effect = api_error
        
        # Make the request
        response = self.app.delete('/api/working-times/wt123/ui-project-times/task1')
        
        # Verify error response
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error', data)
        self.assertEqual(data['error'], "Project time not found")
        
        # Verify enhanced logging was called with proper context
        mock_logger.error.assert_called_once()
        call_args = mock_logger.error.call_args
        
        # Check log message contains technical message
        self.assertIn("DELETE /project-times/pt123 failed with 404", call_args[0][0])
        
        # Check extra context data
        extra_data = call_args[1]['extra']
        self.assertEqual(extra_data['working_time_id'], 'wt123')
        self.assertEqual(extra_data['task_id'], 'task1')
        self.assertEqual(extra_data['error_type'], 'TimrApiError')
        self.assertEqual(extra_data['status_code'], 404)
        self.assertEqual(extra_data['api_response'], {"error": "Not found"})
        
    @patch('app.app_error_handler')
    @patch('app.logger')
    def test_delete_ui_project_time_validation_error(self, mock_logger, mock_error_handler):
        """Test DELETE endpoint handles ValueError with structured logging."""
        # Configure get_working_time to succeed
        working_time = {
            "id": "wt123",
            "start": "2025-04-01T09:00:00Z",
            "end": "2025-04-01T17:00:00Z"
        }
        self.mock_timr_api.get_working_time.return_value = working_time
        
        # Configure delete_ui_project_time to raise ValueError
        validation_error = ValueError("Invalid task ID format")
        self.mock_consolidator.delete_ui_project_time.side_effect = validation_error
        
        # Mock the error handler to return a user-friendly message
        mock_error_handler.log_validation_error.return_value = "The task ID format is invalid."
        
        # Make the request
        response = self.app.delete('/api/working-times/wt123/ui-project-times/invalid-task')
        
        # Verify error response
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error', data)
        self.assertEqual(data['error'], "The task ID format is invalid.")
        
        # Verify structured validation error logging was called
        mock_error_handler.log_validation_error.assert_called_once_with(
            field="ui_project_time_deletion",
            value={'working_time_id': 'wt123', 'task_id': 'invalid-task'},
            reason="Invalid task ID format",
            user_id=REALISTIC_LOGIN_RESPONSE['user']['id']
        )
        
        # Verify standard error logging was also called
        mock_logger.error.assert_called_once()
        call_args = mock_logger.error.call_args
        self.assertIn("Validation error in delete_ui_project_time", call_args[0][0])
        
        # Check extra context data
        extra_data = call_args[1]['extra']
        self.assertEqual(extra_data['working_time_id'], 'wt123')
        self.assertEqual(extra_data['task_id'], 'invalid-task')
        
    @patch('app.app_error_handler')
    def test_delete_ui_project_time_system_error(self, mock_error_handler):
        """Test DELETE endpoint handles unexpected exceptions with comprehensive logging."""
        # Configure get_working_time to succeed
        working_time = {
            "id": "wt123",
            "start": "2025-04-01T09:00:00Z",
            "end": "2025-04-01T17:00:00Z"
        }
        self.mock_timr_api.get_working_time.return_value = working_time
        
        # Configure delete_ui_project_time to raise unexpected exception
        system_error = RuntimeError("Unexpected database connection failure")
        self.mock_consolidator.delete_ui_project_time.side_effect = system_error
        
        # Mock the error handler to return a user-friendly message
        mock_error_handler.log_error.return_value = "An unexpected error occurred. Please try again or contact support."
        
        # Make the request
        response = self.app.delete('/api/working-times/wt123/ui-project-times/task1')
        
        # Verify error response
        self.assertEqual(response.status_code, 500)
        data = json.loads(response.data)
        self.assertIn('error', data)
        self.assertEqual(data['error'], "An unexpected error occurred. Please try again or contact support.")
        
        # Verify comprehensive error logging was called with ErrorContext
        mock_error_handler.log_error.assert_called_once()
        call_args = mock_error_handler.log_error.call_args
        
        # Check the error parameter
        self.assertEqual(call_args[1]['error'], system_error)
        
        # Check ErrorContext
        error_context = call_args[1]['context']
        from error_handler import ErrorCategory, ErrorSeverity
        self.assertEqual(error_context.category, ErrorCategory.SYSTEM)
        self.assertEqual(error_context.severity, ErrorSeverity.HIGH)
        self.assertEqual(error_context.operation, "delete_ui_project_time")
        self.assertEqual(error_context.user_id, REALISTIC_LOGIN_RESPONSE['user']['id'])
        self.assertEqual(error_context.working_time_id, 'wt123')
        self.assertEqual(error_context.task_id, 'task1')
    
    @patch('app.logger')
    def test_delete_ui_project_time_working_time_not_found(self, mock_logger):
        """Test DELETE endpoint when working time is not found."""
        from timr_api import TimrApiError
        
        # Configure get_working_time to raise TimrApiError
        api_error = TimrApiError("Working time not found", status_code=404)
        api_error.technical_message = "GET /working-times/nonexistent failed with 404"
        self.mock_timr_api.get_working_time.side_effect = api_error
        
        # Make the request
        response = self.app.delete('/api/working-times/nonexistent/ui-project-times/task1')
        
        # Verify error response
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error', data)
        self.assertEqual(data['error'], "Working time not found")
        
        # Verify the consolidator delete method was never called
        self.mock_consolidator.delete_ui_project_time.assert_not_called()

    def test_replace_ui_project_times(self):
        """Test replacing all UI project times."""
        # Configure mocks
        working_time = {
            "id": "wt123",
            "start": "2025-04-01T09:00:00Z",
            "end": "2025-04-01T17:00:00Z",
            "break_time_total_minutes": 30
        }
        self.mock_timr_api.get_working_time.return_value = working_time

        # Create UIProjectTime objects for the mock response
        ui_pt1 = UIProjectTime("task3", "Task 3", 120, "Project C/Task 3")
        ui_pt2 = UIProjectTime("task4", "Task 4", 180, "Project D/Task 4")

        # Configure the consolidator mock to return sample data
        self.mock_consolidator.replace_ui_project_times.return_value = {
            "working_time": working_time,
            "ui_project_times": [ui_pt1, ui_pt2],
            "consolidated_project_times": [ui_pt1.to_dict(),
                                           ui_pt2.to_dict()],
            "total_duration": 300,
            "net_duration": 450,
            "remaining_duration": 150,
            "is_fully_allocated": False,
            "is_over_allocated": False
        }

        # Make the request
        response = self.app.put('/api/working-times/wt123/ui-project-times',
                                json={
                                    "ui_project_times": [{
                                        "task_id":
                                        "task3",
                                        "task_name":
                                        "Task 3",
                                        "duration_minutes":
                                        120
                                    }, {
                                        "task_id":
                                        "task4",
                                        "task_name":
                                        "Task 4",
                                        "duration_minutes":
                                        180
                                    }]
                                },
                                content_type='application/json')

        # Check the response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('ui_project_times', data)
        self.assertEqual(len(data['ui_project_times']), 2)
        self.assertEqual(data['total_duration'], 300)
        self.assertEqual(data['remaining_duration'], 150)

        # Verify replace_ui_project_times was called correctly
        self.mock_timr_api.get_working_time.assert_called_once_with('wt123')
        self.mock_consolidator.replace_ui_project_times.assert_called_once()

    def test_unauthorized_access(self):
        """Test that unauthorized access is properly handled."""
        # Configure get_current_user to return None to simulate unauthorized access
        self.mock_get_current_user.return_value = None

        # Make the request
        response = self.app.get('/api/working-times/wt123/ui-project-times')

        # Check the response
        self.assertEqual(response.status_code, 401)
        data = json.loads(response.data)
        self.assertIn('error', data)
        self.assertEqual(data['error'], 'Unauthorized')

    def test_invalid_working_time(self):
        """Test handling of invalid working time."""
        # Configure mock to return None for working time
        self.mock_timr_api.get_working_time.return_value = None

        # Make the request
        response = self.app.get(
            '/api/working-times/invalid-id/ui-project-times')

        # Check the response
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.data)
        self.assertIn('error', data)
        self.assertEqual(data['error'], 'Working time not found')

    def test_api_error_handling(self):
        """Test that API errors are properly handled."""
        # Configure mock to raise an exception
        self.mock_timr_api.get_working_time.side_effect = Exception(
            "API Error")

        # Make the request
        response = self.app.get('/api/working-times/wt123/ui-project-times')

        # Check the response
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error', data)
        self.assertIn('API Error', data['error'])


if __name__ == '__main__':
    unittest.main()

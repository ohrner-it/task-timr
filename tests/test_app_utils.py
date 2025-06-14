import unittest
import json
from unittest.mock import patch, MagicMock
from timr_utils import UIProjectTime
from app import app, get_working_times, get_project_times

class TestApiEndpoints(unittest.TestCase):
    """Test the API endpoints in app.py"""
    
    def setUp(self):
        self.app_context = app.app_context()
        self.app = app
        self.app_context.push()
        self.request_context = app.test_request_context()
        self.request_context.push()
    
    def tearDown(self):
        self.request_context.pop()
        self.app_context.pop()
    
    @patch('app.get_current_user')
    @patch('app.timr_api')
    @patch('app.session')
    def test_get_working_times_with_date(self, mock_session, mock_timr_api, mock_get_current_user):
        """Test that get_working_times filters by date correctly."""
        
        # Configure the mock timr_api instance
        mock_timr_api.get_working_times.return_value = [
            {'id': 'wt1', 'start': '2025-05-01T09:00:00Z', 'end': '2025-05-01T17:00:00Z'}
        ]
        
        # Mock the request
        with self.app.test_request_context('/api/working-times?date=2025-05-01'):
            # Mock the session
            mock_session.get.return_value = 'test_token'
            
            # Mock the current user
            mock_get_current_user.return_value = {'id': 'test_user_id'}
            
            # Call the endpoint
            result = get_working_times()
            
            # Verify the API was called with the correct parameters
            mock_timr_api.get_working_times.assert_called_once()
            kwargs = mock_timr_api.get_working_times.call_args[1]
            
            # Check that start_date and end_date are set
            self.assertIn('start_date', kwargs)
            self.assertIn('end_date', kwargs)
            
            # The start_date should be formatted as 2025-05-01T00:00:00Z
            # And should be passed to the correct API parameters
            self.assertEqual(kwargs['start_date'], '2025-05-01T00:00:00Z')
            self.assertEqual(kwargs['end_date'], '2025-05-01T23:59:59Z')
            self.assertEqual(kwargs['user_id'], 'test_user_id')
            
            # Verify the response is a valid JSON response
            # Flask test client returns a Response object or a tuple (response, status_code)
            
            if isinstance(result, tuple):
                response, status_code = result
                self.assertEqual(status_code, 200)
                
                # If response is already a Response object, use get_json() instead
                if hasattr(response, 'get_json'):
                    response_data = response.get_json()
                else:
                    # Convert JSON string to dict
                    response_data = json.loads(response)
            else:
                self.assertEqual(result.status_code, 200)
                response_data = result.get_json()
            
            self.assertIsNotNone(response_data)
    
    @patch('app.get_current_user')
    @patch('app.timr_api')
    @patch('app.session')
    def test_get_working_times_with_invalid_date(self, mock_session, mock_timr_api, mock_get_current_user):
        """Test that get_working_times handles invalid dates properly."""
        
        # Mock the request with invalid date
        with self.app.test_request_context('/api/working-times?date=invalid-date'):
            # Mock the session
            mock_session.get.return_value = 'test_token'
            
            # Mock the current user
            mock_get_current_user.return_value = {'id': 'test_user_id'}
            
            # Call the endpoint
            result = get_working_times()
            
            # Verify that the API was not called
            mock_timr_api.get_working_times.assert_not_called()
            
            # Verify that an error response was returned
            # Flask test client returns a Response object or a tuple (response, status_code)
            
            if isinstance(result, tuple):
                response, status_code = result
                self.assertEqual(status_code, 400)
                
                # If response is already a Response object, use get_json() instead
                if hasattr(response, 'get_json'):
                    response_data = response.get_json()
                else:
                    # Convert JSON string to dict
                    response_data = json.loads(response)
            else:
                self.assertEqual(result.status_code, 400)
                response_data = result.get_json()
            
            self.assertIn('error', response_data)
    
    @patch('app.get_current_user')
    @patch('app.timr_api')
    @patch('app.project_time_consolidator')
    @patch('app.session')
    def test_get_project_times_response_structure(self, mock_session, mock_consolidator, mock_timr_api, mock_get_current_user):
        """Test that get_project_times returns the correct consolidated_project_times structure."""
        
        # Create test data
        mock_working_time = {'id': 'wt1', 'start': '2025-05-01T09:00:00Z', 'end': '2025-05-01T17:00:00Z'}
        
        # Create UIProjectTime objects for the mock
        ui_project_time1 = UIProjectTime(task_id='task1', task_name='Task 1', duration_minutes=60)
        ui_project_time2 = UIProjectTime(task_id='task2', task_name='Task 2', duration_minutes=30)
        
        # Set up consolidated data with the structure expected by the frontend
        mock_consolidated_data = {
            'working_time': mock_working_time,
            'ui_project_times': [ui_project_time1, ui_project_time2],
            'total_duration': 90,
            'net_duration': 120,
            'remaining_duration': 30,
            'is_fully_allocated': False
        }
        
        # Configure mocks
        mock_timr_api.get_working_time.return_value = mock_working_time
        mock_consolidator.consolidate_project_times.return_value = mock_consolidated_data
        
        # Mock the request
        with self.app.test_request_context('/api/project-times?working_time_id=wt1'):
            # Mock the session and user
            mock_session.get.return_value = 'test_token'
            mock_get_current_user.return_value = {'id': 'test_user_id'}
            
            # Call the endpoint
            result = get_project_times()
            
            # Verify API was called with correct parameters
            mock_timr_api.get_working_time.assert_called_once_with('wt1')
            mock_consolidator.consolidate_project_times.assert_called_once_with(mock_working_time)
            
            # Verify response structure
            self.assertEqual(result.status_code, 200)
            response_data = result.get_json()
            
            # Check the response structure
            self.assertIn('consolidated_project_times', response_data)
            self.assertEqual(len(response_data['consolidated_project_times']), 2)
            
            # Verify all required fields are present with correct values
            self.assertEqual(response_data['total_duration'], 90)
            self.assertEqual(response_data['net_duration'], 120)
            self.assertEqual(response_data['remaining_duration'], 30)
            self.assertEqual(response_data['is_fully_allocated'], False)
            
            # Verify the first item in consolidated_project_times has the expected structure
            project_time = response_data['consolidated_project_times'][0]
            self.assertEqual(project_time['task_id'], 'task1')
            self.assertEqual(project_time['task_name'], 'Task 1')
            self.assertEqual(project_time['duration_minutes'], 60)

if __name__ == "__main__":
    unittest.main()

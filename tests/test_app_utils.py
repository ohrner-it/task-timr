import unittest
import datetime
import json
from unittest.mock import patch, MagicMock
from app import parse_date, parse_time, combine_datetime, format_duration, get_working_times, get_project_times
from config import DATE_FORMAT, TIME_FORMAT
from timr_api import TimrApi
from timr_utils import UIProjectTime
from tests.utils import REALISTIC_WORKING_TIME, REALISTIC_LOGIN_RESPONSE

class TestAppUtils(unittest.TestCase):
    """Test utilities from app.py"""
    
    def test_parse_date(self):
        """Test that date parsing works with different formats."""
        # Test standard format (YYYY-MM-DD)
        date_str = "2025-05-01"
        date = parse_date(date_str)
        self.assertIsNotNone(date)
        self.assertEqual(date.year, 2025)
        self.assertEqual(date.month, 5)
        self.assertEqual(date.day, 1)
        
        # Test ISO format with time
        date_str = "2025-05-01T10:30:00Z"
        date = parse_date(date_str)
        self.assertIsNotNone(date)
        self.assertEqual(date.year, 2025)
        self.assertEqual(date.month, 5)
        self.assertEqual(date.day, 1)
        
        # Test with +00:00 timezone
        date_str = "2025-04-01T10:30:00+00:00"
        date = parse_date(date_str)
        self.assertIsNotNone(date)
        self.assertEqual(date.year, 2025)
        
        # Test invalid format
        date_str = "05/01/2025"
        date = parse_date(date_str)
        self.assertIsNone(date)
        
        # Test None
        date = parse_date(None)
        self.assertIsNone(date)
    
    def test_parse_time(self):
        """Test that time parsing works with different formats."""
        # Test standard format (HH:MM)
        time_str = "10:30"
        time = parse_time(time_str)
        self.assertIsNotNone(time)
        self.assertEqual(time.hour, 10)
        self.assertEqual(time.minute, 30)
        
        # Test ISO format with date
        time_str = "2025-05-01T10:30:00Z"
        time = parse_time(time_str)
        self.assertIsNotNone(time)
        self.assertEqual(time.hour, 10)
        self.assertEqual(time.minute, 30)
        
        # Test with +00:00 timezone  
        time_str = "2025-04-01T14:30:00+00:00"
        time = parse_time(time_str)
        self.assertIsNotNone(time)
        self.assertEqual(time.hour, 14)
        self.assertEqual(time.minute, 30)
        
        # Test invalid format
        time_str = "10:30 AM"
        time = parse_time(time_str)
        self.assertIsNone(time)
        
        # Test None
        time = parse_time(None)
        self.assertIsNone(time)
    
    def test_combine_datetime(self):
        """Test combining date and time."""
        date = datetime.date(2025, 5, 1)
        time = datetime.time(10, 30)
        dt = combine_datetime(date, time)
        self.assertEqual(dt.year, 2025)
        self.assertEqual(dt.month, 5)
        self.assertEqual(dt.day, 1)
        self.assertEqual(dt.hour, 10)
        self.assertEqual(dt.minute, 30)
    
    def test_format_duration(self):
        """Test formatting duration in minutes to hours and minutes."""
        # Test 1 hour
        duration = format_duration(60)
        self.assertEqual(duration, "1h 0m")
        
        # Test 1 hour and 30 minutes
        duration = format_duration(90)
        self.assertEqual(duration, "1h 30m")
        
        # Test just minutes
        duration = format_duration(45)
        self.assertEqual(duration, "0h 45m")
        
        # Test multiple hours
        duration = format_duration(150)
        self.assertEqual(duration, "2h 30m")
        
        # Test edge cases
        self.assertEqual(format_duration(0), "0h 0m")  # Zero duration
        self.assertEqual(format_duration(1500), "25h 0m")  # Large duration
        self.assertEqual(format_duration(1), "0h 1m")  # Single minute

class TestApiEndpoints(unittest.TestCase):
    """Test the API endpoints in app.py"""
    
    def setUp(self):
        from app import app
        self.app = app
        self.app_context = app.app_context()
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
        from app import get_working_times
        
        # Configure the mock timr_api instance
        mock_timr_api.get_working_times.return_value = [REALISTIC_WORKING_TIME]
        
        # Mock the request
        with self.app.test_request_context('/api/working-times?date=2025-05-01'):
            # Mock the session
            mock_session.get.return_value = 'test_token'
            
            # Mock the current user
            mock_get_current_user.return_value = REALISTIC_LOGIN_RESPONSE['user']
            
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
            self.assertEqual(kwargs['user_id'], REALISTIC_LOGIN_RESPONSE['user']['id'])
            
            # Verify the response is a valid JSON response
            # Flask test client returns a Response object or a tuple (response, status_code)
            import json
            
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
        from app import get_working_times
        
        # Mock the request with invalid date
        with self.app.test_request_context('/api/working-times?date=invalid-date'):
            # Mock the session
            mock_session.get.return_value = 'test_token'
            
            # Mock the current user
            mock_get_current_user.return_value = REALISTIC_LOGIN_RESPONSE['user']
            
            # Call the endpoint
            result = get_working_times()
            
            # Verify that the API was not called
            mock_timr_api.get_working_times.assert_not_called()
            
            # Verify that an error response was returned
            # Flask test client returns a Response object or a tuple (response, status_code)
            import json
            
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
        from app import get_project_times
        
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
            mock_get_current_user.return_value = REALISTIC_LOGIN_RESPONSE['user']
            
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

    def test_format_date_with_datetime_object(self):
        """Test format_date with datetime object"""
        from app import format_date
        dt = datetime.datetime(2025, 4, 1, 10, 30)
        result = format_date(dt)
        self.assertEqual(result, "2025-04-01")
        
        # Test with non-datetime object (should return as-is)
        date_str = "2025-04-01"
        result = format_date(date_str)
        self.assertEqual(result, "2025-04-01")

if __name__ == "__main__":
    unittest.main()

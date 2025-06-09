"""
Comprehensive test suite for app.py Flask endpoints
Builds upon existing test coverage to add missing test cases
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import json
import datetime
from flask import Flask
from app import app
from timr_api import TimrApiError


class TestAppEndpointsComprehensive(unittest.TestCase):
    """Comprehensive tests for Flask endpoints in app.py"""

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.app = app.test_client()
        self.app.testing = True
        self.app_context = app.app_context()
        self.app_context.push()
        
        # Create a request context
        self.request_context = app.test_request_context()
        self.request_context.push()

        # Mock session
        self.session_patch = patch('flask.session')
        self.mock_session = self.session_patch.start()
        
        # Mock TimrApi instances
        self.timr_api_patch = patch('app.timr_api')
        self.timr_api_elevated_patch = patch('app.timr_api_elevated')
        self.mock_timr_api = self.timr_api_patch.start()
        self.mock_timr_api_elevated = self.timr_api_elevated_patch.start()

    def tearDown(self):
        """Clean up after each test"""
        self.session_patch.stop()
        self.timr_api_patch.stop()
        self.timr_api_elevated_patch.stop()
        self.request_context.pop()
        self.app_context.pop()

    # Test index endpoint
    def test_index_shows_login_form_when_not_authenticated(self):
        """Test that index shows login form when user is not authenticated"""
        self.mock_session.get.return_value = None
        
        response = self.app.get('/')
        
        self.assertEqual(response.status_code, 200)
        # Should contain login form elements (but not check specific HTML since we don't have template details)
        self.assertIsNotNone(response.data)

    def test_index_renders_page_when_authenticated(self):
        """Test that index renders the main page when user is authenticated"""
        self.mock_session.get.side_effect = lambda key, default=None: {
            'token': 'test-token',
            'user': {'id': 'user1', 'fullname': 'Test User'}
        }.get(key, default)
        
        response = self.app.get('/')
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'<!DOCTYPE html>', response.data)

    # Test login endpoint (POST only - no GET route exists)
    def test_login_get_method_not_allowed(self):
        """Test that GET /login is not allowed (only POST exists)"""
        response = self.app.get('/login')
        
        self.assertEqual(response.status_code, 405)  # Method Not Allowed

    def test_login_post_success(self):
        """Test successful login POST request"""
        # Mock successful login
        self.mock_timr_api.login.return_value = {
            'token': 'test-token',
            'user': {'id': 'user1', 'fullname': 'Test User'}
        }
        
        response = self.app.post('/login', data={
            'username': 'testuser',
            'password': 'testpass'
        })
        
        self.assertEqual(response.status_code, 302)
        self.mock_timr_api.login.assert_called_once_with('testuser', 'testpass')

    def test_login_post_failure(self):
        """Test failed login POST request"""
        # Mock failed login
        self.mock_timr_api.login.side_effect = TimrApiError("Invalid credentials")
        
        response = self.app.post('/login', data={
            'username': 'baduser',
            'password': 'badpass'
        })
        
        # Production code redirects with flash message, not renders page with error
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.location.endswith('/'))  # Redirects to index

    def test_login_post_missing_credentials(self):
        """Test login POST with missing credentials"""
        response = self.app.post('/login', data={})
        
        # Production code redirects with flash message for missing credentials
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.location.endswith('/'))  # Redirects to index

    # Test logout endpoint
    def test_logout_clears_session(self):
        """Test that logout clears the session"""
        # Mock session with user data
        session_data = {'token': 'test-token', 'user': {'id': 'user1'}}
        self.mock_session.get.side_effect = lambda key, default=None: session_data.get(key, default)
        
        response = self.app.get('/logout')
        
        self.assertEqual(response.status_code, 302)
        self.mock_timr_api.logout.assert_called_once()

    # Test working times API endpoints
    def test_get_working_times_requires_authentication(self):
        """Test that get_working_times requires authentication"""
        self.mock_session.get.return_value = None
        
        response = self.app.get('/api/working-times')
        
        self.assertEqual(response.status_code, 401)

    def test_get_working_times_with_date_parameter(self):
        """Test get_working_times with date parameter"""
        # Use the Flask test client session context to test real authentication
        with self.app.session_transaction() as sess:
            sess['token'] = 'test-token'
            sess['user'] = {'id': 'user1', 'fullname': 'Test User'}
        
        # Mock API response to match what timr_api.get_working_times returns
        self.mock_timr_api.get_working_times.return_value = [{
            'id': 'wt1',
            'start': '2025-04-01T09:00:00Z',
            'end': '2025-04-01T17:00:00Z'
        }]
        
        response = self.app.get('/api/working-times?date=2025-04-01')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        # Production code returns {'data': working_times}
        self.assertIn('data', data)
        self.assertEqual(len(data['data']), 1)
        self.assertEqual(data['data'][0]['id'], 'wt1')

    def test_get_working_times_api_error(self):
        """Test get_working_times handles API errors"""
        # Use Flask session to test real authentication
        with self.app.session_transaction() as sess:
            sess['token'] = 'test-token'
            sess['user'] = {'id': 'user1'}
        
        # Mock API error
        self.mock_timr_api.get_working_times.side_effect = Exception("API Error")
        
        response = self.app.get('/api/working-times')
        
        # Production code returns 400 for exceptions, not 500
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error', data)

    # Test create working time endpoint
    def test_create_working_time_success(self):
        """Test successful working time creation"""
        # Use Flask session to test real authentication
        with self.app.session_transaction() as sess:
            sess['token'] = 'test-token'
            sess['user'] = {'id': 'user1'}
        
        # Mock successful creation
        created_wt = {
            'id': 'new_wt',
            'start': '2025-04-01T09:00:00Z',
            'end': '2025-04-01T17:00:00Z'
        }
        self.mock_timr_api.create_working_time.return_value = created_wt
        
        response = self.app.post('/api/working-times', 
                                json={
                                    'start': '2025-04-01T09:00:00Z',
                                    'end': '2025-04-01T17:00:00Z',
                                    'pause_duration': 0
                                })
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        # Production code returns {'working_time': working_time}
        self.assertIn('working_time', data)
        self.assertEqual(data['working_time']['id'], 'new_wt')

    def test_create_working_time_missing_data(self):
        """Test create working time with missing required data"""
        # Use Flask session to test real authentication
        with self.app.session_transaction() as sess:
            sess['token'] = 'test-token'
            sess['user'] = {'id': 'user1'}
        
        response = self.app.post('/api/working-times', json={})
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error', data)

    def test_create_working_time_invalid_date_format(self):
        """Test create working time with invalid date format"""
        # Use Flask session to test real authentication
        with self.app.session_transaction() as sess:
            sess['token'] = 'test-token'
            sess['user'] = {'id': 'user1'}
        
        # Test with missing required fields (production expects 'start' and 'end')
        response = self.app.post('/api/working-times', 
                                json={
                                    'start': 'invalid-datetime-format'
                                })
        
        self.assertEqual(response.status_code, 400)

    # Test update working time endpoint
    def test_update_working_time_success(self):
        """Test successful working time update"""
        # Use Flask session to test real authentication
        with self.app.session_transaction() as sess:
            sess['token'] = 'test-token'
            sess['user'] = {'id': 'user1'}
        
        # Mock successful update
        updated_wt = {
            'id': 'wt1',
            'start': '2025-04-01T10:00:00Z',
            'end': '2025-04-01T18:00:00Z'
        }
        self.mock_timr_api.update_working_time.return_value = updated_wt
        
        response = self.app.patch('/api/working-times/wt1', 
                                 json={
                                     'start_time': '10:00',
                                     'end_time': '18:00'
                                 })
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        # Production code returns {'working_time': {...}} structure
        self.assertIn('working_time', data)
        self.assertEqual(data['working_time']['id'], 'wt1')

    def test_update_working_time_not_found(self):
        """Test update working time when working time not found"""
        # Use Flask session to test real authentication
        with self.app.session_transaction() as sess:
            sess['token'] = 'test-token'
            sess['user'] = {'id': 'user1'}
        
        # Mock API error for not found
        self.mock_timr_api.update_working_time.side_effect = TimrApiError("Not found", status_code=404)
        
        response = self.app.patch('/api/working-times/nonexistent', json={})
        
        # Production code returns 400 for TimrApiError, not 404
        self.assertEqual(response.status_code, 400)

    # Test delete working time endpoint
    def test_delete_working_time_success(self):
        """Test successful working time deletion"""
        # Use Flask session to test real authentication
        with self.app.session_transaction() as sess:
            sess['token'] = 'test-token'
            sess['user'] = {'id': 'user1'}
        
        # Mock successful deletion (production code doesn't return anything)
        self.mock_timr_api.delete_working_time.return_value = None
        
        response = self.app.delete('/api/working-times/wt1')
        
        # Production code returns {'success': True} with 200 status
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['success'], True)

    def test_delete_working_time_not_found(self):
        """Test delete working time when working time not found"""
        # Use Flask session to test real authentication
        with self.app.session_transaction() as sess:
            sess['token'] = 'test-token'
            sess['user'] = {'id': 'user1'}
        
        # Mock API error for not found
        self.mock_timr_api.delete_working_time.side_effect = TimrApiError("Not found", status_code=404)
        
        response = self.app.delete('/api/working-times/nonexistent')
        
        # Production code returns 400 for TimrApiError, not 404
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error', data)

    # Test search tasks endpoint
    def test_search_tasks_success(self):
        """Test successful task search"""
        # Use Flask session to test real authentication
        with self.app.session_transaction() as sess:
            sess['token'] = 'test-token'
            sess['user'] = {'id': 'user1'}
        
        # Mock search results - production returns single result
        search_results = [
            {'id': 'task1', 'name': 'Test Task 1'}
        ]
        self.mock_timr_api_elevated.get_tasks.return_value = search_results
        
        response = self.app.get('/api/tasks/search?q=test')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        # Production code returns {'tasks': [...]} format
        self.assertIn('tasks', data)
        self.assertEqual(len(data['tasks']), 1)
        self.assertEqual(data['tasks'][0]['id'], 'task1')

    def test_search_tasks_empty_query(self):
        """Test task search with empty query"""
        # Use Flask session to test real authentication
        with self.app.session_transaction() as sess:
            sess['token'] = 'test-token'
            sess['user'] = {'id': 'user1'}
        
        response = self.app.get('/api/tasks/search')
        
        # Production code returns empty tasks array for short queries, not 400
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('tasks', data)
        self.assertEqual(data['tasks'], [])

    def test_search_tasks_api_error(self):
        """Test task search handles API errors"""
        # Use Flask session to test real authentication
        with self.app.session_transaction() as sess:
            sess['token'] = 'test-token'
            sess['user'] = {'id': 'user1'}
        
        # Mock API error
        self.mock_timr_api_elevated.get_tasks.side_effect = Exception("Search failed")
        
        response = self.app.get('/api/tasks/search?q=test')
        
        # Production code returns empty tasks array with error message for exceptions
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('tasks', data)
        self.assertEqual(data['tasks'], [])
        self.assertIn('error', data)

    # Test recent tasks endpoint
    def test_get_recent_tasks_success(self):
        """Test successful recent tasks retrieval"""
        # Use Flask session to test real authentication
        with self.app.session_transaction() as sess:
            sess['token'] = 'test-token'
            sess['user'] = {'id': 'user1'}
        
        response = self.app.get('/api/recent-tasks')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        # Production returns {'tasks': []} format
        self.assertIn('tasks', data)
        self.assertIsInstance(data['tasks'], list)

    # Test working time types endpoint
    def test_get_working_time_types_success(self):
        """Test successful working time types retrieval"""
        # Use Flask session to test real authentication
        with self.app.session_transaction() as sess:
            sess['token'] = 'test-token'
            sess['user'] = {'id': 'user1'}
        
        # Mock working time types
        wt_types = [
            {'id': 'type1', 'name': 'Regular'},
            {'id': 'type2', 'name': 'Overtime'}
        ]
        self.mock_timr_api.get_working_time_types.return_value = wt_types
        
        response = self.app.get('/api/working-time-types')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        # Production returns {'attendance_types': [], 'other_types': []} format
        self.assertIn('attendance_types', data)
        self.assertIn('other_types', data)
        self.assertIsInstance(data['attendance_types'], list)
        self.assertIsInstance(data['other_types'], list)

    def test_get_working_time_types_api_error(self):
        """Test working time types handles API errors"""
        # Use Flask session to test real authentication
        with self.app.session_transaction() as sess:
            sess['token'] = 'test-token'
            sess['user'] = {'id': 'user1'}
        
        # Mock API error
        self.mock_timr_api.get_working_time_types.side_effect = Exception("API Error")
        
        response = self.app.get('/api/working-time-types')
        
        # Production code returns 200 with empty arrays and error field for exceptions
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('attendance_types', data)
        self.assertIn('other_types', data)
        self.assertEqual(data['attendance_types'], [])
        self.assertEqual(data['other_types'], [])
        self.assertIn('error', data)

    # Test validation endpoint (correct route is /api/validate-working-times)
    def test_validate_working_times_success(self):
        """Test successful working times validation"""
        # Use Flask session to test real authentication
        with self.app.session_transaction() as sess:
            sess['token'] = 'test-token'
            sess['user'] = {'id': 'user1'}
        
        response = self.app.post('/api/validate-working-times', 
                                json={'working_times': []})
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('working_times', data)

    def test_validate_working_times_missing_date(self):
        """Test validation with missing date"""
        # Use Flask session to test real authentication
        with self.app.session_transaction() as sess:
            sess['token'] = 'test-token'
            sess['user'] = {'id': 'user1'}
        
        response = self.app.post('/api/validate-working-times', json={})
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error', data)
        self.assertEqual(data['error'], 'working_times is required')


class TestAppUtilityFunctions(unittest.TestCase):
    """Test utility functions in app.py"""

    def setUp(self):
        """Set up test fixtures"""
        self.app = app.test_client()
        self.app_context = app.app_context()
        self.app_context.push()

    def tearDown(self):
        """Clean up after each test"""
        self.app_context.pop()

    def test_parse_date_valid_formats(self):
        """Test parse_date with valid date formats"""
        from app import parse_date
        
        # Test ISO format
        result = parse_date('2025-04-01')
        self.assertEqual(result.year, 2025)
        self.assertEqual(result.month, 4)
        self.assertEqual(result.day, 1)
        
        # Test with time component (should extract date)
        result = parse_date('2025-04-01T10:30:00Z')
        self.assertEqual(result.year, 2025)
        self.assertEqual(result.month, 4)
        self.assertEqual(result.day, 1)

    def test_parse_date_invalid_formats(self):
        """Test parse_date with invalid date formats"""
        from app import parse_date
        
        # Test invalid format
        result = parse_date('invalid-date')
        self.assertIsNone(result)
        
        # Test empty string
        result = parse_date('')
        self.assertIsNone(result)
        
        # Test None
        result = parse_date(None)
        self.assertIsNone(result)

    def test_parse_time_valid_formats(self):
        """Test parse_time with valid time formats"""
        from app import parse_time
        
        # Test HH:MM format (the main format supported)
        result = parse_time('14:30')
        self.assertIsNotNone(result)
        self.assertEqual(result.hour, 14)
        self.assertEqual(result.minute, 30)
        
        # Test ISO format with timezone
        result = parse_time('2023-01-01T14:30:00+00:00')
        self.assertIsNotNone(result)
        self.assertEqual(result.hour, 14)
        self.assertEqual(result.minute, 30)

    def test_parse_time_invalid_formats(self):
        """Test parse_time with invalid time formats"""
        from app import parse_time
        
        # Test invalid format
        result = parse_time('invalid-time')
        self.assertIsNone(result)
        
        # Test empty string
        result = parse_time('')
        self.assertIsNone(result)
        
        # Test None
        result = parse_time(None)
        self.assertIsNone(result)

    def test_combine_datetime(self):
        """Test combine_datetime function"""
        from app import combine_datetime
        import datetime
        
        date_obj = datetime.date(2025, 4, 1)
        time_obj = datetime.time(14, 30)
        
        result = combine_datetime(date_obj, time_obj)
        
        self.assertEqual(result.year, 2025)
        self.assertEqual(result.month, 4)
        self.assertEqual(result.day, 1)
        self.assertEqual(result.hour, 14)
        self.assertEqual(result.minute, 30)

    def test_format_duration(self):
        """Test format_duration function"""
        from app import format_duration
        
        # Test basic formatting
        self.assertEqual(format_duration(90), "1h 30m")
        self.assertEqual(format_duration(60), "1h 0m")
        self.assertEqual(format_duration(30), "0h 30m")
        self.assertEqual(format_duration(0), "0h 0m")
        
        # Test edge cases
        self.assertEqual(format_duration(1440), "24h 0m")  # Full day
        self.assertEqual(format_duration(1), "0h 1m")     # Single minute

    def test_format_date(self):
        """Test format_date function"""
        from app import format_date
        import datetime
        
        # Test with datetime object (should format)
        datetime_obj = datetime.datetime(2025, 4, 1, 10, 30)
        result = format_date(datetime_obj)
        self.assertEqual(result, "2025-04-01")
        
        # Test with non-datetime object (should return as-is)
        date_str = "2025-04-01"
        result = format_date(date_str)
        self.assertEqual(result, "2025-04-01")

    def test_get_current_user_authenticated(self):
        """Test get_current_user when user is authenticated"""
        from app import get_current_user, app
        
        # Use Flask request context to test real behavior
        with app.test_request_context():
            from flask import session
            # Both token and user are required for authentication
            session['token'] = 'test-token'
            session['user'] = {'id': 'user1', 'fullname': 'Test User'}
            
            result = get_current_user()
            self.assertEqual(result['id'], 'user1')
            self.assertEqual(result['fullname'], 'Test User')

    def test_get_current_user_not_authenticated(self):
        """Test get_current_user when user is not authenticated"""
        from app import get_current_user, app
        
        # Use Flask request context to test real behavior
        with app.test_request_context():
            # No user in session means not authenticated
            result = get_current_user()
            self.assertIsNone(result)


if __name__ == '__main__':
    unittest.main()
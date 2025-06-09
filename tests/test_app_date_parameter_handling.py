import unittest
import datetime
from unittest.mock import patch, Mock
from timr_api import TimrApi

class TestDateParameterHandling(unittest.TestCase):
    """Test the date parameter handling in the Timr API."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.api = TimrApi()
        self.api.token = "test-token"
        self.api.user = {"id": "test-user-id"}
    
    @patch('timr_api.requests.Session.request')
    def test_working_times_date_parameter_names_correct(self, mock_request):
        """Test that correct API parameter names are used for working times date filtering."""
        # Setup the mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": []}
        mock_response.headers = {"Content-Type": "application/json"}
        mock_request.return_value = mock_response
        
        # Call the API with different date formats
        # Test case 1: ISO date format YYYY-MM-DD
        simple_date = "2025-05-01"
        self.api.get_working_times(start_date=simple_date, end_date=simple_date)
        
        # Verify the correct parameter names are used and in the correct format (YYYY-MM-DD)
        mock_request.assert_called_once()
        params = mock_request.call_args[1]['params']
        self.assertIn('start_from', params, "API should use 'start_from' parameter for start date")
        self.assertIn('start_to', params, "API should use 'start_to' parameter for end date")
        self.assertEqual(params['start_from'], simple_date, "Start date should be in YYYY-MM-DD format")
        self.assertEqual(params['start_to'], simple_date, "End date should be in YYYY-MM-DD format")
        
        # Verify the incorrect parameter names are NOT used
        self.assertNotIn('from', params, "API should NOT use 'from' parameter")
        self.assertNotIn('to', params, "API should NOT use 'to' parameter")
        
        # Reset the mock for the next test
        mock_request.reset_mock()
        
        # Test case 2: ISO datetime format with datetime object
        dt = datetime.datetime(2025, 5, 1, 12, 0, 0)
        self.api.get_working_times(start_date=dt, end_date=dt)
        
        # Verify the correct parameter names are used and in the correct format (YYYY-MM-DD)
        mock_request.assert_called_once()
        params = mock_request.call_args[1]['params']
        self.assertIn('start_from', params, "API should use 'start_from' parameter for start date")
        self.assertIn('start_to', params, "API should use 'start_to' parameter for end date")
        self.assertEqual(params['start_from'], "2025-05-01", "Start date should be converted to YYYY-MM-DD format")
        self.assertEqual(params['start_to'], "2025-05-01", "End date should be converted to YYYY-MM-DD format")
    
    @patch('timr_api.requests.Session.request')
    def test_project_times_date_parameter_names_correct(self, mock_request):
        """Test that correct API parameter names are used for project times date filtering."""
        # Setup the mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": []}
        mock_response.headers = {"Content-Type": "application/json"}
        mock_request.return_value = mock_response
        
        # Call the API with different date formats
        # Test case 1: ISO date format YYYY-MM-DD
        simple_date = "2025-05-01"
        self.api.get_project_times(start_date=simple_date, end_date=simple_date)
        
        # Verify the correct parameter names are used and in the correct format (YYYY-MM-DD)
        mock_request.assert_called_once()
        params = mock_request.call_args[1]['params']
        self.assertIn('start_from', params, "API should use 'start_from' parameter for start date")
        self.assertIn('start_to', params, "API should use 'start_to' parameter for end date")
        self.assertEqual(params['start_from'], simple_date, "Start date should be in YYYY-MM-DD format")
        self.assertEqual(params['start_to'], simple_date, "End date should be in YYYY-MM-DD format")
        
        # Verify the incorrect parameter names are NOT used
        self.assertNotIn('from', params, "API should NOT use 'from' parameter")
        self.assertNotIn('to', params, "API should NOT use 'to' parameter")
        
        # Reset the mock for the next test
        mock_request.reset_mock()
        
        # Test case 2: ISO datetime format with datetime object
        dt = datetime.datetime(2025, 5, 1, 12, 0, 0)
        self.api.get_project_times(start_date=dt, end_date=dt)
        
        # Verify the correct parameter names are used and in the correct format (YYYY-MM-DD)
        mock_request.assert_called_once()
        params = mock_request.call_args[1]['params']
        self.assertIn('start_from', params, "API should use 'start_from' parameter for start date")
        self.assertIn('start_to', params, "API should use 'start_to' parameter for end date")
        self.assertEqual(params['start_from'], "2025-05-01", "Start date should be converted to YYYY-MM-DD format")
        self.assertEqual(params['start_to'], "2025-05-01", "End date should be converted to YYYY-MM-DD format")

    @patch('timr_api.requests.Session.request')
    def test_parameter_names_match_api_docs(self, mock_request):
        """Test that parameter names match the official API documentation."""
        # Setup the mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": []}
        mock_response.headers = {"Content-Type": "application/json"}
        mock_request.return_value = mock_response
        
        # Expected parameter names according to the API documentation
        expected_params = {
            'working_times': {
                'date': ['start_from', 'start_to', 'user'],
                'format': 'YYYY-MM-DD'  # Expected date format
            },
            'project_times': {
                'date': ['start_from', 'start_to', 'user', 'task'],
                'format': 'YYYY-MM-DD'  # Expected date format
            }
        }
        
        # Test parameter names for working times
        date_str = "2025-05-01"
        self.api.get_working_times(start_date=date_str, end_date=date_str)
        
        params = mock_request.call_args[1]['params']
        for param in expected_params['working_times']['date']:
            if param not in ['user', 'task']:  # Only check date parameters
                self.assertIn(param, params, f"Working times API should include '{param}' parameter")
        
        # Verify format matches expected (YYYY-MM-DD)
        for param in ['start_from', 'start_to']:
            self.assertEqual(len(params[param]), 10, "Date parameter should be in YYYY-MM-DD format (10 chars)")
            self.assertEqual(params[param], date_str, f"Date format for {param} should match expected format")
        
        # Reset mock for next test
        mock_request.reset_mock()
        
        # Test parameter names for project times
        self.api.get_project_times(start_date=date_str, end_date=date_str, task_id="task1")
        
        params = mock_request.call_args[1]['params']
        # Check required date parameters exist
        for param in ['start_from', 'start_to']:
            self.assertIn(param, params, f"Project times API should include '{param}' parameter")
        
        # Verify format matches expected (YYYY-MM-DD)
        for param in ['start_from', 'start_to']:
            self.assertEqual(len(params[param]), 10, "Date parameter should be in YYYY-MM-DD format (10 chars)")
            self.assertEqual(params[param], date_str, f"Date format for {param} should match expected format")
        
        # Verify task parameter is passed correctly
        self.assertIn('task', params, "Project times API should include 'task' parameter")
        self.assertEqual(params['task'], "task1", "Task ID should be passed correctly")


if __name__ == '__main__':
    unittest.main()

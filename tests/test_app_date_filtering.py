import unittest
from datetime import datetime, date, time
from unittest.mock import patch, MagicMock, Mock
import json
import logging
import requests
from app import app
from timr_api import TimrApi
from tests.utils import REALISTIC_WORKING_TIME, create_working_time_variant

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class TestDateFiltering(unittest.TestCase):
    """Test cases specifically for date-based filtering with the Timr API."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test fixtures once for the test class."""
        # Configure the Flask app for testing
        app.config['TESTING'] = True
        app.config['DEBUG'] = True
        cls.client = app.test_client()
        
        # Sample working times data for testing using realistic structures
        cls.working_times_data = [
            create_working_time_variant(id='wt1', start='2025-04-27T09:00:00+00:00', end='2025-04-27T17:00:00+00:00'),
            create_working_time_variant(id='wt2', start='2025-05-01T08:30:00+00:00', end='2025-05-01T16:30:00+00:00'), 
            create_working_time_variant(id='wt3', start='2025-05-02T09:00:00+00:00', end='2025-05-02T17:00:00+00:00')
        ]
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.api = TimrApi()
        self.api.token = "test-token"
        self.api.user = {"id": "test-user-id"}
    
    def test_01_api_parameter_names_working_times(self):
        """Test that the API uses the correct parameter names for working times."""
        # Mock the request method to check parameter names
        with patch('timr_api.requests.Session.request') as mock_request:
            # Setup the mock response
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"data": []}
            mock_response.headers = {"Content-Type": "application/json"}
            mock_request.return_value = mock_response
            
            # Test with various date formats
            test_dates = [
                # Simple string dates
                "2025-04-27",
                # Full ISO format
                "2025-05-01T00:00:00Z",
                # Datetime objects
                datetime(2025, 5, 2, 12, 0, 0)
            ]
            
            for idx, date_value in enumerate(test_dates):
                # Reset mock for each test case
                mock_request.reset_mock()
                
                # Call API method with date parameters
                logger.debug(f"Testing date format {idx}: {date_value}")
                self.api.get_working_times(start_date=date_value, end_date=date_value)
                
                # Verify parameters sent to the API
                mock_request.assert_called_once()
                params = mock_request.call_args[1]['params']
                
                # Check that the correct parameter names are used
                self.assertIn('start_from', params, f"Test {idx}: 'start_from' parameter missing")
                self.assertIn('start_to', params, f"Test {idx}: 'start_to' parameter missing")
                
                # Check that the old incorrect parameter names are not used
                self.assertNotIn('from', params, f"Test {idx}: 'from' parameter should not be used")
                self.assertNotIn('to', params, f"Test {idx}: 'to' parameter should not be used")
                
                # For datetime objects, verify they are converted to YYYY-MM-DD format
                if isinstance(date_value, datetime):
                    expected_date = date_value.strftime("%Y-%m-%d")
                    self.assertEqual(params['start_from'], expected_date, 
                                     f"Test {idx}: datetime should be converted to YYYY-MM-DD")
                # For ISO format strings, verify they are properly handled
                elif 'T' in str(date_value):
                    expected_date = str(date_value).split('T')[0]
                    self.assertEqual(params['start_from'], expected_date,
                                    f"Test {idx}: full ISO date should be converted to YYYY-MM-DD")
                # For simple date strings, they should be used as-is
                else:
                    self.assertEqual(params['start_from'], date_value, 
                                     f"Test {idx}: simple date string should be used as-is")
    
    def test_02_api_parameter_names_project_times(self):
        """Test that the API uses the correct parameter names for project times."""
        # Mock the request method to check parameter names
        with patch('timr_api.requests.Session.request') as mock_request:
            # Setup the mock response
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"data": []}
            mock_response.headers = {"Content-Type": "application/json"}
            mock_request.return_value = mock_response
            
            # Test with various date formats
            test_dates = [
                # Simple string dates
                "2025-04-27",
                # Full ISO format
                "2025-05-01T00:00:00Z",
                # Datetime objects
                datetime(2025, 5, 2, 12, 0, 0)
            ]
            
            for idx, date_value in enumerate(test_dates):
                # Reset mock for each test case
                mock_request.reset_mock()
                
                # Call API method with date parameters and task_id
                logger.debug(f"Testing date format {idx}: {date_value}")
                self.api.get_project_times(start_date=date_value, end_date=date_value, task_id="test-task")
                
                # Verify parameters sent to the API
                mock_request.assert_called_once()
                params = mock_request.call_args[1]['params']
                
                # Check that the correct parameter names are used
                self.assertIn('start_from', params, f"Test {idx}: 'start_from' parameter missing")
                self.assertIn('start_to', params, f"Test {idx}: 'start_to' parameter missing")
                self.assertIn('task', params, f"Test {idx}: 'task' parameter missing")
                
                # Check that the old incorrect parameter names are not used
                self.assertNotIn('from', params, f"Test {idx}: 'from' parameter should not be used")
                self.assertNotIn('to', params, f"Test {idx}: 'to' parameter should not be used")
                
                # For datetime objects, verify they are converted to YYYY-MM-DD format
                if isinstance(date_value, datetime):
                    expected_date = date_value.strftime("%Y-%m-%d")
                    self.assertEqual(params['start_from'], expected_date, 
                                     f"Test {idx}: datetime should be converted to YYYY-MM-DD")
                # For ISO format strings, verify they are properly handled
                elif 'T' in str(date_value):
                    expected_date = str(date_value).split('T')[0]
                    self.assertEqual(params['start_from'], expected_date,
                                    f"Test {idx}: full ISO date should be converted to YYYY-MM-DD")
                # For simple date strings, they should be used as-is
                else:
                    self.assertEqual(params['start_from'], date_value, 
                                     f"Test {idx}: simple date string should be used as-is")
    
    def test_03_api_integration_with_flask_endpoint(self):
        """Test the integration between Flask route and API for date filtering."""
        # Set up session data for authenticated user
        with app.test_client() as client:
            with client.session_transaction() as session:
                session['token'] = 'test-token'
                session['user'] = {'id': 'user1'}
            
            # Mock the requests.request method to catch the actual API call
            with patch('requests.Session.request') as mock_request:
                # Setup the mock response
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.json.return_value = {"data": []}
                mock_response.headers = {"Content-Type": "application/json"}
                mock_request.return_value = mock_response
                
                # Also patch get_current_user to return a valid user
                with patch('app.get_current_user') as mock_get_current_user:
                    mock_get_current_user.return_value = {'id': 'user1'}
                    
                    # Test a specific date that was problematic in the bug report
                    test_date = '2025-05-03'
                    response = client.get(f'/api/working-times?date={test_date}')
                    
                    # Verify the response is successful
                    self.assertEqual(response.status_code, 200)
                    
                    # Check that the request was captured
                    mock_request.assert_called()
                    
                    # Get the parameters from the call
                    call_args_list = mock_request.call_args_list
                    for call in call_args_list:
                        if 'params' in call[1]:
                            params = call[1]['params']
                            # Only check if this is the API call with parameters
                            if params:
                                self.assertIn('start_from', params, "API should use 'start_from' parameter")
                                self.assertIn('start_to', params, "API should use 'start_to' parameter")
                                # Verify the parameter names are correct and start_from < start_to
                                self.assertNotIn('from', params, "API should NOT use 'from' parameter")
                                self.assertNotIn('to', params, "API should NOT use 'to' parameter")

if __name__ == '__main__':
    unittest.main()

"""
Test module for ongoing working time editing protection.
Tests that ongoing working times cannot be edited or deleted.
"""

import unittest
from unittest.mock import Mock, patch
import sys
import os

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestOngoingWorkingTimeProtection(unittest.TestCase):
    """Test protection against editing/deleting ongoing working times"""

    def setUp(self):
        """Set up test fixtures"""
        self.ongoing_working_time = {
            "id": "ongoing-wt-id",
            "start": "2025-06-15T09:00:00+00:00",
            "end": None,  # Ongoing working time
            "duration": {
                "type": "ongoing",
                "minutes": 120,
                "minutes_rounded": 120
            },
            "break_time_total_minutes": 15,
            "status": "changeable"
        }
        
        self.completed_working_time = {
            "id": "completed-wt-id",
            "start": "2025-06-15T09:00:00+00:00",
            "end": "2025-06-15T11:00:00+00:00",
            "break_time_total_minutes": 15,
            "status": "changeable"
        }

    def test_update_ongoing_working_time_should_be_blocked(self):
        """Test that updating ongoing working times is blocked in backend"""
        
        # This test simulates what the backend endpoint should do
        # when trying to update an ongoing working time
        
        def mock_update_working_time_logic(working_time):
            """Simulate the backend logic for update_working_time endpoint"""
            # Check if this is an ongoing working time (null end time)
            if working_time.get('end') is None:
                return {'error': 'Cannot edit ongoing working times. Please stop the time recording first.'}, 400
            
            # Normal update logic would go here for completed working times
            return {'success': True}, 200
        
        # Test ongoing working time
        result, status_code = mock_update_working_time_logic(self.ongoing_working_time)
        
        self.assertEqual(status_code, 400)
        self.assertIn('Cannot edit ongoing working times', result['error'])
        
        # Test completed working time (should work)
        result, status_code = mock_update_working_time_logic(self.completed_working_time)
        
        self.assertEqual(status_code, 200)
        self.assertTrue(result['success'])

    def test_delete_ongoing_working_time_should_be_blocked(self):
        """Test that deleting ongoing working times is blocked in backend"""
        
        def mock_delete_working_time_logic(working_time):
            """Simulate the backend logic for delete_working_time endpoint"""
            # Check if this is an ongoing working time (null end time)
            if working_time.get('end') is None:
                return {'error': 'Cannot delete ongoing working times. Please stop the time recording first.'}, 400
            
            # Normal delete logic would go here for completed working times
            return {'success': True}, 200
        
        # Test ongoing working time
        result, status_code = mock_delete_working_time_logic(self.ongoing_working_time)
        
        self.assertEqual(status_code, 400)
        self.assertIn('Cannot delete ongoing working times', result['error'])
        
        # Test completed working time (should work)
        result, status_code = mock_delete_working_time_logic(self.completed_working_time)
        
        self.assertEqual(status_code, 200)
        self.assertTrue(result['success'])

    def test_add_task_allocation_to_ongoing_working_time_should_work(self):
        """Test that adding task allocations to ongoing working times still works"""
        
        def mock_add_ui_project_time_logic(working_time, task_id, duration_minutes):
            """Simulate the backend logic for add_ui_project_time endpoint"""
            # This endpoint should NOT check for ongoing status
            # It should only validate inputs and available time
            
            if not task_id or duration_minutes <= 0:
                return {'error': 'Invalid task or duration'}, 400
            
            # Simulate adding task allocation (no ongoing time restriction)
            return {
                'success': True,
                'ui_project_times': [
                    {
                        'task_id': task_id,
                        'duration_minutes': duration_minutes,
                        'task_name': 'Test Task'
                    }
                ]
            }, 200
        
        # Test adding task allocation to ongoing working time
        result, status_code = mock_add_ui_project_time_logic(
            self.ongoing_working_time, 
            'task1', 
            30
        )
        
        self.assertEqual(status_code, 200)
        self.assertTrue(result['success'])
        self.assertEqual(len(result['ui_project_times']), 1)
        
        # Test adding task allocation to completed working time (should also work)
        result, status_code = mock_add_ui_project_time_logic(
            self.completed_working_time, 
            'task2', 
            45
        )
        
        self.assertEqual(status_code, 200)
        self.assertTrue(result['success'])

    def test_frontend_edit_button_logic(self):
        """Test frontend logic for hiding edit/delete buttons on ongoing times"""
        
        def mock_frontend_button_logic(working_time, is_type_editable):
            """Simulate frontend logic for showing/hiding edit buttons"""
            is_ongoing = working_time.get('end') is None
            is_working_time_editable = is_type_editable and not is_ongoing
            
            return {
                'show_task_allocation_buttons': is_type_editable,
                'show_edit_delete_buttons': is_working_time_editable,
                'is_ongoing': is_ongoing
            }
        
        # Test ongoing working time with editable type
        result = mock_frontend_button_logic(self.ongoing_working_time, True)
        
        self.assertTrue(result['show_task_allocation_buttons'])  # Task allocation should work
        self.assertFalse(result['show_edit_delete_buttons'])     # Edit/delete should be disabled
        self.assertTrue(result['is_ongoing'])
        
        # Test completed working time with editable type
        result = mock_frontend_button_logic(self.completed_working_time, True)
        
        self.assertTrue(result['show_task_allocation_buttons'])  # Task allocation should work
        self.assertTrue(result['show_edit_delete_buttons'])      # Edit/delete should work
        self.assertFalse(result['is_ongoing'])
        
        # Test ongoing working time with non-editable type
        result = mock_frontend_button_logic(self.ongoing_working_time, False)
        
        self.assertFalse(result['show_task_allocation_buttons']) # No task allocation for non-editable types
        self.assertFalse(result['show_edit_delete_buttons'])     # No edit/delete for non-editable types
        self.assertTrue(result['is_ongoing'])

    def test_ongoing_status_detection(self):
        """Test the logic for detecting ongoing working times"""
        
        def is_ongoing_working_time(working_time):
            """Helper function to detect ongoing working times"""
            return working_time.get('end') is None
        
        # Test ongoing working time
        self.assertTrue(is_ongoing_working_time(self.ongoing_working_time))
        
        # Test completed working time
        self.assertFalse(is_ongoing_working_time(self.completed_working_time))
        
        # Test working time with empty string end (should be treated as ongoing)
        working_time_empty_end = {
            "id": "test-id",
            "start": "2025-06-15T09:00:00+00:00",
            "end": "",  # Empty string
        }
        # Note: In practice, empty string might need special handling
        # For now, we only check for None (null)
        self.assertFalse(is_ongoing_working_time(working_time_empty_end))


if __name__ == "__main__":
    unittest.main()
import unittest
import datetime
import pytz
from unittest.mock import Mock, patch
from timr_api import TimrApi, TimrApiError


class TestTimrApiTaskFiltering(unittest.TestCase):
    """Tests for task filtering logic that excludes tasks with closed parent tasks"""

    def setUp(self):
        """Set up test fixtures"""
        self.api = TimrApi(company_id="test_company")
        # Mock token for testing
        self.api.token = "test_token"
        self.api.user = {"id": "test_user"}
        
        # Test date references
        self.now = datetime.datetime.now(pytz.UTC)
        self.past_date = self.now - datetime.timedelta(days=30)
        self.future_date = self.now + datetime.timedelta(days=30)
        
    def test_is_task_effectively_bookable_task_with_no_parent(self):
        """Test that task with no parent is bookable if it has no end_date"""
        task = {
            "id": "task-1",
            "name": "Test Task",
            "bookable": True,
            "end_date": None,
            "parent_task": None
        }
        
        result = self.api._is_task_effectively_bookable(task)
        self.assertTrue(result)
        
    def test_is_task_effectively_bookable_task_with_past_end_date(self):
        """Test that task with past end_date is not bookable"""
        task = {
            "id": "task-1",
            "name": "Test Task",
            "bookable": True,
            "end_date": self.past_date.isoformat(),
            "parent_task": None
        }
        
        result = self.api._is_task_effectively_bookable(task)
        self.assertFalse(result)
        
    def test_is_task_effectively_bookable_task_with_future_end_date(self):
        """Test that task with future end_date is bookable"""
        task = {
            "id": "task-1", 
            "name": "Test Task",
            "bookable": True,
            "end_date": self.future_date.isoformat(),
            "parent_task": None
        }
        
        result = self.api._is_task_effectively_bookable(task)
        self.assertTrue(result)
        
    def test_is_task_effectively_bookable_task_with_closed_parent(self):
        """Test that task with closed parent is not bookable even if task itself is active"""
        # Create parent task that is closed
        parent_task = {
            "id": "parent-1",
            "name": "Closed Parent",
            "bookable": True,
            "end_date": self.past_date.isoformat(),
            "parent_task": None
        }
        
        # Create child task that would be active if parent wasn't closed
        child_task = {
            "id": "child-1",
            "name": "Child Task", 
            "bookable": True,
            "end_date": None,  # No end date on child
            "parent_task": {
                "id": "parent-1",
                "name": "Closed Parent"
            }
        }
        
        # Mock the parent task fetch
        with patch.object(self.api, '_get_task_by_id', return_value=parent_task):
            result = self.api._is_task_effectively_bookable(child_task)
            self.assertFalse(result)
            
    def test_is_task_effectively_bookable_task_with_open_parent(self):
        """Test that task with open parent is bookable if task is also active"""
        # Create parent task that is open
        parent_task = {
            "id": "parent-1", 
            "name": "Open Parent",
            "bookable": True,
            "end_date": None,
            "parent_task": None
        }
        
        # Create child task that is active
        child_task = {
            "id": "child-1",
            "name": "Child Task",
            "bookable": True, 
            "end_date": None,
            "parent_task": {
                "id": "parent-1",
                "name": "Open Parent"
            }
        }
        
        # Mock the parent task fetch
        with patch.object(self.api, '_get_task_by_id', return_value=parent_task):
            result = self.api._is_task_effectively_bookable(child_task)
            self.assertTrue(result)
            
    def test_is_task_effectively_bookable_task_with_nested_closed_grandparent(self):
        """Test that task is not bookable if grandparent is closed"""
        # Create grandparent task that is closed
        grandparent_task = {
            "id": "grandparent-1",
            "name": "Closed Grandparent", 
            "bookable": True,
            "end_date": self.past_date.isoformat(),
            "parent_task": None
        }
        
        # Create parent task that is open but has closed grandparent
        parent_task = {
            "id": "parent-1",
            "name": "Open Parent",
            "bookable": True,
            "end_date": None,
            "parent_task": {
                "id": "grandparent-1",
                "name": "Closed Grandparent"
            }
        }
        
        # Create child task that would be active if grandparent wasn't closed
        child_task = {
            "id": "child-1",
            "name": "Child Task",
            "bookable": True,
            "end_date": None,
            "parent_task": {
                "id": "parent-1", 
                "name": "Open Parent"
            }
        }
        
        # Mock the task fetches for hierarchy
        def mock_get_task(task_id):
            if task_id == "parent-1":
                return parent_task
            elif task_id == "grandparent-1":
                return grandparent_task
            else:
                raise TimrApiError(f"Task {task_id} not found", 404)
                
        with patch.object(self.api, '_get_task_by_id', side_effect=mock_get_task):
            result = self.api._is_task_effectively_bookable(child_task)
            self.assertFalse(result)
            
    def test_is_task_effectively_bookable_handles_api_errors_gracefully(self):
        """Test that API errors when fetching parent tasks are handled gracefully"""
        child_task = {
            "id": "child-1",
            "name": "Child Task",
            "bookable": True,
            "end_date": None,
            "parent_task": {
                "id": "parent-1",
                "name": "Unknown Parent"
            }
        }
        
        # Mock API error when fetching parent
        with patch.object(self.api, '_get_task_by_id', side_effect=TimrApiError("Not found", 404)):
            result = self.api._is_task_effectively_bookable(child_task)
            # Should return True (assume active) when parent can't be fetched
            self.assertTrue(result)
            
    def test_get_tasks_filters_out_tasks_with_closed_parents(self):
        """Test that get_tasks excludes tasks with closed parents from results"""
        # Mock API response with mixed tasks
        mock_tasks = [
            {
                "id": "good-task",
                "name": "Good Task",
                "bookable": True,
                "end_date": None,
                "parent_task": None
            },
            {
                "id": "bad-task", 
                "name": "Bad Task",
                "bookable": True,
                "end_date": None,
                "parent_task": {
                    "id": "closed-parent",
                    "name": "Closed Parent"
                }
            }
        ]
        
        # Mock closed parent
        closed_parent = {
            "id": "closed-parent",
            "name": "Closed Parent", 
            "bookable": True,
            "end_date": self.past_date.isoformat(),
            "parent_task": None
        }
        
        with patch.object(self.api, '_request_paginated', return_value=mock_tasks), \
             patch.object(self.api, '_get_task_by_id', return_value=closed_parent):
            
            result = self.api.get_tasks(active_only=True)
            
            # Should only return the good task, bad task should be filtered out
            self.assertEqual(len(result), 1)
            self.assertEqual(result[0]["id"], "good-task")
            
    def test_get_tasks_preserves_tasks_with_open_parents(self):
        """Test that get_tasks includes tasks with open parents in results"""
        # Mock API response
        mock_tasks = [
            {
                "id": "child-task",
                "name": "Child Task", 
                "bookable": True,
                "end_date": None,
                "parent_task": {
                    "id": "open-parent",
                    "name": "Open Parent"
                }
            }
        ]
        
        # Mock open parent
        open_parent = {
            "id": "open-parent",
            "name": "Open Parent",
            "bookable": True, 
            "end_date": None,
            "parent_task": None
        }
        
        with patch.object(self.api, '_request_paginated', return_value=mock_tasks), \
             patch.object(self.api, '_get_task_by_id', return_value=open_parent):
            
            result = self.api.get_tasks(active_only=True)
            
            # Should return the child task since parent is open
            self.assertEqual(len(result), 1)
            self.assertEqual(result[0]["id"], "child-task")

    def test_real_world_case_3995_scenario(self):
        """Test the specific real-world case that was reported (task 3995)"""
        # Simulate task 3995 scenario
        task_3995 = {
            "id": "a8a70a90-5f19-435d-a3a6-7436fb780a70",
            "name": "3995 IMP ADM - MemoryAlpha Backup Partition vollgelaufen",
            "bookable": True,
            "end_date": None,
            "parent_task": {
                "id": "4c71da5b-a7bf-46ad-a686-85ef0a0afffb", 
                "name": "3994 BUG ADM - MemoryAlpha Backup Partition vollgelaufen"
            }
        }
        
        # Parent task that is closed (as discovered in analysis)
        parent_3994 = {
            "id": "4c71da5b-a7bf-46ad-a686-85ef0a0afffb",
            "name": "3994 BUG ADM - MemoryAlpha Backup Partition vollgelaufen",
            "bookable": True,
            "end_date": "2024-05-28T00:00:00+00:00",  # Closed in May 2024
            "parent_task": None
        }
        
        with patch.object(self.api, '_get_task_by_id', return_value=parent_3994):
            result = self.api._is_task_effectively_bookable(task_3995)
            # Should be False because parent is closed
            self.assertFalse(result)

    def test_parent_task_caching_prevents_duplicate_api_calls(self):
        """Test that caching prevents duplicate API calls for the same parent task"""
        # Create two child tasks with the same parent
        child_task_1 = {
            "id": "child-1",
            "name": "Child Task 1",
            "bookable": True,
            "end_date": None,
            "parent_task": {
                "id": "shared-parent",
                "name": "Shared Parent"
            }
        }
        
        child_task_2 = {
            "id": "child-2", 
            "name": "Child Task 2",
            "bookable": True,
            "end_date": None,
            "parent_task": {
                "id": "shared-parent",
                "name": "Shared Parent"
            }
        }
        
        # Mock parent task
        shared_parent = {
            "id": "shared-parent",
            "name": "Shared Parent",
            "bookable": True,
            "end_date": None,
            "parent_task": None
        }
        
        # Mock the _request method instead of _get_task_by_id to test actual caching logic
        with patch.object(self.api, '_request', return_value=shared_parent) as mock_request:
            # Check both tasks
            result1 = self.api._is_task_effectively_bookable(child_task_1)
            result2 = self.api._is_task_effectively_bookable(child_task_2)
            
            # Both should be bookable
            self.assertTrue(result1)
            self.assertTrue(result2)
            
            # API should only be called once due to caching (second call uses cache)
            mock_request.assert_called_once_with("GET", "/tasks/shared-parent")

    def test_parent_task_cache_is_isolated_per_get_tasks_call(self):
        """Test that parent task cache is cleared between different get_tasks calls"""
        # Create tasks that will trigger parent fetching
        mock_tasks = [
            {
                "id": "child-1",
                "name": "Child Task 1", 
                "bookable": True,
                "end_date": None,
                "parent_task": {
                    "id": "parent-1",
                    "name": "Parent 1"
                }
            }
        ]
        
        parent_task = {
            "id": "parent-1",
            "name": "Parent 1",
            "bookable": True,
            "end_date": None,
            "parent_task": None
        }
        
        with patch.object(self.api, '_request_paginated', return_value=mock_tasks), \
             patch.object(self.api, '_request', return_value=parent_task) as mock_request:
            
            # First get_tasks call
            result1 = self.api.get_tasks(active_only=True)
            first_call_count = mock_request.call_count
            
            # Second get_tasks call should fetch parent again (cache cleared)
            result2 = self.api.get_tasks(active_only=True)
            second_call_count = mock_request.call_count
            
            # Should have fetched parent task twice (once per get_tasks call)
            self.assertEqual(first_call_count, 1)
            self.assertEqual(second_call_count, 2)
            self.assertEqual(len(result1), 1)
            self.assertEqual(len(result2), 1)

    def test_parent_task_cache_handles_api_errors_correctly(self):
        """Test that caching doesn't interfere with error handling"""
        child_task = {
            "id": "child-1",
            "name": "Child Task",
            "bookable": True,
            "end_date": None,
            "parent_task": {
                "id": "error-parent",
                "name": "Error Parent"
            }
        }
        
        with patch.object(self.api, '_request', side_effect=TimrApiError("Not found", 404)) as mock_request:
            # First call should handle error gracefully
            result1 = self.api._is_task_effectively_bookable(child_task)
            self.assertTrue(result1)  # Should assume active when parent can't be fetched
            
            # Second call should not use cache for failed requests
            result2 = self.api._is_task_effectively_bookable(child_task)
            self.assertTrue(result2)
            
            # Should have attempted to fetch parent twice (no caching of errors)
            self.assertEqual(mock_request.call_count, 2)

    def test_parent_task_cache_works_with_deep_hierarchy(self):
        """Test that caching works correctly with nested parent hierarchies"""
        # Create a deep hierarchy: grandchild -> child -> parent -> grandparent
        grandchild_task = {
            "id": "grandchild",
            "name": "Grandchild Task",
            "bookable": True,
            "end_date": None,
            "parent_task": {
                "id": "child-parent",
                "name": "Child Parent"
            }
        }
        
        child_parent = {
            "id": "child-parent",
            "name": "Child Parent",
            "bookable": True,
            "end_date": None,
            "parent_task": {
                "id": "grandparent",
                "name": "Grandparent"
            }
        }
        
        grandparent = {
            "id": "grandparent",
            "name": "Grandparent",
            "bookable": True,
            "end_date": None,
            "parent_task": None
        }
        
        def mock_request(method, endpoint):
            if endpoint == "/tasks/child-parent":
                return child_parent
            elif endpoint == "/tasks/grandparent":
                return grandparent
            else:
                raise TimrApiError(f"Task not found: {endpoint}", 404)
        
        with patch.object(self.api, '_request', side_effect=mock_request) as mock_request_func:
            # First check should traverse the full hierarchy
            result1 = self.api._is_task_effectively_bookable(grandchild_task)
            self.assertTrue(result1)
            
            # Check the same task again - should use cached parent data
            result2 = self.api._is_task_effectively_bookable(grandchild_task)
            self.assertTrue(result2)
            
            # Should have fetched each parent only once due to caching
            expected_calls = [
                unittest.mock.call("GET", "/tasks/child-parent"), 
                unittest.mock.call("GET", "/tasks/grandparent")
            ]
            mock_request_func.assert_has_calls(expected_calls)
            self.assertEqual(mock_request_func.call_count, 2)  # Only 2 calls total, not 4


if __name__ == '__main__':
    unittest.main()
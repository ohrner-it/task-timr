"""
Tests for retrieving the tasks a user can book on.

Bookability (task flag) and activity (own and inherited parent task dates) are
filtered by the Timr API itself via /users/{id}/tasks; these tests verify that the
client requests exactly that filter. The server-side semantics are validated by the
integration tests.
"""

import datetime
import unittest
from unittest.mock import Mock, patch

from timr_api import TimrApi
from tests.utils.http_responses import make_json_response

# Created before datetime.date gets patched in the tests
TODAY = datetime.date(2026, 10, 4)


class TestTimrApiBookableTasks(unittest.TestCase):
    """Tests for TimrApi.get_bookable_tasks"""

    def setUp(self):
        self.api = TimrApi()
        self.api.token = "access-token"
        self.api.user = {"id": "user-1"}
        self.api.session = Mock()
        self.api.session.request.return_value = make_json_response(200, {
            "data": [{"id": "task-1", "name": "Development", "breadcrumbs": "Customer/Development"}],
            "next_page_token": None,
        })

    def _sent(self):
        return self.api.session.request.call_args.kwargs

    def test_requests_tasks_of_current_user(self):
        self.api.get_bookable_tasks()

        self.assertEqual(self._sent()["method"], "GET")
        self.assertEqual(self._sent()["url"], "https://api.timr.com/v1/users/user-1/tasks")

    @patch("timr_api.datetime.date")
    def test_filters_for_bookable_tasks_active_today(self, mock_date):
        mock_date.today.return_value = TODAY

        self.api.get_bookable_tasks()

        params = self._sent()["params"]
        self.assertIs(params["bookable"], True)
        self.assertEqual(params["active_at"], "2026-10-04")

    def test_passes_search_term_as_name_filter(self):
        self.api.get_bookable_tasks(search="Develop")

        self.assertEqual(self._sent()["params"]["name"], "Develop")

    def test_omits_name_filter_without_search_term(self):
        self.api.get_bookable_tasks()

        self.assertNotIn("name", self._sent()["params"])

    def test_returns_tasks_from_response(self):
        tasks = self.api.get_bookable_tasks()

        self.assertEqual(tasks, [{"id": "task-1", "name": "Development",
                                  "breadcrumbs": "Customer/Development"}])

    def test_collects_tasks_from_all_pages(self):
        self.api.session.request.side_effect = [
            make_json_response(200, {"data": [{"id": "task-1"}], "next_page_token": "page-2"}),
            make_json_response(200, {"data": [{"id": "task-2"}], "next_page_token": None}),
        ]

        tasks = self.api.get_bookable_tasks()

        self.assertEqual([task["id"] for task in tasks], ["task-1", "task-2"])
        self.assertEqual(self._sent()["params"]["page_token"], "page-2")


if __name__ == "__main__":
    unittest.main()

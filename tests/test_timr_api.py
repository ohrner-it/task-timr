import unittest
import datetime
import json
from unittest.mock import Mock
import pytz
from config import REQUEST_TIMEOUT_SECONDS
from timr_api import TimrApi, TimrApiError, PROBLEM_TYPE_TASK_NOT_BOOKABLE
from tests.utils.http_responses import make_json_response


class TestTimrApiDateFormatting(unittest.TestCase):
    """Formatting of dates and times for API requests"""

    def setUp(self):
        self.api = TimrApi()

    def test_format_datetime_iso8601(self):
        """Date-time values are sent in ISO 8601 with explicit UTC offset"""
        cases = [
            (datetime.datetime(2025, 5, 1, 9, 0, 0, tzinfo=pytz.UTC), "2025-05-01T09:00:00+00:00"),
            ("2025-05-01T09:00:00Z", "2025-05-01T09:00:00+00:00"),
            ("2025-05-01T09:00:00+00:00", "2025-05-01T09:00:00+00:00"),
            ("2025-05-01", "2025-05-01T00:00:00+00:00"),
            (datetime.date(2025, 5, 1), "2025-05-01T00:00:00+00:00"),
        ]
        for value, expected in cases:
            with self.subTest(value=value):
                self.assertEqual(self.api._format_datetime_iso8601(value), expected)

    def test_format_date_for_query(self):
        """Date filters are sent as plain dates"""
        cases = [
            (datetime.datetime(2025, 5, 1, 9, 0, 0), "2025-05-01"),
            (datetime.date(2025, 5, 1), "2025-05-01"),
            ("2025-05-01T09:00:00Z", "2025-05-01"),
            ("2025-05-01", "2025-05-01"),
        ]
        for value, expected in cases:
            with self.subTest(value=value):
                self.assertEqual(self.api._format_date_for_query(value), expected)


class TestTimrApiV1Requests(unittest.TestCase):
    """Requests sent to and responses read from the Timr API v1 (HTTP boundary mocked)."""

    def setUp(self):
        self.api = TimrApi()
        self.api.token = "access-token"
        self.api.user = {"id": "user-1"}
        self.api.session = Mock()
        self.api.session.request.return_value = make_json_response(
            200, {"data": [], "next_page_token": None})

    def _sent(self):
        """Return keyword arguments of the last HTTP request."""
        return self.api.session.request.call_args.kwargs

    def test_requests_use_v1_base_url_and_bearer_token(self):
        self.api.get_working_time_types()

        self.assertTrue(self._sent()["url"].startswith("https://api.timr.com/v1/working-time-types"))
        self.assertEqual(self._sent()["headers"]["Authorization"], "Bearer access-token")

    def test_requests_are_sent_with_timeout(self):
        self.api.get_working_time_types()

        self.assertEqual(self._sent()["timeout"], REQUEST_TIMEOUT_SECONDS)

    def test_get_working_times_filters_by_current_user_with_users_parameter(self):
        self.api.get_working_times(start_date="2026-10-01", end_date="2026-10-02")

        params = self._sent()["params"]
        self.assertEqual(params["users"], "user-1")
        self.assertNotIn("user", params)

    def test_get_project_times_filters_by_given_user_with_users_parameter(self):
        self.api.get_project_times(start_date="2026-10-01", end_date="2026-10-02", user_id="user-2")

        params = self._sent()["params"]
        self.assertEqual(params["users"], "user-2")
        self.assertNotIn("user", params)

    def test_create_working_time_sends_current_user_and_given_working_time_type(self):
        self.api.session.request.return_value = make_json_response(201, {"id": "wt-1"})

        self.api.create_working_time(start="2026-10-01T09:00:00+02:00",
                                     end="2026-10-01T17:00:00+02:00",
                                     working_time_type_id="type-1")

        payload = json.loads(self._sent()["data"])
        self.assertEqual(payload["user_id"], "user-1")
        self.assertEqual(payload["working_time_type_id"], "type-1")

    def test_problem_details_error_exposes_detail_field_errors_status_and_type(self):
        self.api.session.request.return_value = make_json_response(422, {
            "type": "https://errors.timr.com/validation",
            "title": "Bad Request",
            "status": 422,
            "detail": "Request validation failed",
            "instance": "/working-times",
            "trace_id": "trace-1",
            "errors": [{"detail": "must not be null", "field": "start",
                        "type": "https://errors.timr.com/validation/not-null"}],
        }, content_type="application/problem+json")

        with self.assertRaises(TimrApiError) as context:
            self.api.get_working_time("wt-1")

        error = context.exception
        self.assertEqual(error.status_code, 422)
        self.assertEqual(error.problem_type, "https://errors.timr.com/validation")
        self.assertEqual(error.get_technical_message(),
                         "Request validation failed (start: must not be null)")

    def test_problem_details_error_without_detail_uses_title(self):
        self.api.session.request.return_value = make_json_response(403, {
            "type": "https://errors.timr.com/forbidden", "title": "Forbidden", "status": 403,
        }, content_type="application/problem+json")

        with self.assertRaises(TimrApiError) as context:
            self.api.get_working_time("wt-1")

        self.assertEqual(context.exception.get_technical_message(), "Forbidden")

    def test_create_project_time_on_non_bookable_task_reports_business_rule(self):
        self.api.session.request.return_value = make_json_response(422, {
            "type": PROBLEM_TYPE_TASK_NOT_BOOKABLE,
            "title": "Unprocessable Content",
            "status": 422,
            "detail": "Task is a container",
        }, content_type="application/problem+json")

        with self.assertRaises(TimrApiError) as context:
            self.api.create_project_time("task-1", "2026-10-01T09:00:00+02:00",
                                         "2026-10-01T10:00:00+02:00")

        self.assertEqual(context.exception.get_user_message(),
                         "This task is not bookable. Please select a different task.")
        self.assertEqual(context.exception.problem_type, PROBLEM_TYPE_TASK_NOT_BOOKABLE)

    def test_create_project_time_passes_other_problems_through_unchanged(self):
        self.api.session.request.return_value = make_json_response(409, {
            "type": "https://errors.timr.com/conflict/resource-outdated",
            "title": "Conflict",
            "status": 409,
            "detail": "The entry was modified in the meantime",
        }, content_type="application/problem+json")

        with self.assertRaises(TimrApiError) as context:
            self.api.create_project_time("task-1", "2026-10-01T09:00:00+02:00",
                                         "2026-10-01T10:00:00+02:00")

        self.assertEqual(context.exception.get_user_message(), "The entry was modified in the meantime")
        self.assertEqual(context.exception.problem_type,
                         "https://errors.timr.com/conflict/resource-outdated")


if __name__ == '__main__':
    unittest.main()

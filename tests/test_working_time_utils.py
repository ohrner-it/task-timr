import unittest
import datetime
from working_time_utils import parse_working_time_range


class TestWorkingTimeUtils(unittest.TestCase):
    """Tests for working time helper functions"""

    def test_parse_range_uses_duration(self):
        working_time = {
            "start": "2025-06-14T10:00:00+00:00",
            "end": None,
            "duration": {"minutes": 15},
        }
        start, end = parse_working_time_range(working_time)
        self.assertEqual(start,
                         datetime.datetime(2025, 6, 14, 10, 0, tzinfo=datetime.timezone.utc))
        self.assertEqual(end - start, datetime.timedelta(minutes=15))

    def test_parse_range_missing_values(self):
        with self.assertRaises(ValueError):
            parse_working_time_range({"start": "2025-06-14T10:00:00+00:00"})

    def test_parse_range_missing_start(self):
        with self.assertRaises(ValueError):
            parse_working_time_range({"end": "2025-06-14T10:10:00+00:00"})


if __name__ == '__main__':
    unittest.main()

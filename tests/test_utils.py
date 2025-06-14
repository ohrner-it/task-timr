import unittest
import datetime
from utils import (
    parse_date,
    parse_time,
    combine_datetime,
    format_duration,
    parse_iso_datetime,
)

class TestUtilsFunctions(unittest.TestCase):
    """Test helpers in utils.py."""
    
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

    def test_parse_iso_datetime_valid(self):
        """parse_iso_datetime parses ISO strings with Z suffix and offsets."""
        dt = parse_iso_datetime("2025-05-01T10:00:00Z")
        self.assertEqual(
            dt,
            datetime.datetime(2025, 5, 1, 10, 0, tzinfo=datetime.timezone.utc),
        )

        offset_dt = parse_iso_datetime("2025-05-01T11:30:00+02:00")
        self.assertEqual(
            offset_dt,
            datetime.datetime(
                2025,
                5,
                1,
                11,
                30,
                tzinfo=datetime.timezone(datetime.timedelta(hours=2)),
            ),
        )

    def test_parse_iso_datetime_invalid(self):
        """Invalid or None input returns None."""
        self.assertIsNone(parse_iso_datetime(None))
        self.assertIsNone(parse_iso_datetime("invalid"))


if __name__ == "__main__":
    unittest.main()


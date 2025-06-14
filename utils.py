import logging
from datetime import datetime
from config import DATE_FORMAT, TIME_FORMAT

logger = logging.getLogger(__name__)

def parse_iso_datetime(value):
    """Safely parse an ISO 8601 datetime string.

    Returns None if the value is None or invalid.
    """
    if not value:
        return None
    try:
        if isinstance(value, str) and value.endswith('Z'):
            value = value.replace('Z', '+00:00')
        return datetime.fromisoformat(value)
    except (ValueError, AttributeError, TypeError):
        logger.error("Invalid ISO datetime provided: %s", value)
        return None

def parse_date(date_str):
    """Parse a date string into a datetime.date object."""
    if not date_str:
        return None
    formats = [DATE_FORMAT, "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%SZ"]
    for fmt in formats:
        try:
            if fmt == DATE_FORMAT:
                return datetime.strptime(date_str, fmt).date()
            else:
                if date_str.endswith('Z'):
                    date_str = date_str[:-1] + '+00:00'
                dt = datetime.strptime(date_str, fmt)
                return dt.date()
        except ValueError:
            continue
    return None

def parse_time(time_str):
    """Parse a time string into a datetime.time object."""
    if not time_str:
        return None
    formats = [TIME_FORMAT, "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%SZ"]
    for fmt in formats:
        try:
            if fmt == TIME_FORMAT:
                return datetime.strptime(time_str, fmt).time()
            else:
                if time_str.endswith('Z'):
                    time_str = time_str[:-1] + '+00:00'
                dt = datetime.strptime(time_str, fmt)
                return dt.time()
        except ValueError:
            continue
    return None

def combine_datetime(date_obj, time_obj):
    """Combine date and time objects into a datetime."""
    return datetime.combine(date_obj, time_obj)

def format_duration(minutes):
    """Format duration in minutes to hours and minutes."""
    hours = minutes // 60
    remaining_mins = minutes % 60
    return f"{hours}h {remaining_mins}m"

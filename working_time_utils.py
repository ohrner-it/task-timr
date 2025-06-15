"""Utility helpers for working time entries."""

from datetime import datetime, timedelta
from typing import Dict, Tuple


def parse_working_time_range(working_time: Dict[str, any]) -> Tuple[datetime, datetime]:
    """Return start and end datetimes for a working time entry.

    Args:
        working_time: Dict representing the working time.

    Returns:
        Tuple of (start, end) datetimes.

    Raises:
        ValueError: If start is missing or neither end nor duration are provided.
    """
    start_str = working_time.get("start")
    if not start_str:
        raise ValueError("Working time missing start time")
    start_dt = datetime.fromisoformat(start_str.replace("Z", "+00:00"))

    end_str = working_time.get("end")
    if end_str:
        end_dt = datetime.fromisoformat(end_str.replace("Z", "+00:00"))
    else:
        duration = (working_time.get("duration") or {}).get("minutes")
        if duration is None:
            raise ValueError("Working time missing end time and duration")
        end_dt = start_dt + timedelta(minutes=duration)

    return start_dt, end_dt

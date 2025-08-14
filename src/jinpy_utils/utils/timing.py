import time
from datetime import UTC, datetime

# Time constants for duration formatting
SECONDS_IN_MINUTE = 60
SECONDS_IN_HOUR = 3600


def get_current_datetime() -> datetime:
    """Return the current timezone-aware datetime in UTC.

    Returns:
        A `datetime` object with tzinfo set to UTC.
    """
    return datetime.now(UTC)


def get_timestamp_ms() -> int:
    """Return the current timestamp in milliseconds.

    Returns:
        Current timestamp as milliseconds since epoch.
    """
    return int(time.time() * 1000)


def format_duration(seconds: float) -> str:
    """Format duration in seconds to human-readable string.

    Args:
        seconds: Duration in seconds

    Returns:
        Human-readable duration string (e.g., "2.5s", "1m 30s", "1h 5m")
    """
    if seconds < 1:
        return f"{seconds * 1000:.1f}ms"
    elif seconds < SECONDS_IN_MINUTE:
        return f"{seconds:.1f}s"
    elif seconds < SECONDS_IN_HOUR:
        minutes = int(seconds // SECONDS_IN_MINUTE)
        remaining_seconds = int(seconds % SECONDS_IN_MINUTE)
        if remaining_seconds == 0:
            return f"{minutes}m"
        return f"{minutes}m {remaining_seconds}s"
    else:
        hours = int(seconds // SECONDS_IN_HOUR)
        remaining_minutes = int((seconds % SECONDS_IN_HOUR) // SECONDS_IN_MINUTE)
        if remaining_minutes == 0:
            return f"{hours}h"
        return f"{hours}h {remaining_minutes}m"

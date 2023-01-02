import re
from datetime import timedelta, time


def parse_timedelta(time_string: str) -> timedelta:
    # Compile the regular expression
    pattern = re.compile(r"^(?:(\d+)\sday(?:s)?,\s)?(\d{2}):(\d{2})(?::(\d{2}))?$")

    # Use the regular expression to match the time string
    match = pattern.match(time_string)

    # If the time string doesn't match the pattern, return an invalid timedelta
    if not match:
        return timedelta()

    # Extract the number of days, hours, minutes, and seconds from the match
    days = int(match.group(1) or 0)
    hours = int(match.group(2))
    minutes = int(match.group(3))
    seconds = int(match.group(4) or 0)

    # Return a timedelta representing the duration
    return timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds).seconds


def parse_time(time_string: str) -> time:
    # Compile the regular expression
    pattern = re.compile(r"^(?:(\d+)\sday(?:s)?,\s)?(\d{2}):(\d{2})(?::(\d{2}))?$")

    # Use the regular expression to match the time string
    match = pattern.match(time_string)

    # If the time string doesn't match the pattern, return an invalid timedelta
    if not match:
        return time()

    # Extract the number of days, hours, minutes, and seconds from the match
    days = int(match.group(1) or 0)
    hours = int(match.group(2))
    minutes = int(match.group(3))
    seconds = int(match.group(4) or 0)

    # Return a timedelta representing the duration
    return time(hours, minutes, seconds)

# shimmy_cloud_agents/tools/datetime_tool.py

import logging
from datetime import datetime
import pytz
from typing import Optional

logger = logging.getLogger(__name__)

def get_current_datetime(timezone_str: str = "UTC") -> dict:
    """
    Gets the current date and time for a given timezone.

    :param timezone_str: A string representing the timezone, e.g., 'America/New_York' or 'UTC'.
    :return: A dictionary containing the formatted date, time, and timezone information.
    """
    try:
        # Get the timezone object
        tz = pytz.timezone(timezone_str)
    except pytz.UnknownTimeZoneError:
        logger.warning(f"Unknown timezone: {timezone_str}. Defaulting to UTC.")
        tz = pytz.utc
        timezone_str = "UTC"

    # Get the current time in the specified timezone
    now = datetime.now(tz)

    # Format the output
    response = {
        "timezone": timezone_str,
        "date": now.strftime("%Y-%m-%d"),
        "time": now.strftime("%H:%M:%S"),
        "day_of_week": now.strftime("%A"),
        "full_datetime": now.isoformat(),
    }
    logger.info(f"Generated datetime for {timezone_str}: {response}")
    return response 
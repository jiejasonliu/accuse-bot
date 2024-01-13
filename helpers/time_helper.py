import pytz
from datetime import datetime


def utc_to_human_readable(utc_time: datetime, timezone_info: datetime.tzinfo):
    to_timezone = utc_time.replace(
        tzinfo=pytz.timezone('UTC')).astimezone(timezone_info)
    formatted_expire_time = to_timezone.strftime("%Y-%m-%d %I:%M %p %Z")
    return formatted_expire_time

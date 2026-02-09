from datetime import datetime, timezone, timedelta
from pytz import timezone as pytz_timezone
from config import settings

def get_local_time() -> datetime:
    """Get current time in configured timezone"""
    tz = pytz_timezone(settings.TIMEZONE)
    return datetime.now(tz)

def format_time(dt: datetime, include_seconds: bool = False) -> str:
    """Format datetime as time string"""
    if include_seconds:
        return dt.strftime("%H:%M:%S")
    return dt.strftime("%H:%M")

def format_date(dt: datetime, include_time: bool = False) -> str:
    """Format datetime as date string"""
    if include_time:
        return dt.strftime("%d %b %Y, %H:%M")
    return dt.strftime("%d %b %Y")

def format_datetime_short(dt: datetime) -> str:
    """Format datetime in short format"""
    now = get_local_time()
    today = now.date()
    
    if dt.date() == today:
        return f"Today, {dt.strftime('%H:%M')}"
    elif dt.date() == today - timedelta(days=1):
        return f"Yesterday, {dt.strftime('%H:%M')}"
    else:
        return dt.strftime("%d/%m %H:%M")

def get_time_ago(dt: datetime) -> str:
    """Get human-readable time ago"""
    now = get_local_time()
    diff = now - dt
    
    if diff.days > 365:
        years = diff.days // 365
        return f"{years} year{'s' if years > 1 else ''} ago"
    elif diff.days > 30:
        months = diff.days // 30
        return f"{months} month{'s' if months > 1 else ''} ago"
    elif diff.days > 0:
        return f"{diff.days} day{'s' if diff.days > 1 else ''} ago"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f"{hours} hour{'s' if hours > 1 else ''} ago"
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
    else:
        return "just now"
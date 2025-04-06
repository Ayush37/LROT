# backend/functions/time_remaining.py
from datetime import datetime
import pytz
from config import Config
from functions.function_registry import register_function

def time_remaining():
    """
    Calculate time remaining until EOD (5PM EST).
    
    Returns:
        dict: Current time and time remaining information
    """
    # Get current time in EST
    tz = pytz.timezone(Config.EOD_TIMEZONE)
    now = datetime.now(tz)
    
    # Create EOD time for today
    eod = now.replace(hour=Config.EOD_HOUR, minute=0, second=0, microsecond=0)
    
    # If it's already past EOD, return 0 time remaining
    if now > eod:
        hours_remaining = 0
        minutes_remaining = 0
    else:
        # Calculate time difference
        time_diff = eod - now
        hours_remaining = time_diff.seconds // 3600
        minutes_remaining = (time_diff.seconds % 3600) // 60
    
    return {
        "current_time": now.strftime("%Y-%m-%d %H:%M:%S %Z"),
        "eod_time": eod.strftime("%Y-%m-%d %H:%M:%S %Z"),
        "hours_remaining": hours_remaining,
        "minutes_remaining": minutes_remaining,
        "message": "Have a nice day!"
    }

# Register the function
register_function("time_remaining", time_remaining)

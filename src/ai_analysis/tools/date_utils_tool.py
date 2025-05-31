"""
Utility class for date operations and relative date calculations with timezone support.
"""

from datetime import datetime, timedelta
import calendar
import re
import pytz
from typing import Dict, Any, Optional, Union
from dateutil import parser as dateutil_parser

class DateUtilsTool:
    """
    Utility class for common date operations used throughout the application.
    Provides methods for getting current date, last week, last month, next month,
    this month, and other useful date ranges with timezone support.
    """
    
    def __init__(self, default_timezone: str = "UTC"):
        """
        Initialize the DateUtilsTool with timezone support.
        
        Args:
            default_timezone (str): Default timezone to use (e.g., "America/New_York", "UTC")
        """
        # Standard date format for ISO strings
        self.iso_format = "%Y-%m-%dT%H:%M:%SZ"
        # Standard date format for display
        self.display_format = "%Y-%m-%d"
        # Default timezone
        self.default_timezone = default_timezone
        
        # Validate the default timezone
        try:
            pytz.timezone(default_timezone)
        except pytz.exceptions.UnknownTimeZoneError:
            # Fall back to UTC if the timezone is invalid
            self.default_timezone = "UTC"
    
    def get_current_date(self, as_string: bool = True, include_time: bool = False, 
                         timezone: Optional[str] = None) -> Any:
        """
        Get the current date in the specified timezone.
        
        Args:
            as_string (bool): Return date as string if True, datetime object if False
            include_time (bool): Include time in string output if True
            timezone (str, optional): Timezone to use (e.g., "America/New_York")
            
        Returns:
            str or datetime: Current date as string or datetime object
        """
        # Use the specified timezone or fall back to default
        tz_name = timezone or self.default_timezone
        try:
            tz = pytz.timezone(tz_name)
        except pytz.exceptions.UnknownTimeZoneError:
            # Fall back to default timezone if the specified one is invalid
            tz = pytz.timezone(self.default_timezone)
        
        # Get current time in the specified timezone
        now = datetime.now(pytz.UTC).astimezone(tz)
        
        if as_string:
            if include_time:
                # For ISO format, convert to UTC
                utc_now = now.astimezone(pytz.UTC)
                return utc_now.strftime(self.iso_format)
            return now.strftime(self.display_format)
        return now
    
    def get_date_range(self, period: str, as_string: bool = True, 
                       timezone: Optional[str] = None) -> Dict[str, Any]:
        """
        Get start and end dates for common time periods in the specified timezone.
        
        Args:
            period (str): Time period ('today', 'yesterday', 'this_week', 'last_week', 
                         'this_month', 'last_month', 'next_month', 'this_year', 'last_year')
            as_string (bool): Return dates as strings if True, datetime objects if False
            timezone (str, optional): Timezone to use (e.g., "America/New_York")
            
        Returns:
            dict: Dictionary containing start_date and end_date
        """
        # Get current time in the specified timezone
        now = self.get_current_date(as_string=False, timezone=timezone)
        
        if period == "today":
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = now.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        elif period == "yesterday":
            yesterday = now - timedelta(days=1)
            start_date = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = yesterday.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        elif period == "this_week":
            # Get the start of the week (Monday)
            start_date = now - timedelta(days=now.weekday())
            start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
            # End of the week (Sunday)
            end_date = start_date + timedelta(days=6)
            end_date = end_date.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        elif period == "last_week":
            # Start of last week (Monday)
            start_date = now - timedelta(days=now.weekday() + 7)
            start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
            # End of last week (Sunday)
            end_date = start_date + timedelta(days=6)
            end_date = end_date.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        elif period == "this_month":
            # Start of this month
            start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            # End of this month
            last_day = calendar.monthrange(now.year, now.month)[1]
            end_date = now.replace(day=last_day, hour=23, minute=59, second=59, microsecond=999999)
        
        elif period == "last_month":
            # First day of the current month
            first_day_current_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            # Last day of previous month
            last_day_prev_month = first_day_current_month - timedelta(days=1)
            # First day of previous month
            start_date = last_day_prev_month.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            end_date = last_day_prev_month.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        elif period == "next_month":
            # First day of the current month
            first_day_current_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            # First day of next month
            if now.month == 12:
                start_date = first_day_current_month.replace(year=now.year + 1, month=1)
            else:
                start_date = first_day_current_month.replace(month=now.month + 1)
            # Last day of next month
            last_day = calendar.monthrange(start_date.year, start_date.month)[1]
            end_date = start_date.replace(day=last_day, hour=23, minute=59, second=59, microsecond=999999)
        
        elif period == "this_year":
            # Start of this year
            start_date = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
            # End of this year
            end_date = now.replace(month=12, day=31, hour=23, minute=59, second=59, microsecond=999999)
        
        elif period == "last_year":
            # Start of last year
            start_date = now.replace(year=now.year - 1, month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
            # End of last year
            end_date = now.replace(year=now.year - 1, month=12, day=31, hour=23, minute=59, second=59, microsecond=999999)
        
        else:
            # Default to today if invalid period
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = now.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        if as_string:
            # Convert to UTC for ISO format
            utc_start = start_date.astimezone(pytz.UTC)
            utc_end = end_date.astimezone(pytz.UTC)
            
            return {
                "start_date": start_date.strftime(self.display_format),
                "end_date": end_date.strftime(self.display_format),
                "iso_start_date": utc_start.strftime(self.iso_format),
                "iso_end_date": utc_end.strftime(self.iso_format),
                "timezone": timezone or self.default_timezone
            }
        else:
            return {
                "start_date": start_date,
                "end_date": end_date,
                "timezone": timezone or self.default_timezone
            }
    
    def format_date_for_display(self, date_obj: datetime, timezone: Optional[str] = None) -> str:
        """
        Format a datetime object for display in the specified timezone.
        
        Args:
            date_obj (datetime): Datetime object to format
            timezone (str, optional): Timezone to use for display
            
        Returns:
            str: Formatted date string
        """
        # Ensure the datetime is timezone-aware
        if date_obj.tzinfo is None:
            date_obj = pytz.UTC.localize(date_obj)
        
        # Convert to the specified timezone if provided
        if timezone:
            try:
                tz = pytz.timezone(timezone)
                date_obj = date_obj.astimezone(tz)
            except pytz.exceptions.UnknownTimeZoneError:
                # Fall back to default timezone if the specified one is invalid
                tz = pytz.timezone(self.default_timezone)
                date_obj = date_obj.astimezone(tz)
        
        return date_obj.strftime(self.display_format)
    
    def format_date_for_api(self, date_obj: datetime) -> str:
        """
        Format a datetime object for API use (ISO format in UTC).
        
        Args:
            date_obj (datetime): Datetime object to format
            
        Returns:
            str: Formatted date string in ISO format
        """
        # Ensure the datetime is timezone-aware
        if date_obj.tzinfo is None:
            date_obj = pytz.UTC.localize(date_obj)
        else:
            # Convert to UTC
            date_obj = date_obj.astimezone(pytz.UTC)
        
        return date_obj.strftime(self.iso_format)
    
    def parse_date_string(self, date_string: str, include_time: bool = False, 
                          timezone: Optional[str] = None) -> Optional[datetime]:
        """
        Parse a date string into a timezone-aware datetime object.
        
        Args:
            date_string (str): Date string to parse
            include_time (bool): Whether the string includes time information
            timezone (str, optional): Timezone to use if the string doesn't specify one
            
        Returns:
            datetime or None: Parsed timezone-aware datetime object or None if failed
        """
        # Get the timezone object
        tz_name = timezone or self.default_timezone
        try:
            tz = pytz.timezone(tz_name)
        except pytz.exceptions.UnknownTimeZoneError:
            # Fall back to default timezone if the specified one is invalid
            tz = pytz.timezone(self.default_timezone)
        
        # First, try to use dateutil parser which handles ISO 8601 well
        try:
            # Handle ISO 8601 with Z timezone indicator
            if 'Z' in date_string:
                # Replace Z with +00:00 for ISO format compatibility
                clean_date_string = date_string.replace('Z', '+00:00')
                dt = dateutil_parser.parse(clean_date_string)
                # If the parsed datetime is naive, assume UTC
                if dt.tzinfo is None:
                    dt = pytz.UTC.localize(dt)
                return dt
            
            # Try dateutil parser for any format
            dt = dateutil_parser.parse(date_string)
            # If the parsed datetime is naive, use the specified timezone
            if dt.tzinfo is None:
                dt = tz.localize(dt)
            return dt
        except (ValueError, TypeError):
            pass
        
        # If dateutil fails, try standard formats
        try:
            if include_time:
                # Try standard ISO format (assumes UTC)
                dt = datetime.strptime(date_string, self.iso_format)
                dt = pytz.UTC.localize(dt)
                return dt
            
            # For date-only formats, use the specified timezone
            dt = datetime.strptime(date_string, self.display_format)
            dt = tz.localize(dt.replace(hour=12))  # Use noon to avoid DST issues
            return dt
        except ValueError:
            # Try different common formats if the standard format doesn't work
            formats = [
                "%Y-%m-%dT%H:%M:%S",  # ISO without Z
                "%Y-%m-%dT%H:%M:%SZ",  # ISO with Z
                "%Y-%m-%d %H:%M:%S",   # Common datetime format
                "%Y-%m-%d",
                "%Y/%m/%d",
                "%m/%d/%Y",
                "%d/%m/%Y",
                "%b %d, %Y",
                "%d %b %Y",
                "%B %d, %Y",
                "%d %B %Y"
            ]
            
            for fmt in formats:
                try:
                    dt = datetime.strptime(date_string, fmt)
                    # For formats with time, assume UTC if no timezone info
                    if 'T' in fmt or ':' in fmt:
                        dt = pytz.UTC.localize(dt)
                    else:
                        # For date-only formats, use the specified timezone
                        dt = tz.localize(dt.replace(hour=12))  # Use noon to avoid DST issues
                    return dt
                except ValueError:
                    continue
            
            return None
    
    def add_days_to_date(self, date_obj: datetime, days: int) -> datetime:
        """
        Add days to a date, preserving timezone information.
        
        Args:
            date_obj (datetime): Base datetime object
            days (int): Number of days to add (can be negative)
            
        Returns:
            datetime: New datetime object with same timezone
        """
        # Ensure the datetime is timezone-aware
        if date_obj.tzinfo is None:
            date_obj = pytz.timezone(self.default_timezone).localize(date_obj)
        
        return date_obj + timedelta(days=days)
    
    def date_to_string(self, date_obj: datetime, include_time: bool = False, 
                       timezone: Optional[str] = None) -> str:
        """
        Convert a datetime object to a string in the specified timezone.
        
        Args:
            date_obj (datetime): Datetime object to convert
            include_time (bool): Include time in output string
            timezone (str, optional): Timezone to use for the string representation
            
        Returns:
            str: Formatted date string
        """
        # Ensure the datetime is timezone-aware
        if date_obj.tzinfo is None:
            date_obj = pytz.UTC.localize(date_obj)
        
        # Convert to the specified timezone if provided
        if timezone:
            try:
                tz = pytz.timezone(timezone)
                date_obj = date_obj.astimezone(tz)
            except pytz.exceptions.UnknownTimeZoneError:
                # Fall back to default timezone if the specified one is invalid
                tz = pytz.timezone(self.default_timezone)
                date_obj = date_obj.astimezone(tz)
        
        if include_time:
            # For ISO format, convert to UTC
            utc_date = date_obj.astimezone(pytz.UTC)
            return utc_date.strftime(self.iso_format)
        return date_obj.strftime(self.display_format)
    
    def get_relative_date(self, reference: str = "today", offset_days: int = 0, 
                          timezone: Optional[str] = None) -> Dict[str, Any]:
        """
        Get a date relative to a reference point with an offset in the specified timezone.
        
        Args:
            reference (str): Reference point ('today', 'tomorrow', 'yesterday', 'start_of_week', etc.)
            offset_days (int): Number of days to offset (can be negative)
            timezone (str, optional): Timezone to use for the calculation
            
        Returns:
            dict: Dictionary containing date information
        """
        # Get the reference date in the specified timezone
        now = self.get_current_date(as_string=False, timezone=timezone)
        
        if reference == "today":
            ref_date = now
        elif reference == "tomorrow":
            ref_date = now + timedelta(days=1)
        elif reference == "yesterday":
            ref_date = now - timedelta(days=1)
        elif reference == "start_of_week":
            # Start of the week (Monday)
            ref_date = now - timedelta(days=now.weekday())
        elif reference == "end_of_week":
            # End of the week (Sunday)
            ref_date = now + timedelta(days=6-now.weekday())
        elif reference == "start_of_month":
            # Start of the month
            ref_date = now.replace(day=1)
        elif reference == "end_of_month":
            # End of the month
            last_day = calendar.monthrange(now.year, now.month)[1]
            ref_date = now.replace(day=last_day)
        else:
            # Default to today
            ref_date = now
        
        # Apply offset
        result_date = ref_date + timedelta(days=offset_days)
        
        # Get the timezone name
        tz_name = timezone or self.default_timezone
        
        # Format date for response
        return {
            "date": self.date_to_string(result_date, timezone=tz_name),
            "iso_date": self.date_to_string(result_date, include_time=True, timezone=tz_name),
            "day_of_week": result_date.strftime("%A"),
            "month": result_date.strftime("%B"),
            "year": result_date.year,
            "timezone": tz_name
        }
    
    def normalize_date_string(self, date_string: str, timezone: Optional[str] = None) -> Optional[str]:
        """
        Normalize a date string to ISO format in UTC, ensuring it uses the current year
        if no year is specified or the year is in the past.
        
        Args:
            date_string (str): Date string to normalize
            timezone (str, optional): Timezone to use for parsing relative dates
            
        Returns:
            str or None: Normalized date string in ISO format or None if parsing failed
        """
        # Get current time in the specified timezone
        now = self.get_current_date(as_string=False, timezone=timezone)
        
        # Special handling for ISO 8601 format with or without Z
        iso_pattern = r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:Z|(?:[+-]\d{2}:\d{2}))?$'
        if re.match(iso_pattern, date_string):
            try:
                # For ISO format, parse with timezone awareness
                parsed_date = self.parse_date_string(date_string, include_time=True, timezone=timezone)
                if parsed_date:
                    # Ensure the date is not in the past
                    if parsed_date.year < now.year:
                        # Update to current year
                        try:
                            # Create a new datetime with the updated year
                            current_tz = parsed_date.tzinfo
                            naive_date = parsed_date.replace(tzinfo=None, year=now.year)
                            parsed_date = current_tz.localize(naive_date)
                            
                            # If this date is still in the past (e.g., earlier in the current year),
                            # move to next year
                            if parsed_date < now:
                                naive_date = parsed_date.replace(tzinfo=None, year=now.year + 1)
                                parsed_date = current_tz.localize(naive_date)
                        except ValueError:
                            # Handle February 29 in non-leap years
                            if parsed_date.month == 2 and parsed_date.day == 29 and not calendar.isleap(now.year):
                                naive_date = datetime(now.year, 3, 1, 
                                                     parsed_date.hour, parsed_date.minute, parsed_date.second)
                                parsed_date = parsed_date.tzinfo.localize(naive_date)
                    
                    # Format as ISO string in UTC
                    return self.format_date_for_api(parsed_date)
                return None
            except Exception:
                return None
        
        # Try to parse the date string for non-ISO formats
        parsed_date = self.parse_date_string(date_string, timezone=timezone)
        
        if parsed_date is None:
            # Handle relative date terms
            if date_string.lower() in ["today", "now"]:
                parsed_date = now
            elif date_string.lower() == "tomorrow":
                parsed_date = now + timedelta(days=1)
            elif date_string.lower() == "yesterday":
                parsed_date = now - timedelta(days=1)
            elif "next" in date_string.lower() and "week" in date_string.lower():
                parsed_date = now + timedelta(days=7)
            elif "next" in date_string.lower() and "month" in date_string.lower():
                # Move to the next month
                current_tz = now.tzinfo
                if now.month == 12:
                    naive_date = now.replace(tzinfo=None, year=now.year + 1, month=1)
                else:
                    naive_date = now.replace(tzinfo=None, month=now.month + 1)
                parsed_date = current_tz.localize(naive_date)
            else:
                # Try to extract month and day
                months = {
                    "jan": 1, "january": 1,
                    "feb": 2, "february": 2,
                    "mar": 3, "march": 3,
                    "apr": 4, "april": 4,
                    "may": 5,
                    "jun": 6, "june": 6,
                    "jul": 7, "july": 7,
                    "aug": 8, "august": 8,
                    "sep": 9, "september": 9,
                    "oct": 10, "october": 10,
                    "nov": 11, "november": 11,
                    "dec": 12, "december": 12
                }
                
                # Try to find a month name in the string
                found_month = None
                for month_name, month_num in months.items():
                    if month_name in date_string.lower():
                        found_month = month_num
                        break
                
                if found_month:
                    # Try to extract a day number
                    day_match = re.search(r'\b(\d{1,2})(st|nd|rd|th)?\b', date_string)
                    if day_match:
                        day = int(day_match.group(1))
                        if 1 <= day <= 31:  # Validate day
                            # Check if a year is specified
                            year_match = re.search(r'\b(20\d{2})\b', date_string)
                            year = int(year_match.group(1)) if year_match else now.year
                            
                            try:
                                # Create a timezone-aware datetime
                                naive_date = datetime(year, found_month, day, 12, 0, 0)  # Use noon to avoid DST issues
                                current_tz = now.tzinfo
                                parsed_date = current_tz.localize(naive_date)
                            except ValueError:
                                # Invalid date (e.g., February 30)
                                return None
                
                if parsed_date is None:
                    return None
        
        # Ensure the date is not in the past (use current year if it is)
        if parsed_date.year < now.year:
            # Update to current year
            try:
                # Create a new datetime with the updated year
                current_tz = parsed_date.tzinfo
                naive_date = parsed_date.replace(tzinfo=None, year=now.year)
                parsed_date = current_tz.localize(naive_date)
                
                # If this date is still in the past (e.g., earlier in the current year),
                # move to next year
                if parsed_date < now:
                    naive_date = parsed_date.replace(tzinfo=None, year=now.year + 1)
                    parsed_date = current_tz.localize(naive_date)
            except ValueError:
                # Handle February 29 in non-leap years
                if parsed_date.month == 2 and parsed_date.day == 29 and not calendar.isleap(now.year):
                    naive_date = datetime(now.year, 3, 1, 12, 0, 0)  # Use noon to avoid DST issues
                    parsed_date = parsed_date.tzinfo.localize(naive_date)
        
        # Format as ISO string in UTC
        return self.format_date_for_api(parsed_date)
    
    def get_available_timezones(self) -> Dict[str, Any]:
        """
        Get a list of available timezones grouped by region.
        
        Returns:
            dict: Dictionary containing timezone information grouped by region
        """
        all_timezones = pytz.all_timezones
        
        # Group timezones by region
        timezone_groups = {}
        for tz_name in all_timezones:
            # Split by first slash to get region
            parts = tz_name.split('/', 1)
            region = parts[0]
            
            if region not in timezone_groups:
                timezone_groups[region] = []
            
            if len(parts) > 1:
                timezone_groups[region].append(tz_name)
            else:
                # Handle special cases like 'UTC'
                if 'Other' not in timezone_groups:
                    timezone_groups['Other'] = []
                timezone_groups['Other'].append(tz_name)
        
        # Add common timezones section
        common_timezones = [
            "UTC",
            "America/New_York",
            "America/Los_Angeles",
            "America/Chicago",
            "Europe/London",
            "Europe/Paris",
            "Asia/Tokyo",
            "Asia/Shanghai",
            "Australia/Sydney",
            "Pacific/Auckland"
        ]
        timezone_groups['Common'] = [tz for tz in common_timezones if tz in all_timezones]
        
        return {
            "groups": timezone_groups,
            "current": self.default_timezone,
            "total_count": len(all_timezones)
        }
    
    def set_default_timezone(self, timezone: str) -> bool:
        """
        Set the default timezone for all date operations.
        
        Args:
            timezone (str): Timezone to set as default (e.g., "America/New_York")
            
        Returns:
            bool: True if successful, False if the timezone is invalid
        """
        try:
            pytz.timezone(timezone)
            self.default_timezone = timezone
            return True
        except pytz.exceptions.UnknownTimeZoneError:
            return False
    
    def get_timezone_offset(self, timezone: Optional[str] = None) -> Dict[str, Any]:
        """
        Get the current offset information for a timezone.
        
        Args:
            timezone (str, optional): Timezone to get offset for
            
        Returns:
            dict: Dictionary containing offset information
        """
        # Use the specified timezone or fall back to default
        tz_name = timezone or self.default_timezone
        try:
            tz = pytz.timezone(tz_name)
        except pytz.exceptions.UnknownTimeZoneError:
            # Fall back to default timezone if the specified one is invalid
            tz = pytz.timezone(self.default_timezone)
            tz_name = self.default_timezone
        
        # Get current time in the timezone
        now = datetime.now(pytz.UTC).astimezone(tz)
        
        # Get the offset
        offset = now.strftime('%z')
        offset_hours = int(offset[0:3])
        offset_minutes = int(offset[0] + offset[3:5])
        
        # Format for display
        if offset_hours >= 0:
            offset_display = f"+{offset_hours}"
        else:
            offset_display = f"{offset_hours}"
        
        if offset_minutes != 0:
            offset_display += f":{abs(offset_minutes)}"
        
        return {
            "timezone": tz_name,
            "offset": offset,
            "offset_hours": offset_hours,
            "offset_minutes": offset_minutes,
            "offset_display": offset_display,
            "is_dst": now.dst() != timedelta(0),
            "current_time": now.strftime("%Y-%m-%d %H:%M:%S")
        }

"""
Date utilities for handling calendar operations.
"""

import logging
from typing import Dict, Optional, Tuple, Any
from datetime import datetime, timedelta
import re
import calendar
import dateutil.parser
import dateutil.tz

logger = logging.getLogger("schoolconnect_ai")

class DateUtils:
    """Utilities for date and time operations."""
    
    # Standard date formats
    ISO_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
    DISPLAY_FORMAT = "%Y-%m-%d"
    
    @staticmethod
    def parse_date_time(text: str) -> Optional[datetime]:
        """
        Parse a date/time from text using various formats.
        
        Args:
            text: Text containing date/time information
            
        Returns:
            Parsed datetime object or None if parsing failed
        """
        try:
            # Try direct ISO format
            return datetime.fromisoformat(text)
        except ValueError:
            pass
        
        # Try common formats
        formats = [
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M",
            "%Y-%m-%d",
            "%m/%d/%Y %H:%M:%S",
            "%m/%d/%Y %H:%M",
            "%m/%d/%Y",
            "%d-%m-%Y %H:%M:%S",
            "%d-%m-%Y %H:%M",
            "%d-%m-%Y",
            "%b %d, %Y",
            "%d %b %Y",
            "%B %d, %Y",
            "%d %B %Y"
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(text, fmt)
            except ValueError:
                continue
        
        # Try natural language parsing
        return DateUtils.parse_natural_language_date(text)
    
    @staticmethod
    def parse_natural_language_date(text: str) -> Optional[datetime]:
        """
        Parse natural language date expressions.
        
        Args:
            text: Natural language date expression
            
        Returns:
            Parsed datetime object or None if parsing failed
        """
        text = text.lower().strip()
        now = datetime.now()
        
        # Today, tomorrow, etc.
        if text == "today":
            return datetime(now.year, now.month, now.day)
        elif text == "tomorrow":
            return datetime(now.year, now.month, now.day) + timedelta(days=1)
        elif text == "yesterday":
            return datetime(now.year, now.month, now.day) - timedelta(days=1)
        
        # Next/last day of week
        days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        for i, day in enumerate(days):
            if f"next {day}" in text:
                days_ahead = (i - now.weekday()) % 7
                if days_ahead == 0:
                    days_ahead = 7
                return datetime(now.year, now.month, now.day) + timedelta(days=days_ahead)
            elif f"last {day}" in text:
                days_behind = (now.weekday() - i) % 7
                if days_behind == 0:
                    days_behind = 7
                return datetime(now.year, now.month, now.day) - timedelta(days=days_behind)
        
        # In X days/weeks/months
        in_match = re.match(r"in (\d+) (day|days|week|weeks|month|months)", text)
        if in_match:
            num = int(in_match.group(1))
            unit = in_match.group(2)
            if unit in ["day", "days"]:
                return now + timedelta(days=num)
            elif unit in ["week", "weeks"]:
                return now + timedelta(days=num*7)
            elif unit in ["month", "months"]:
                # Simple approximation for months
                return now + timedelta(days=num*30)
        
        # X days/weeks/months ago
        ago_match = re.match(r"(\d+) (day|days|week|weeks|month|months) ago", text)
        if ago_match:
            num = int(ago_match.group(1))
            unit = ago_match.group(2)
            if unit in ["day", "days"]:
                return now - timedelta(days=num)
            elif unit in ["week", "weeks"]:
                return now - timedelta(days=num*7)
            elif unit in ["month", "months"]:
                # Simple approximation for months
                return now - timedelta(days=num*30)
        
        return None
    
    @staticmethod
    def get_date_range(period: str, as_timezone_aware: bool = True) -> Dict[str, datetime]:
        """
        Get start and end dates for common time periods.
        
        Args:
            period (str): Time period ('today', 'yesterday', 'this_week', 'last_week', 
                         'this_month', 'last_month', 'next_month', 'this_year', 'last_year')
            as_timezone_aware (bool): Return dates as timezone-aware if True
            
        Returns:
            dict: Dictionary containing start_date and end_date
        """
        now = datetime.now()
        
        if period == "today":
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = now.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        elif period == "yesterday":
            yesterday = now - timedelta(days=1)
            start_date = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = yesterday.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        elif period == "this_week" or period == "this week":
            # Get the start of the week (Monday)
            start_date = now - timedelta(days=now.weekday())
            start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
            # End of the week (Sunday)
            end_date = start_date + timedelta(days=6)
            end_date = end_date.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        elif period == "last_week" or period == "last week":
            # Start of last week (Monday)
            start_date = now - timedelta(days=now.weekday() + 7)
            start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
            # End of last week (Sunday)
            end_date = start_date + timedelta(days=6)
            end_date = end_date.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        elif period == "next_week" or period == "next week":
            # Start of next week (Monday)
            start_date = now + timedelta(days=7 - now.weekday())
            start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
            # End of next week (Sunday)
            end_date = start_date + timedelta(days=6)
            end_date = end_date.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        elif period == "this_month" or period == "this month":
            # Start of this month
            start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            # End of this month
            last_day = calendar.monthrange(now.year, now.month)[1]
            end_date = now.replace(day=last_day, hour=23, minute=59, second=59, microsecond=999999)
        
        elif period == "last_month" or period == "last month":
            # First day of the current month
            first_day_current_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            # Last day of previous month
            last_day_prev_month = first_day_current_month - timedelta(days=1)
            # First day of previous month
            start_date = last_day_prev_month.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            end_date = last_day_prev_month.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        elif period == "next_month" or period == "next month":
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
        
        elif period == "this_year" or period == "this year":
            # Start of this year
            start_date = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
            # End of this year
            end_date = now.replace(month=12, day=31, hour=23, minute=59, second=59, microsecond=999999)
        
        elif period == "last_year" or period == "last year":
            # Start of last year
            start_date = now.replace(year=now.year - 1, month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
            # End of last year
            end_date = now.replace(year=now.year - 1, month=12, day=31, hour=23, minute=59, second=59, microsecond=999999)
        
        else:
            # Default to today if invalid period
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = now.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        # Add timezone information if requested
        if as_timezone_aware:
            start_date = start_date.replace(tzinfo=dateutil.tz.UTC)
            end_date = end_date.replace(tzinfo=dateutil.tz.UTC)
        
        return {
            "start_date": start_date,
            "end_date": end_date
        }
    
    @staticmethod
    def extract_date_time_range(text: str) -> Tuple[Optional[datetime], Optional[datetime]]:
        """
        Extract a date/time range from text.
        
        Args:
            text: Text containing date/time range information
            
        Returns:
            Tuple of (start_datetime, end_datetime), either may be None if extraction failed
        """
        text = text.lower().strip()
        
        # Handle relative time ranges using the get_date_range method
        relative_periods = [
            "today", "yesterday", 
            "this week", "last week", "next week", 
            "this month", "last month", "next month",
            "this year", "last year",
            "this_week", "last_week", "next_week", 
            "this_month", "last_month", "next_month",
            "this_year", "last_year"
        ]
        
        for period in relative_periods:
            if text == period:
                date_range = DateUtils.get_date_range(period, as_timezone_aware=False)
                return date_range["start_date"], date_range["end_date"]
        
        # Look for common patterns
        # "from X to Y"
        from_to_match = re.search(r"from\s+(.+?)\s+to\s+(.+?)(?:\s|$)", text, re.IGNORECASE)
        if from_to_match:
            start_text = from_to_match.group(1)
            end_text = from_to_match.group(2)
            start_dt = DateUtils.parse_date_time(start_text)
            end_dt = DateUtils.parse_date_time(end_text)
            return start_dt, end_dt
        
        # "between X and Y"
        between_match = re.search(r"between\s+(.+?)\s+and\s+(.+?)(?:\s|$)", text, re.IGNORECASE)
        if between_match:
            start_text = between_match.group(1)
            end_text = between_match.group(2)
            start_dt = DateUtils.parse_date_time(start_text)
            end_dt = DateUtils.parse_date_time(end_text)
            return start_dt, end_dt
        
        # "on X at Y" (single date with time)
        on_at_match = re.search(r"on\s+(.+?)\s+at\s+(.+?)(?:\s|$)", text, re.IGNORECASE)
        if on_at_match:
            date_text = on_at_match.group(1)
            time_text = on_at_match.group(2)
            
            date_dt = DateUtils.parse_date_time(date_text)
            if date_dt:
                # Try to parse time and combine with date
                time_formats = ["%H:%M", "%H:%M:%S", "%I:%M %p", "%I:%M:%S %p"]
                for fmt in time_formats:
                    try:
                        time_dt = datetime.strptime(time_text, fmt)
                        start_dt = datetime.combine(date_dt.date(), time_dt.time())
                        # Default to 1 hour duration
                        end_dt = start_dt + timedelta(hours=1)
                        return start_dt, end_dt
                    except ValueError:
                        continue
        
        # If we couldn't extract a range, try to get a single date/time
        single_dt = DateUtils.parse_date_time(text)
        if single_dt:
            # Default to full day for a single date
            start_dt = single_dt.replace(hour=0, minute=0, second=0, microsecond=0)
            end_dt = single_dt.replace(hour=23, minute=59, second=59, microsecond=999999)
            return start_dt, end_dt
        
        return None, None
    
    @staticmethod
    def format_date_for_display(date_obj: datetime) -> str:
        """
        Format a datetime object for display.
        
        Args:
            date_obj (datetime): Datetime object to format
            
        Returns:
            str: Formatted date string
        """
        return date_obj.strftime(DateUtils.DISPLAY_FORMAT)
    
    @staticmethod
    def format_date_for_api(date_obj: datetime) -> str:
        """
        Format a datetime object for API use (ISO format).
        
        Args:
            date_obj (datetime): Datetime object to format
            
        Returns:
            str: Formatted date string in ISO format
        """
        return date_obj.strftime(DateUtils.ISO_FORMAT)

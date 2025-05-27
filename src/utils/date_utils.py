"""
Date utilities for handling calendar operations.
"""

import logging
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta
import re

logger = logging.getLogger("schoolconnect_ai")

class DateUtils:
    """Utilities for date and time operations."""
    
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
    def extract_date_time_range(text: str) -> Tuple[Optional[datetime], Optional[datetime]]:
        """
        Extract a date/time range from text.
        
        Args:
            text: Text containing date/time range information
            
        Returns:
            Tuple of (start_datetime, end_datetime), either may be None if extraction failed
        """
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
            # Default to 1 hour duration
            return single_dt, single_dt + timedelta(hours=1)
        
        return None, None

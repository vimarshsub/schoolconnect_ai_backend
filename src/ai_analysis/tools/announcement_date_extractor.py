"""
Utility for extracting dates from announcement content.
"""

import re
import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
import dateutil.parser
import dateutil.tz

logger = logging.getLogger("schoolconnect_ai")

class AnnouncementDateExtractor:
    """Utility class for extracting dates from announcement content."""
    
    # Common date patterns in announcements
    DATE_PATTERNS = [
        # Formal date patterns
        r'(?:on|for|date:?|scheduled for|happening on|will be on|starts on|begins on|due on|due by)\s+([A-Za-z]+\s+\d{1,2}(?:st|nd|rd|th)?(?:,?\s+\d{4})?)',
        r'(?:on|for|date:?|scheduled for|happening on|will be on|starts on|begins on|due on|due by)\s+(\d{1,2}(?:st|nd|rd|th)?\s+[A-Za-z]+(?:,?\s+\d{4})?)',
        r'(?:on|for|date:?|scheduled for|happening on|will be on|starts on|begins on|due on|due by)\s+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
        
        # Time-specific patterns
        r'(?:at|from|starting at|beginning at|time:?)\s+(\d{1,2}(?::\d{2})?\s*(?:am|pm|AM|PM))',
        
        # Date and time combined
        r'([A-Za-z]+\s+\d{1,2}(?:st|nd|rd|th)?(?:,?\s+\d{4})?)\s+(?:at|from)\s+(\d{1,2}(?::\d{2})?\s*(?:am|pm|AM|PM))',
        r'(\d{1,2}(?:st|nd|rd|th)?\s+[A-Za-z]+(?:,?\s+\d{4})?)\s+(?:at|from)\s+(\d{1,2}(?::\d{2})?\s*(?:am|pm|AM|PM))',
        
        # Specific day mentions
        r'(?:this|next|coming|upcoming)\s+(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)',
        r'(tomorrow|today|tonight|this evening)',
        
        # Month with day
        r'([A-Za-z]+\s+\d{1,2}(?:st|nd|rd|th)?)',
        
        # ISO-like dates
        r'(\d{4}-\d{2}-\d{2})',
        r'(\d{2}/\d{2}/\d{4})',
        r'(\d{2}\.\d{2}\.\d{4})',
    ]
    
    # Common time patterns
    TIME_PATTERNS = [
        r'(\d{1,2}(?::\d{2})?\s*(?:am|pm|AM|PM))',
        r'(\d{1,2}(?::\d{2})?\s*(?:a\.m\.|p\.m\.|A\.M\.|P\.M\.))',
        r'(\d{2}:\d{2})'
    ]
    
    @classmethod
    def extract_date_from_announcement(cls, announcement: Dict[str, Any], 
                                      current_date: Optional[datetime] = None,
                                      timezone: Optional[str] = None) -> Optional[str]:
        """
        Extract the most relevant date from an announcement.
        
        Args:
            announcement: Announcement data dictionary
            current_date: Current date for reference (defaults to now)
            timezone: Timezone for date interpretation
            
        Returns:
            ISO format date string or None if no date found
        """
        if not announcement:
            return None
            
        # Set current date if not provided
        if current_date is None:
            current_date = datetime.now(dateutil.tz.gettz(timezone) if timezone else dateutil.tz.UTC)
        
        # Check for SentTime field first (most reliable)
        event_date = cls._extract_from_sent_time(announcement)
        if event_date:
            return event_date
        
        # Check for explicit EventDate field
        event_date = cls._extract_from_event_date_field(announcement)
        if event_date:
            return event_date
            
        # Extract from title and description
        title = announcement.get("Title", "")
        description = announcement.get("Description", "")
        
        # Try title first (more likely to contain the main event date)
        event_date = cls._extract_date_from_text(title, current_date, timezone)
        if event_date:
            return event_date
            
        # Then try description
        event_date = cls._extract_date_from_text(description, current_date, timezone)
        if event_date:
            return event_date
            
        # If no date found, return None
        return None
    
    @classmethod
    def _extract_from_sent_time(cls, announcement: Dict[str, Any]) -> Optional[str]:
        """
        Extract date from SentTime field, assuming the event is on the same day.
        
        Args:
            announcement: Announcement data dictionary
            
        Returns:
            ISO format date string or None
        """
        sent_time = announcement.get("SentTime")
        if not sent_time:
            return None
            
        try:
            # Parse the sent time
            sent_datetime = dateutil.parser.parse(sent_time)
            
            # Ensure timezone awareness
            if sent_datetime.tzinfo is None:
                sent_datetime = sent_datetime.replace(tzinfo=dateutil.tz.UTC)
                
            # For SentTime, we assume the event might be on the same day
            # But we should check the content to confirm
            title = announcement.get("Title", "").lower()
            description = announcement.get("Description", "").lower()
            
            # If the announcement mentions "today", use the sent date
            if "today" in title or "today" in description:
                return sent_datetime.isoformat()
                
            # If it mentions "tomorrow", add one day
            if "tomorrow" in title or "tomorrow" in description:
                event_date = sent_datetime + timedelta(days=1)
                return event_date.isoformat()
                
            # Otherwise, don't use SentTime as the event date
            return None
        except Exception as e:
            logger.warning(f"Error parsing SentTime '{sent_time}': {str(e)}")
            return None
    
    @classmethod
    def _extract_from_event_date_field(cls, announcement: Dict[str, Any]) -> Optional[str]:
        """
        Extract date from a dedicated EventDate field if it exists.
        
        Args:
            announcement: Announcement data dictionary
            
        Returns:
            ISO format date string or None
        """
        # Check for various possible event date field names
        event_date_field_names = ["EventDate", "Event Date", "Date", "DueDate", "Due Date", "Deadline"]
        
        for field_name in event_date_field_names:
            event_date = announcement.get(field_name)
            if event_date:
                try:
                    # Parse the event date
                    event_datetime = dateutil.parser.parse(event_date)
                    
                    # Ensure timezone awareness
                    if event_datetime.tzinfo is None:
                        event_datetime = event_datetime.replace(tzinfo=dateutil.tz.UTC)
                        
                    return event_datetime.isoformat()
                except Exception as e:
                    logger.warning(f"Error parsing EventDate '{event_date}': {str(e)}")
                    continue
                    
        return None
    
    @classmethod
    def _extract_date_from_text(cls, text: str, current_date: datetime, 
                              timezone: Optional[str] = None) -> Optional[str]:
        """
        Extract date from text content using regex patterns.
        
        Args:
            text: Text to extract date from
            current_date: Current date for reference
            timezone: Timezone for date interpretation
            
        Returns:
            ISO format date string or None
        """
        if not text:
            return None
            
        # Extract date mentions
        date_mentions = []
        for pattern in cls.DATE_PATTERNS:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                date_mentions.append(match.group(1))
                
        # Extract time mentions
        time_mentions = []
        for pattern in cls.TIME_PATTERNS:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                time_mentions.append(match.group(1))
                
        # If we found date mentions, try to parse them
        if date_mentions:
            # Try each date mention
            for date_mention in date_mentions:
                try:
                    # Handle special cases
                    if date_mention.lower() == "today":
                        return current_date.isoformat()
                    elif date_mention.lower() == "tomorrow":
                        tomorrow = current_date + timedelta(days=1)
                        return tomorrow.isoformat()
                    elif date_mention.lower() in ["tonight", "this evening"]:
                        # Set time to 7pm for "tonight"
                        evening = current_date.replace(hour=19, minute=0, second=0, microsecond=0)
                        return evening.isoformat()
                        
                    # Handle day of week mentions
                    days_of_week = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
                    day_mention_lower = date_mention.lower()
                    
                    for i, day in enumerate(days_of_week):
                        if day in day_mention_lower:
                            # Calculate days until the next occurrence of this day
                            current_weekday = current_date.weekday()
                            days_until = (i - current_weekday) % 7
                            
                            # If it's "next" day, add 7 more days
                            if "next" in day_mention_lower and days_until == 0:
                                days_until = 7
                                
                            # Calculate the date
                            target_date = current_date + timedelta(days=days_until)
                            
                            # If we also have a time mention, combine them
                            if time_mentions:
                                time_str = time_mentions[0]
                                combined_str = f"{target_date.strftime('%Y-%m-%d')} {time_str}"
                                try:
                                    combined_date = dateutil.parser.parse(combined_str)
                                    if combined_date.tzinfo is None:
                                        combined_date = combined_date.replace(tzinfo=dateutil.tz.gettz(timezone) if timezone else dateutil.tz.UTC)
                                    return combined_date.isoformat()
                                except Exception:
                                    # If combining fails, just return the date
                                    return target_date.isoformat()
                            
                            return target_date.isoformat()
                    
                    # Try to parse the date mention directly
                    parsed_date = dateutil.parser.parse(date_mention, fuzzy=True)
                    
                    # If year is not specified, use current year
                    if parsed_date.year < 100:  # Likely a 2-digit year
                        parsed_date = parsed_date.replace(year=current_date.year)
                    elif parsed_date.year == 1900:  # dateutil default when no year specified
                        parsed_date = parsed_date.replace(year=current_date.year)
                        
                    # Ensure the date is in the future
                    if parsed_date.date() < current_date.date():
                        # If it's in the past, it might be for next year
                        if parsed_date.month < current_date.month or (parsed_date.month == current_date.month and parsed_date.day < current_date.day):
                            parsed_date = parsed_date.replace(year=current_date.year + 1)
                    
                    # If we also have a time mention, combine them
                    if time_mentions:
                        time_str = time_mentions[0]
                        combined_str = f"{parsed_date.strftime('%Y-%m-%d')} {time_str}"
                        try:
                            combined_date = dateutil.parser.parse(combined_str)
                            if combined_date.tzinfo is None:
                                combined_date = combined_date.replace(tzinfo=dateutil.tz.gettz(timezone) if timezone else dateutil.tz.UTC)
                            return combined_date.isoformat()
                        except Exception:
                            # If combining fails, just return the date
                            if parsed_date.tzinfo is None:
                                parsed_date = parsed_date.replace(tzinfo=dateutil.tz.gettz(timezone) if timezone else dateutil.tz.UTC)
                            return parsed_date.isoformat()
                    
                    # Ensure timezone awareness
                    if parsed_date.tzinfo is None:
                        parsed_date = parsed_date.replace(tzinfo=dateutil.tz.gettz(timezone) if timezone else dateutil.tz.UTC)
                        
                    return parsed_date.isoformat()
                except Exception as e:
                    logger.warning(f"Error parsing date mention '{date_mention}': {str(e)}")
                    continue
        
        return None

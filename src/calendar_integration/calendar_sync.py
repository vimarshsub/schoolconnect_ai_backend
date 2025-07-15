"""
Calendar synchronization for event integration.

This module provides functionality to create and manage Google Calendar events
based on extracted event details from announcements.
"""

import logging
import re
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List

from .config import (
    REMINDER_DAYS_BEFORE, 
    DEFAULT_EVENT_TYPE, 
    DEFAULT_EVENT_START_TIME, 
    DEFAULT_EVENT_DURATION_HOURS
)
from .utils import format_event_description
from ..ai_analysis.tools.google_calendar_tool import GoogleCalendarTool

class CalendarSync:
    """
    Syncs extracted event details with Google Calendar.
    """
    
    def __init__(self, calendar_tool=None, logger=None):
        """
        Initialize the CalendarSync.
        
        Args:
            calendar_tool: Google Calendar tool for API calls
            logger: Logger instance
        """
        self.calendar_tool = calendar_tool or GoogleCalendarTool()
        self.logger = logger or logging.getLogger(__name__)
        
    def create_calendar_events(self, event_details: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Create Google Calendar events from extracted event details.
        
        Args:
            event_details: Dict with extracted event details
            
        Returns:
            Dict with created event IDs or None if creation failed
        """
        try:
            self.logger.info(f"Creating calendar events for: {event_details.get('EVENT')}")
            
            # Create main event
            main_event_result = self._create_main_event_with_status(event_details)
            if not main_event_result['success']:
                return None
                
            result = {
                'main_event_id': main_event_result['event_id'],
                'reminder_event_id': None
            }
            
            # Create reminder event if supplies are needed
            if (event_details.get('SUPPLIES NEEDED') and 
                event_details.get('SUPPLIES NEEDED') != 'None' and
                event_details.get('REMINDER DATE') and 
                event_details.get('REMINDER DATE') not in ['N/A', 'Unknown']):
                
                reminder_result = self._create_reminder_event_with_status(event_details)
                result['reminder_event_id'] = reminder_result['event_id'] if reminder_result['success'] else None
                
            return result
            
        except Exception as e:
            self.logger.error(f"Error creating calendar events: {str(e)}", exc_info=True)
            return None
            
    def _should_be_all_day_event(self, event_details: Dict[str, Any]) -> bool:
        """
        Determine if an event should be created as all-day or timed.
        
        Args:
            event_details: Dict with extracted event details
            
        Returns:
            bool: True if event should be all-day, False if timed
        """
        # Check if event details contain specific time information
        event_title = event_details.get('EVENT', '').lower()
        event_description = str(event_details.get('description', '')).lower()
        
        # Look for time indicators in the event title or description
        time_patterns = [
            r'\b\d{1,2}:\d{2}\s*(am|pm|a\.m\.|p\.m\.)\b',  # 9:00 AM, 2:30 PM
            r'\b\d{1,2}\s*(am|pm|a\.m\.|p\.m\.)\b',        # 9 AM, 2 PM
            r'\b(morning|afternoon|evening|noon)\b',        # morning, afternoon, etc.
            r'\b(breakfast|lunch|dinner)\b',                # meal times
        ]
        
        combined_text = f"{event_title} {event_description}"
        
        for pattern in time_patterns:
            if re.search(pattern, combined_text, re.IGNORECASE):
                return False  # Has specific time, should be timed event
        
        # Default to configuration setting
        return DEFAULT_EVENT_TYPE == "all_day"
            
    def _create_main_event_with_status(self, event_details: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create the main calendar event and return success status.
        
        Args:
            event_details: Dict with extracted event details
            
        Returns:
            Dict with 'success' (bool) and 'event_id' (str or None)
        """
        try:
            event_date = event_details.get('DATE OF EVENT')
            if not event_date or event_date == 'Unknown':
                return {'success': False, 'event_id': None}
                
            # Convert date to ISO format
            date_obj = datetime.strptime(event_date, '%Y-%m-%d')
            
            # Determine if this should be an all-day event
            is_all_day = self._should_be_all_day_event(event_details)
            
            # Create event description
            description = format_event_description(event_details)
            
            if is_all_day:
                # Create all-day event (no specific time)
                start_date = date_obj.strftime('%Y-%m-%d')
                
                result = self.calendar_tool.create_event(
                    title=event_details.get('EVENT'),
                    start_time=start_date,
                    end_time=None,  # Will default to next day for all-day events
                    description=description,
                    reminder_minutes=1440,  # 24 hours before
                    all_day=True
                )
            else:
                # Create timed event with default time
                start_time = date_obj.strftime(f'%Y-%m-%dT{DEFAULT_EVENT_START_TIME}:00')
                end_dt = date_obj.replace(hour=int(DEFAULT_EVENT_START_TIME.split(':')[0]), minute=int(DEFAULT_EVENT_START_TIME.split(':')[1])) + timedelta(hours=DEFAULT_EVENT_DURATION_HOURS)
                end_time = end_dt.strftime('%Y-%m-%dT%H:%M:00')
                
                result = self.calendar_tool.create_event(
                    title=event_details.get('EVENT'),
                    start_time=start_time,
                    end_time=end_time,
                    description=description,
                    reminder_minutes=1440,  # 24 hours before
                    all_day=False
                )            
            # Check if the operation was successful
            if isinstance(result, dict) and result.get('success', False):
                # Event was successfully created
                event_id = self._extract_event_id_from_result(result)
                self.logger.info(f"Created main calendar event with ID: {event_id}")
                return {'success': True, 'event_id': event_id}
            elif isinstance(result, dict) and not result.get('success', False):
                # Event creation failed
                self.logger.error(f"Calendar tool failed to create event: {result.get('message', 'Unknown error')}")
                return {'success': False, 'event_id': None}
            else:
                # Legacy string response - assume success if no error message
                event_id = self._extract_event_id_from_result(result)
                if "Error" in str(result) or "Failed" in str(result):
                    self.logger.error(f"Calendar tool failed to create event: {result}")
                    return {'success': False, 'event_id': None}
                else:
                    self.logger.info(f"Created main calendar event with ID: {event_id}")
                    return {'success': True, 'event_id': event_id}
            
        except Exception as e:
            self.logger.error(f"Error creating main event: {str(e)}", exc_info=True)
            return {'success': False, 'event_id': None}
            
    def _create_reminder_event_with_status(self, event_details: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create reminder calendar event and return success status.
        
        Args:
            event_details: Dict with extracted event details
            
        Returns:
            Dict with 'success' (bool) and 'event_id' (str or None)
        """
        try:
            reminder_date = event_details.get('REMINDER DATE')
            if not reminder_date or reminder_date in ['N/A', 'Unknown']:
                return {'success': False, 'event_id': None}
                
            # Convert date to ISO format
            date_obj = datetime.strptime(reminder_date, '%Y-%m-%d')
            
            # Reminders are typically all-day events since they're just reminders
            # But we can still check if there's specific time information
            is_all_day = self._should_be_all_day_event(event_details)
            
            # Create reminder title and description
            title = f"REMINDER: {event_details.get('EVENT')} - Supplies Due Soon"
            description = f"This is a reminder to prepare the following supplies for {event_details.get('EVENT')}:\n\n"
            description += f"Supplies needed: {event_details.get('SUPPLIES NEEDED')}\n"
            description += f"Due date: {event_details.get('SUPPLIES DUE DATE')}\n"
            description += f"Event date: {event_details.get('DATE OF EVENT')}"
            
            if is_all_day:
                # Create all-day reminder event (most common)
                start_date = date_obj.strftime('%Y-%m-%d')
                
                result = self.calendar_tool.create_event(
                    title=title,
                    start_time=start_date,
                    end_time=None,  # Will default to next day for all-day events
                    description=description,
                    reminder_minutes=1440,  # 24 hours before
                    all_day=True
                )
            else:
                # Create timed reminder event
                start_time = date_obj.strftime(f'%Y-%m-%dT{DEFAULT_EVENT_START_TIME}:00')
                end_dt = date_obj.replace(hour=int(DEFAULT_EVENT_START_TIME.split(':')[0]), minute=int(DEFAULT_EVENT_START_TIME.split(':')[1])) + timedelta(hours=DEFAULT_EVENT_DURATION_HOURS)
                end_time = end_dt.strftime('%Y-%m-%dT%H:%M:00')
                
                result = self.calendar_tool.create_event(
                    title=title,
                    start_time=start_time,
                    end_time=end_time,
                    description=description,
                    reminder_minutes=1440,  # 24 hours before
                    all_day=False
                )
            
            # Check if the operation was successful
            if isinstance(result, dict) and result.get('success', False):
                # Reminder was successfully created
                event_id = self._extract_event_id_from_result(result)
                self.logger.info(f"Created reminder calendar event with ID: {event_id}")
                return {'success': True, 'event_id': event_id}
            elif isinstance(result, dict) and not result.get('success', False):
                # Reminder creation failed
                self.logger.error(f"Calendar tool failed to create reminder: {result.get('message', 'Unknown error')}")
                return {'success': False, 'event_id': None}
            else:
                # Legacy string response - assume success if no error message
                event_id = self._extract_event_id_from_result(result)
                if "Error" in str(result) or "Failed" in str(result):
                    self.logger.error(f"Calendar tool failed to create reminder: {result}")
                    return {'success': False, 'event_id': None}
                else:
                    self.logger.info(f"Created reminder calendar event with ID: {event_id}")
                    return {'success': True, 'event_id': event_id}
            
        except Exception as e:
            self.logger.error(f"Error creating reminder event: {str(e)}", exc_info=True)
            return {'success': False, 'event_id': None}
            
    def _create_main_event(self, event_details: Dict[str, Any]) -> Optional[str]:
        """
        Create the main calendar event.
        
        Args:
            event_details: Dict with extracted event details
            
        Returns:
            Event ID or None if creation failed
        """
        try:
            event_date = event_details.get('DATE OF EVENT')
            if not event_date or event_date == 'Unknown':
                return None
                
            # Convert date to ISO format
            date_obj = datetime.strptime(event_date, '%Y-%m-%d')
            start_time = date_obj.strftime('%Y-%m-%dT09:00:00')  # Default to 9 AM
            end_time = date_obj.strftime('%Y-%m-%dT10:00:00')    # Default to 1 hour duration
            
            # Create event description
            description = format_event_description(event_details)
            
            # Create the event
            result = self.calendar_tool.create_event(
                title=event_details.get('EVENT'),
                start_time=start_time,
                end_time=end_time,
                description=description,
                reminder_minutes=1440  # 24 hours before
            )
            
            # Check if the operation was successful
            if isinstance(result, dict) and not result.get('success', False):
                self.logger.error(f"Calendar tool failed to create event: {result.get('message', 'Unknown error')}")
                return None
            
            # Extract event ID from result
            event_id = self._extract_event_id_from_result(result)
            
            self.logger.info(f"Created main calendar event with ID: {event_id}")
            return event_id
            
        except Exception as e:
            self.logger.error(f"Error creating main event: {str(e)}", exc_info=True)
            return None
            
    def _create_reminder_event(self, event_details: Dict[str, Any]) -> Optional[str]:
        """
        Create reminder calendar event.
        
        Args:
            event_details: Dict with extracted event details
            
        Returns:
            Event ID or None if creation failed
        """
        try:
            reminder_date = event_details.get('REMINDER DATE')
            if not reminder_date or reminder_date in ['N/A', 'Unknown']:
                return None
                
            # Convert date to ISO format
            date_obj = datetime.strptime(reminder_date, '%Y-%m-%d')
            start_time = date_obj.strftime('%Y-%m-%dT09:00:00')  # Default to 9 AM
            
            # Create reminder title and description
            title = f"REMINDER: {event_details.get('EVENT')} - Supplies Due Soon"
            description = f"This is a reminder to prepare the following supplies for {event_details.get('EVENT')}:\n\n"
            description += f"Supplies needed: {event_details.get('SUPPLIES NEEDED')}\n"
            description += f"Due date: {event_details.get('SUPPLIES DUE DATE')}\n"
            description += f"Event date: {event_details.get('DATE OF EVENT')}"
            
            # Create the reminder
            result = self.calendar_tool.create_reminder(
                title=title,
                due_date=start_time,
                description=description
            )
            
            # Check if the operation was successful
            if isinstance(result, dict) and not result.get('success', False):
                self.logger.error(f"Calendar tool failed to create reminder: {result.get('message', 'Unknown error')}")
                return None
            
            # Extract event ID from result
            reminder_id = self._extract_event_id_from_result(result)
            
            self.logger.info(f"Created reminder calendar event with ID: {reminder_id}")
            return reminder_id
            
        except Exception as e:
            self.logger.error(f"Error creating reminder event: {str(e)}", exc_info=True)
            return None
            
    def _extract_event_id_from_result(self, result: Any) -> Optional[str]:
        """
        Extract event ID from calendar tool result.
        
        Args:
            result: Result from calendar tool
            
        Returns:
            Event ID or None if extraction failed
        """
        # Handle new dictionary format from GoogleCalendarTool
        if isinstance(result, dict):
            if result.get('success') and result.get('event_id'):
                return result['event_id']
            elif 'id' in result:
                # Fallback for other dictionary formats
                return result['id']
        
        # Handle legacy string format
        elif isinstance(result, str) and "Successfully created" in result:
            # Example: extract ID from "Successfully created calendar event: My Event with ID: 123456"
            match = re.search(r"ID: ([a-zA-Z0-9_-]+)", result)
            if match:
                return match.group(1)
        
        return None

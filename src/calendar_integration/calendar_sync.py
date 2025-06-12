"""
Calendar synchronization for event integration.

This module provides functionality to create and manage Google Calendar events
based on extracted event details from announcements.
"""

import logging
import re
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List

from .config import REMINDER_DAYS_BEFORE
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
            main_event_id = self._create_main_event(event_details)
            if not main_event_id:
                return None
                
            result = {
                'main_event_id': main_event_id,
                'reminder_event_id': None
            }
            
            # Create reminder event if supplies are needed
            if (event_details.get('SUPPLIES NEEDED') and 
                event_details.get('SUPPLIES NEEDED') != 'None' and
                event_details.get('REMINDER DATE') and 
                event_details.get('REMINDER DATE') not in ['N/A', 'Unknown']):
                
                reminder_event_id = self._create_reminder_event(event_details)
                result['reminder_event_id'] = reminder_event_id
                
            return result
            
        except Exception as e:
            self.logger.error(f"Error creating calendar events: {str(e)}", exc_info=True)
            return None
            
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
        # This implementation depends on how your GoogleCalendarTool returns results
        if isinstance(result, str) and "Successfully created" in result:
            # Example: extract ID from "Successfully created calendar event: My Event with ID: 123456"
            match = re.search(r"ID: ([a-zA-Z0-9_-]+)", result)
            if match:
                return match.group(1)
        elif isinstance(result, dict) and 'id' in result:
            # If the tool returns a dictionary with an ID field
            return result['id']
        return None

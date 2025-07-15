"""
Google Calendar integration for creating events based on document analysis.
"""

import os
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json
import requests

from src.core.config import get_settings

logger = logging.getLogger("schoolconnect_ai")

class GoogleCalendarTool:
    """Tool for creating Google Calendar events."""
    
    def __init__(self):
        """Initialize the Google Calendar tool."""
        settings = get_settings()
        self.credentials_json = settings.GOOGLE_CALENDAR_CREDENTIALS
        
        # API endpoints from the legacy implementation
        self.get_url = "https://agentichome.app.n8n.cloud/webhook/3c4e4c24-635b-4776-aec6-afb141cfab5c"
        self.post_url = "https://agentichome.app.n8n.cloud/webhook/615f7ae5-4d59-4555-aa7c-228feef7d013"
        
        logger.info("Initialized Google Calendar tool with n8n webhook integration")
    
    def search_events(self, query=None, start_date=None, end_date=None, max_results=10):
        """
        Search for events in Google Calendar.
        
        Args:
            query (str, optional): Search term to find events
            start_date (str, optional): Start date in 'YYYY-MM-DD' format
            end_date (str, optional): End date in 'YYYY-MM-DD' format
            max_results (int, optional): Maximum number of results to return
            
        Returns:
            dict: Dictionary containing the search results or error message
        """
        try:
            # Prepare request data
            params = {
                "action": "search_events",
                "max_results": max_results
            }
            
            if query:
                params["query"] = query
            
            if start_date:
                params["start_date"] = start_date
                
            if end_date:
                params["end_date"] = end_date
            
            logger.info(f"Searching calendar events with params: {params}")
            
            # Send GET request
            response = requests.get(self.get_url, params=params)
            
            # Check if request was successful
            if response.status_code == 200:
                result = response.json()
                logger.info(f"Successfully searched events, found {len(result.get('events', []))} results")
                return result
            else:
                error_msg = f"Failed to search events. Status code: {response.status_code}, Response: {response.text}"
                logger.error(error_msg)
                return {
                    "error": f"Failed to search events. Status code: {response.status_code}",
                    "message": response.text
                }
                
        except Exception as e:
            error_msg = f"Error searching calendar events: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {
                "error": "Failed to search events",
                "message": str(e)
            }
    
    def create_event(self, title, start_time, end_time=None, description=None, location=None, attendees=None, reminder_minutes=None, all_day=False):
        """
        Create a new event in Google Calendar.
        
        Args:
            title (str): Title of the event
            start_time (str): Start date and time in ISO format (YYYY-MM-DDTHH:MM:SS) or date format (YYYY-MM-DD) for all-day events
            end_time (str, optional): End date and time in ISO format or date format for all-day events
            description (str, optional): Description of the event
            location (str, optional): Location of the event
            attendees (list, optional): List of email addresses of attendees
            reminder_minutes (int, optional): Reminder time in minutes before the event
            all_day (bool, optional): Whether this is an all-day event
            
        Returns:
            str: Success message or error message
        """
        try:
            # Validate inputs
            if not title:
                error_msg = "Error: Event title is required"
                logger.error(error_msg)
                return {'success': False, 'message': error_msg, 'event_id': None}
            
            if all_day:
                # For all-day events, use date format (YYYY-MM-DD)
                if not end_time:
                    # For all-day events, end date should be the next day
                    try:
                        start_date = datetime.strptime(start_time, '%Y-%m-%d')
                        end_date = start_date + timedelta(days=1)
                        end_time = end_date.strftime('%Y-%m-%d')
                    except ValueError:
                        error_msg = "Error: Invalid start_time format for all-day event. Please use date format (YYYY-MM-DD)"
                        logger.error(error_msg)
                        return {'success': False, 'message': error_msg, 'event_id': None}
                
                # Prepare request data for all-day event
                data = {
                    "action": "create_event",
                    "title": title,
                    "start_date": start_time,  # Use start_date for all-day events
                    "end_date": end_time,      # Use end_date for all-day events
                    "all_day": True
                }
            else:
                # For timed events, use datetime format
                # Set end time to 1 hour after start time if not provided
                if not end_time:
                    try:
                        start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                        end_dt = start_dt + timedelta(hours=1)
                        end_time = end_dt.isoformat().replace('+00:00', 'Z')
                    except ValueError:
                        error_msg = "Error: Invalid start_time format. Please use ISO format (YYYY-MM-DDTHH:MM:SS)"
                        logger.error(error_msg)
                        return {'success': False, 'message': error_msg, 'event_id': None}
                
                # Prepare request data for timed event
                data = {
                    "action": "create_event",
                    "title": title,
                    "start_datetime": start_time,
                    "end_datetime": end_time,
                    "all_day": False
                }
            
            if description:
                data["description"] = description
                
            if location:
                data["location"] = location
                
            if attendees:
                data["attendees"] = attendees
                
            if reminder_minutes:
                data["reminder_minutes"] = reminder_minutes
            
            logger.info(f"Creating calendar event: {json.dumps(data)}")
            
            # Send POST request
            headers = {"Content-Type": "application/json"}
            response = requests.post(self.post_url, json=data, headers=headers)
            
            # Check if request was successful
            if response.status_code == 200:
                result = response.json()
                logger.info(f"Successfully created calendar event: {title}")
                
                # Try to extract event ID from the response
                event_id = None
                if isinstance(result, dict):
                    # Check common fields where event ID might be returned
                    event_id = result.get('id') or result.get('event_id') or result.get('eventId')
                    
                if event_id:
                    return {
                        'success': True,
                        'message': f"Successfully created calendar event: {title} from {start_time} to {end_time}",
                        'event_id': event_id
                    }
                else:
                    # If no event ID found, return success message with indication
                    return {
                        'success': True,
                        'message': f"Successfully created calendar event: {title} from {start_time} to {end_time}",
                        'event_id': None
                    }
            else:
                error_msg = f"Failed to create event. Status code: {response.status_code}, Response: {response.text}"
                logger.error(error_msg)
                return {'success': False, 'message': error_msg, 'event_id': None}
                
        except Exception as e:
            error_msg = f"Error creating calendar event: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {'success': False, 'message': error_msg, 'event_id': None}
    
    def create_reminder(self, title, due_date, description=None):
        """
        Create a new reminder in Google Calendar.
        
        Args:
            title (str): Title of the reminder
            due_date (str): Due date and time in ISO format (YYYY-MM-DDTHH:MM:SS)
            description (str, optional): Description of the reminder
            
        Returns:
            str: Success message or error message
        """
        try:
            # Validate inputs
            if not title:
                error_msg = "Error: Reminder title is required"
                logger.error(error_msg)
                return error_msg
            
            try:
                datetime.fromisoformat(due_date.replace('Z', '+00:00'))
            except ValueError:
                error_msg = "Error: Invalid due_date format. Please use ISO format (YYYY-MM-DDTHH:MM:SS)"
                logger.error(error_msg)
                return error_msg
            
            # Prepare request data
            data = {
                "action": "create_reminder",
                "title": title,
                "due_date": due_date
            }
            
            if description:
                data["description"] = description
            
            logger.info(f"Creating calendar reminder: {json.dumps(data)}")
            
            # Send POST request
            headers = {"Content-Type": "application/json"}
            response = requests.post(self.post_url, json=data, headers=headers)
            
            # Check if request was successful
            if response.status_code == 200:
                result = response.json()
                logger.info(f"Successfully created calendar reminder: {title}")
                
                # Try to extract event ID from the response
                event_id = None
                if isinstance(result, dict):
                    # Check common fields where event ID might be returned
                    event_id = result.get('id') or result.get('event_id') or result.get('eventId')
                    
                if event_id:
                    return {
                        'success': True,
                        'message': f"Successfully created calendar reminder: {title} due on {due_date}",
                        'event_id': event_id
                    }
                else:
                    # If no event ID found, return success message with indication
                    return {
                        'success': True,
                        'message': f"Successfully created calendar reminder: {title} due on {due_date}",
                        'event_id': None
                    }
            else:
                error_msg = f"Failed to create reminder. Status code: {response.status_code}, Response: {response.text}"
                logger.error(error_msg)
                return {'success': False, 'message': error_msg, 'event_id': None}
                
        except Exception as e:
            error_msg = f"Error creating calendar reminder: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {'success': False, 'message': error_msg, 'event_id': None}

    def delete_event(self, event_id):
        """
        Delete an event from Google Calendar.
        
        Args:
            event_id (str): ID of the event to delete
            
        Returns:
            str: Success message or error message
        """
        try:
            # Validate inputs
            if not event_id:
                error_msg = "Error: Event ID is required"
                logger.error(error_msg)
                return error_msg
            
            # Prepare request data
            data = {
                "action": "delete_event",
                "event_id": event_id
            }
            
            logger.info(f"Deleting calendar event with ID: {event_id}")
            
            # Send POST request
            headers = {"Content-Type": "application/json"}
            response = requests.post(self.post_url, json=data, headers=headers)
            
            # Check if request was successful
            if response.status_code == 200:
                result = response.json()
                logger.info(f"Successfully deleted calendar event with ID: {event_id}")
                return f"Successfully deleted calendar event with ID: {event_id}"
            else:
                error_msg = f"Failed to delete event. Status code: {response.status_code}, Response: {response.text}"
                logger.error(error_msg)
                return error_msg
                
        except Exception as e:
            error_msg = f"Error deleting calendar event: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return error_msg

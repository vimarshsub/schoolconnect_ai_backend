"""
Core agent logic for AI-powered announcement analysis.
"""

import os
import logging
from typing import Dict, List, Any, Optional
from langchain.chat_models import ChatOpenAI
from langchain.agents import initialize_agent, AgentType
from langchain.tools import Tool, StructuredTool
from pydantic.v1 import BaseModel, Field  # Explicitly use pydantic.v1 to match LangChain
from langchain.schema import SystemMessage

from src.core.config import get_settings
from src.ai_analysis.tools.airtable_tool import AirtableTool
from src.ai_analysis.tools.openai_tool import OpenAIDocumentAnalysisTool
from src.ai_analysis.tools.google_calendar_tool import GoogleCalendarTool
from src.ai_analysis.tools.date_utils_tool import DateUtilsTool

logger = logging.getLogger("schoolconnect_ai")

# Memory key for chat history
MEMORY_KEY = "chat_history"

# Default timezone (can be overridden by user settings)
DEFAULT_TIMEZONE = "America/New_York"

# Define Pydantic models for structured tool inputs
class CalendarEventInput(BaseModel):
    title: str = Field(description="Title of the event")
    start_datetime: str = Field(description="Start date and time in ISO format (YYYY-MM-DDTHH:MM:SS)")
    end_datetime: Optional[str] = Field(None, description="End date and time in ISO format (YYYY-MM-DDTHH:MM:SS)")
    description: Optional[str] = Field(None, description="Description of the event")
    location: Optional[str] = Field(None, description="Location of the event")
    attendees: Optional[str] = Field(None, description="Comma-separated list of attendee email addresses")
    reminder_minutes: Optional[int] = Field(None, description="Reminder time in minutes before the event")
    timezone: Optional[str] = Field(None, description="Timezone for the event (e.g., 'America/New_York', 'UTC')")

class CalendarReminderInput(BaseModel):
    title: str = Field(description="Title of the reminder")
    due_date: str = Field(description="Due date in ISO format (YYYY-MM-DDTHH:MM:SS)")
    description: Optional[str] = Field(None, description="Description of the reminder")
    timezone: Optional[str] = Field(None, description="Timezone for the reminder (e.g., 'America/New_York', 'UTC')")

class CalendarSearchInput(BaseModel):
    query: Optional[str] = Field(None, description="Search term to find events")
    start_date: Optional[str] = Field(None, description="Start date in 'YYYY-MM-DD' format")
    end_date: Optional[str] = Field(None, description="End date in 'YYYY-MM-DD' format")
    max_results: Optional[int] = Field(10, description="Maximum number of results to return")
    timezone: Optional[str] = Field(None, description="Timezone for date interpretation (e.g., 'America/New_York', 'UTC')")

class CalendarDeleteInput(BaseModel):
    event_id: str = Field(description="ID of the event to delete")

class DateRangeInput(BaseModel):
    period: str = Field(description="Time period ('today', 'yesterday', 'this_week', 'last_week', 'this_month', 'last_month', 'next_month', 'this_year', 'last_year')")
    timezone: Optional[str] = Field(None, description="Timezone for date calculations (e.g., 'America/New_York', 'UTC')")

class RelativeDateInput(BaseModel):
    reference: str = Field(description="Reference point ('today', 'tomorrow', 'yesterday', 'start_of_week', 'end_of_week', 'start_of_month', 'end_of_month')")
    offset_days: Optional[int] = Field(0, description="Number of days to offset (can be negative)")
    timezone: Optional[str] = Field(None, description="Timezone for date calculations (e.g., 'America/New_York', 'UTC')")

class GetCurrentDateInput(BaseModel):
    timezone: Optional[str] = Field(None, description="Timezone to get current date in (e.g., 'America/New_York', 'UTC')")

class TimezoneInfoInput(BaseModel):
    timezone: Optional[str] = Field(None, description="Timezone to get information about (e.g., 'America/New_York', 'UTC')")

# Empty schema for tools that take no arguments
class EmptySchema(BaseModel):
    pass

class AgentManager:
    """Manager for AI agent setup and execution."""
    
    def __init__(self, user_timezone: Optional[str] = None):
        """
        Initialize the agent manager.
        
        Args:
            user_timezone: Optional timezone to use for date calculations
        """
        settings = get_settings()
        self.openai_api_key = settings.OPENAI_API_KEY
        self.model = settings.OPENAI_MODEL
        
        # Initialize date utils with user timezone if provided
        self.user_timezone = user_timezone or DEFAULT_TIMEZONE
        self.date_utils = DateUtilsTool(default_timezone=self.user_timezone)
        
        # Initialize other tools
        self.airtable_tool = AirtableTool()
        self.openai_analysis_tool = OpenAIDocumentAnalysisTool()
        self.calendar_tool = GoogleCalendarTool()
        
        # Set up agent
        self.agent_executor = self._setup_agent()
    
    def _create_calendar_event_wrapper(self, title: str, start_datetime: str, 
                              end_datetime: Optional[str] = None, 
                              description: Optional[str] = None,
                              location: Optional[str] = None,
                              attendees: Optional[str] = None,
                              reminder_minutes: Optional[int] = None,
                              timezone: Optional[str] = None) -> str:
        """
        Wrapper for calendar event creation that handles multiple arguments.
        
        Args:
            title: Title of the event
            start_datetime: Start time in ISO format (YYYY-MM-DDTHH:MM:SS)
            end_datetime: End time in ISO format (YYYY-MM-DDTHH:MM:SS)
            description: Description of the event
            location: Location of the event
            attendees: Comma-separated list of attendee email addresses
            reminder_minutes: Reminder time in minutes before the event
            timezone: Timezone for date interpretation
            
        Returns:
            Success or error message
        """
        # Use provided timezone or fall back to user's default
        tz = timezone or self.user_timezone
        
        # Normalize dates to ensure they're in the future and properly formatted
        normalized_start = self.date_utils.normalize_date_string(start_datetime, timezone=tz)
        if not normalized_start:
            return f"Error: Could not parse start date '{start_datetime}'. Please provide a valid date."
        
        normalized_end = None
        if end_datetime:
            normalized_end = self.date_utils.normalize_date_string(end_datetime, timezone=tz)
            if not normalized_end:
                return f"Error: Could not parse end date '{end_datetime}'. Please provide a valid date."
        
        # Convert attendees from string to list if provided
        attendees_list = None
        if attendees:
            attendees_list = [email.strip() for email in attendees.split(',')]
        
        return self.calendar_tool.create_event(
            title=title,
            start_time=normalized_start,
            end_time=normalized_end,
            description=description,
            location=location,
            attendees=attendees_list,
            reminder_minutes=reminder_minutes
        )
    
    def _create_calendar_reminder_wrapper(self, title: str, due_date: str, 
                                 description: Optional[str] = None,
                                 timezone: Optional[str] = None) -> str:
        """
        Wrapper for calendar reminder creation that handles multiple arguments.
        
        Args:
            title: Title of the reminder
            due_date: Due date in ISO format (YYYY-MM-DDTHH:MM:SS)
            description: Description of the reminder
            timezone: Timezone for date interpretation
            
        Returns:
            Success or error message
        """
        # Use provided timezone or fall back to user's default
        tz = timezone or self.user_timezone
        
        # Normalize date to ensure it's in the future and properly formatted
        normalized_date = self.date_utils.normalize_date_string(due_date, timezone=tz)
        if not normalized_date:
            return f"Error: Could not parse due date '{due_date}'. Please provide a valid date."
        
        return self.calendar_tool.create_reminder(
            title=title,
            due_date=normalized_date,
            description=description
        )
    
    def _search_calendar_events_wrapper(self, query: Optional[str] = None, 
                               start_date: Optional[str] = None,
                               end_date: Optional[str] = None,
                               max_results: int = 10,
                               timezone: Optional[str] = None) -> Dict:
        """
        Wrapper for calendar event search that handles multiple arguments.
        
        Args:
            query: Search term to find events
            start_date: Start date in 'YYYY-MM-DD' format
            end_date: End date in 'YYYY-MM-DD' format
            max_results: Maximum number of results to return
            timezone: Timezone for date interpretation
            
        Returns:
            Search results or error message
        """
        # Use provided timezone or fall back to user's default
        tz = timezone or self.user_timezone
        
        # Normalize dates if provided
        normalized_start = None
        if start_date:
            normalized_start = self.date_utils.normalize_date_string(start_date, timezone=tz)
            if not normalized_start:
                return f"Error: Could not parse start date '{start_date}'. Please provide a valid date."
        
        normalized_end = None
        if end_date:
            normalized_end = self.date_utils.normalize_date_string(end_date, timezone=tz)
            if not normalized_end:
                return f"Error: Could not parse end date '{end_date}'. Please provide a valid date."
        
        return self.calendar_tool.search_events(
            query=query,
            start_date=normalized_start,
            end_date=normalized_end,
            max_results=max_results
        )
    
    def _delete_calendar_event_wrapper(self, event_id: str) -> str:
        """
        Wrapper for calendar event deletion.
        
        Args:
            event_id: ID of the event to delete
            
        Returns:
            Success or error message
        """
        return self.calendar_tool.delete_event(event_id=event_id)
    
    def _get_current_date_wrapper(self, timezone: Optional[str] = None) -> str:
        """
        Get the current date and time in the specified timezone.
        
        Args:
            timezone: Timezone to get current date in
            
        Returns:
            Current date and time in ISO format
        """
        # Use provided timezone or fall back to user's default
        tz = timezone or self.user_timezone
        return self.date_utils.get_current_date(include_time=True, timezone=tz)
    
    def _get_date_range_wrapper(self, period: str, timezone: Optional[str] = None) -> Dict[str, Any]:
        """
        Get start and end dates for common time periods in the specified timezone.
        
        Args:
            period: Time period ('today', 'yesterday', 'this_week', etc.)
            timezone: Timezone for date calculations
            
        Returns:
            Dictionary with date range information
        """
        # Use provided timezone or fall back to user's default
        tz = timezone or self.user_timezone
        return self.date_utils.get_date_range(period, timezone=tz)
    
    def _get_relative_date_wrapper(self, reference: str, offset_days: int = 0, 
                                  timezone: Optional[str] = None) -> Dict[str, Any]:
        """
        Get a date relative to a reference point with an offset in the specified timezone.
        
        Args:
            reference: Reference point ('today', 'tomorrow', etc.)
            offset_days: Number of days to offset
            timezone: Timezone for date calculations
            
        Returns:
            Dictionary with date information
        """
        # Use provided timezone or fall back to user's default
        tz = timezone or self.user_timezone
        return self.date_utils.get_relative_date(reference, offset_days, timezone=tz)
    
    def _get_timezone_info_wrapper(self, timezone: Optional[str] = None) -> Dict[str, Any]:
        """
        Get information about a timezone, including current offset and time.
        
        Args:
            timezone: Timezone to get information about
            
        Returns:
            Dictionary with timezone information
        """
        # Use provided timezone or fall back to user's default
        tz = timezone or self.user_timezone
        return self.date_utils.get_timezone_offset(timezone=tz)
    
    def _get_available_timezones_wrapper(self) -> Dict[str, Any]:
        """
        Get a list of available timezones grouped by region.
        
        Returns:
            Dictionary with timezone information grouped by region
        """
        return self.date_utils.get_available_timezones()
    
    def _setup_agent(self):
        """
        Set up the LangChain agent with tools.
        
        Returns:
            Configured AgentExecutor
        """
        # Initialize LLM
        llm = ChatOpenAI(
            model=self.model,
            temperature=0,
            api_key=self.openai_api_key
        )
        
        # Define tools
        tools = [
            Tool(
                name="get_all_announcements",
                func=self.airtable_tool.get_all_announcements,
                description="Get all announcements from the Airtable database."
            ),
            Tool(
                name="search_announcements",
                func=self.airtable_tool.search_announcements,
                description="Search for announcements by text in the Title, Description, or Sender fields."
            ),
            Tool(
                name="search_announcements_by_sender",
                func=self.airtable_tool.search_announcements_by_sender,
                description="Search for announcements by sender name."
            ),
            Tool(
                name="filter_announcements_by_date",
                func=self.airtable_tool.filter_announcements_by_date,
                description="Filter announcements by date based on the SentTime field. Examples: 'in May', 'last week', 'this month', '2023-01-01'."
            ),
            Tool(
                name="get_attachment",
                func=self._get_and_download_attachment,
                description="Get an attachment from an announcement by ID, search term, or get the latest. Returns the local file path."
            ),
            Tool(
                name="analyze_document",
                func=self._analyze_document,
                description="Analyze a document (PDF) using OpenAI. Specify the analysis type: summarize, extract_action_items, sentiment, or custom."
            ),
            # Date utility tools with timezone support
            StructuredTool.from_function(
                func=self._get_current_date_wrapper,
                name="get_current_date",
                description=f"Get the current date and time in ISO format in the specified timezone (default: {self.user_timezone}). Use this to know the current date when creating events or reminders.",
                args_schema=GetCurrentDateInput
            ),
            StructuredTool.from_function(
                func=self._get_date_range_wrapper,
                name="get_date_range",
                description=f"Get start and end dates for common time periods like 'today', 'this_week', 'last_month', etc. in the specified timezone (default: {self.user_timezone}).",
                args_schema=DateRangeInput
            ),
            StructuredTool.from_function(
                func=self._get_relative_date_wrapper,
                name="get_relative_date",
                description=f"Get a date relative to a reference point with an offset in days in the specified timezone (default: {self.user_timezone}). For example, 'tomorrow' would be ('today', 1).",
                args_schema=RelativeDateInput
            ),
            StructuredTool.from_function(
                func=self._get_timezone_info_wrapper,
                name="get_timezone_info",
                description="Get information about a timezone, including current offset and time.",
                args_schema=TimezoneInfoInput
            ),
            StructuredTool.from_function(
                func=self._get_available_timezones_wrapper,
                name="get_available_timezones",
                description="Get a list of available timezones grouped by region.",
                args_schema=EmptySchema
            ),
            # Calendar tools with timezone support
            StructuredTool.from_function(
                func=self._create_calendar_event_wrapper,
                name="create_calendar_event",
                description=f"Creates a new event in Google Calendar with timezone support (default: {self.user_timezone}). You must specify the title and start time. Optionally specify end time, description, location, attendees, and reminder time.",
                args_schema=CalendarEventInput
            ),
            StructuredTool.from_function(
                func=self._search_calendar_events_wrapper,
                name="search_calendar_events",
                description=f"Searches for events in Google Calendar with timezone support (default: {self.user_timezone}). You can specify a search term, date range, and maximum number of results to return.",
                args_schema=CalendarSearchInput
            ),
            StructuredTool.from_function(
                func=self._create_calendar_reminder_wrapper,
                name="create_calendar_reminder",
                description=f"Creates a new reminder in Google Calendar with timezone support (default: {self.user_timezone}). You must specify the title and due date. Optionally specify a description.",
                args_schema=CalendarReminderInput
            ),
            StructuredTool.from_function(
                func=self._delete_calendar_event_wrapper,
                name="delete_calendar_event",
                description="Deletes an event from Google Calendar. You must specify the event ID.",
                args_schema=CalendarDeleteInput
            )
        ]
        
        # Create system message using the proper format
        system_message = SystemMessage(content=f"""You are a helpful assistant that can interact with Airtable, analyze documents, manage Google Calendar, and perform date calculations. 
                
The current year is 2025. Always use the current date tools to get accurate date information when working with calendar events or reminders.

Your default timezone is set to {self.user_timezone}. When users mention dates or times without specifying a timezone, assume they are referring to their local time in {self.user_timezone}.

When creating calendar events or reminders:
1. Always check the current date first using get_current_date
2. For relative dates like "tomorrow" or "next week", use get_relative_date
3. Ensure all dates are in the future and use the correct year (2025)
4. Format dates in ISO format (YYYY-MM-DDTHH:MM:SSZ)
5. Consider the user's timezone ({self.user_timezone}) when interpreting time references

For calendar-related tasks, help users create, find, and manage their events and reminders effectively. You can also provide date calculations and ranges when users need to know about specific time periods.

Always maintain context between conversation turns.""")
        
        # Create agent using the initialize_agent method with proper system message
        agent_executor = initialize_agent(
            tools=tools,
            llm=llm,
            agent=AgentType.OPENAI_FUNCTIONS,
            verbose=True,
            handle_parsing_errors=True,
            agent_kwargs={
                "system_message": system_message
            }
        )
        
        return agent_executor
    
    def _get_and_download_attachment(self, announcement_id: Optional[str] = None, 
                                    search_term: Optional[str] = None, 
                                    get_latest: bool = False) -> str:
        """
        Get and download an attachment from an announcement.
        
        Args:
            announcement_id: Airtable record ID
            search_term: Text to search for in Title or Description
            get_latest: Whether to get the latest announcement
            
        Returns:
            Local file path to the downloaded attachment
        """
        try:
            # Get attachment URL and filename
            result = self.airtable_tool.get_attachment_from_announcement(
                announcement_id=announcement_id,
                search_term=search_term,
                get_latest=get_latest
            )
            
            if isinstance(result, str) and not result.startswith("http"):
                # This is an error message
                return result
            
            # Download the file
            url, filename = result
            local_path = self.airtable_tool.download_file(url, filename)
            
            return local_path
        except Exception as e:
            logger.error(f"Error getting attachment: {str(e)}")
            return f"Error getting attachment: {str(e)}"
    
    def _analyze_document(self, file_path: str, analysis_type: str = "summarize", 
                         custom_prompt: Optional[str] = None) -> str:
        """
        Analyze a document using OpenAI.
        
        Args:
            file_path: Path to the document file
            analysis_type: Type of analysis to perform
            custom_prompt: Custom prompt for analysis
            
        Returns:
            Analysis result
        """
        try:
            return self.openai_analysis_tool.analyze_document(
                file_path=file_path,
                analysis_type=analysis_type,
                custom_prompt=custom_prompt
            )
        except Exception as e:
            logger.error(f"Error analyzing document: {str(e)}")
            return f"Error analyzing document: {str(e)}"
    
    def set_user_timezone(self, timezone: str) -> bool:
        """
        Set the user's timezone for all date operations.
        
        Args:
            timezone: Timezone to set (e.g., "America/New_York", "UTC")
            
        Returns:
            True if successful, False if the timezone is invalid
        """
        # Update the timezone in DateUtilsTool
        if self.date_utils.set_default_timezone(timezone):
            self.user_timezone = timezone
            # Recreate the agent with the new timezone
            self.agent_executor = self._setup_agent()
            return True
        return False
    
    def execute(self, query: str, chat_history: Optional[List] = None) -> Dict[str, Any]:
        """
        Execute a query using the agent.
        
        Args:
            query: User query
            chat_history: Optional chat history
            
        Returns:
            Agent response
        """
        try:
            # Execute the query
            if chat_history:
                result = self.agent_executor.run(input=query, chat_history=chat_history)
            else:
                result = self.agent_executor.run(input=query)
            
            return {
                "response": result,
                "success": True
            }
        except Exception as e:
            logger.error(f"Error executing query: {str(e)}")
            return {
                "response": f"I encountered an error: {str(e)}",
                "success": False
            }


# Create an instance of AgentManager to be imported by other modules
agent_manager = AgentManager()

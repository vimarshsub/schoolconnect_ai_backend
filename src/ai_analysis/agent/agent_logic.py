"""
Core agent logic for AI-powered announcement analysis.
"""

import os
import logging
from typing import Dict, List, Any, Optional
from langchain.chat_models import ChatOpenAI
from langchain.agents import initialize_agent, AgentType
from langchain.tools import Tool, StructuredTool
from pydantic import BaseModel, Field

from src.core.config import get_settings
from src.ai_analysis.tools.airtable_tool import AirtableTool
from src.ai_analysis.tools.openai_tool import OpenAIDocumentAnalysisTool
from src.ai_analysis.tools.google_calendar_tool import GoogleCalendarTool

logger = logging.getLogger("schoolconnect_ai")

# Memory key for chat history
MEMORY_KEY = "chat_history"

# Define Pydantic models for structured tool inputs
class CalendarEventInput(BaseModel):
    title: str = Field(..., description="Title of the event")
    start_time: str = Field(..., description="Start time in ISO format (YYYY-MM-DDTHH:MM:SS)")
    end_time: Optional[str] = Field(None, description="End time in ISO format (YYYY-MM-DDTHH:MM:SS)")
    description: Optional[str] = Field(None, description="Description of the event")
    location: Optional[str] = Field(None, description="Location of the event")
    attendees: Optional[str] = Field(None, description="Comma-separated list of attendee email addresses")
    reminder_minutes: Optional[int] = Field(None, description="Reminder time in minutes before the event")

class CalendarReminderInput(BaseModel):
    title: str = Field(..., description="Title of the reminder")
    due_date: str = Field(..., description="Due date in ISO format (YYYY-MM-DDTHH:MM:SS)")
    description: Optional[str] = Field(None, description="Description of the reminder")

class CalendarSearchInput(BaseModel):
    query: Optional[str] = Field(None, description="Search term to find events")
    start_date: Optional[str] = Field(None, description="Start date in 'YYYY-MM-DD' format")
    end_date: Optional[str] = Field(None, description="End date in 'YYYY-MM-DD' format")
    max_results: Optional[int] = Field(10, description="Maximum number of results to return")

class CalendarDeleteInput(BaseModel):
    event_id: str = Field(..., description="ID of the event to delete")

class AgentManager:
    """Manager for AI agent setup and execution."""
    
    def __init__(self):
        """Initialize the agent manager."""
        settings = get_settings()
        self.openai_api_key = settings.OPENAI_API_KEY
        self.model = settings.OPENAI_MODEL
        
        # Initialize tools
        self.airtable_tool = AirtableTool()
        self.openai_analysis_tool = OpenAIDocumentAnalysisTool()
        self.calendar_tool = GoogleCalendarTool()
        
        # Set up agent
        self.agent_executor = self._setup_agent()
    
    def _create_calendar_event(self, input_data: CalendarEventInput) -> str:
        """
        Wrapper for calendar event creation that handles structured input.
        
        Args:
            input_data: Structured input for calendar event
            
        Returns:
            Success or error message
        """
        # Convert attendees from string to list if provided
        attendees_list = None
        if input_data.attendees:
            attendees_list = [email.strip() for email in input_data.attendees.split(',')]
        
        return self.calendar_tool.create_event(
            title=input_data.title,
            start_time=input_data.start_time,
            end_time=input_data.end_time,
            description=input_data.description,
            location=input_data.location,
            attendees=attendees_list,
            reminder_minutes=input_data.reminder_minutes
        )
    
    def _create_calendar_reminder(self, input_data: CalendarReminderInput) -> str:
        """
        Wrapper for calendar reminder creation that handles structured input.
        
        Args:
            input_data: Structured input for calendar reminder
            
        Returns:
            Success or error message
        """
        return self.calendar_tool.create_reminder(
            title=input_data.title,
            due_date=input_data.due_date,
            description=input_data.description
        )
    
    def _search_calendar_events(self, input_data: CalendarSearchInput) -> Dict:
        """
        Wrapper for calendar event search that handles structured input.
        
        Args:
            input_data: Structured input for calendar search
            
        Returns:
            Search results or error message
        """
        return self.calendar_tool.search_events(
            query=input_data.query,
            start_date=input_data.start_date,
            end_date=input_data.end_date,
            max_results=input_data.max_results
        )
    
    def _delete_calendar_event(self, input_data: CalendarDeleteInput) -> str:
        """
        Wrapper for calendar event deletion that handles structured input.
        
        Args:
            input_data: Structured input for calendar event deletion
            
        Returns:
            Success or error message
        """
        return self.calendar_tool.delete_event(event_id=input_data.event_id)
    
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
            # Use StructuredTool for calendar operations to handle multiple arguments
            StructuredTool.from_function(
                func=self._create_calendar_event,
                name="create_calendar_event",
                description="Create a Google Calendar event with title, times, and optional details."
            ),
            StructuredTool.from_function(
                func=self._search_calendar_events,
                name="search_calendar_events",
                description="Search for events in Google Calendar with optional filters."
            ),
            StructuredTool.from_function(
                func=self._create_calendar_reminder,
                name="create_calendar_reminder",
                description="Create a reminder in Google Calendar with title and due date."
            ),
            StructuredTool.from_function(
                func=self._delete_calendar_event,
                name="delete_calendar_event",
                description="Delete an event from Google Calendar by ID."
            )
        ]
        
        # Create agent using the legacy initialize_agent method
        agent_executor = initialize_agent(
            tools=tools,
            llm=llm,
            agent=AgentType.OPENAI_FUNCTIONS,
            verbose=True,
            handle_parsing_errors=True
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
            Local file path or error message
        """
        url, filename = self.airtable_tool.get_attachment_from_announcement(
            announcement_id=announcement_id,
            search_term=search_term,
            get_latest=get_latest
        )
        
        if filename is None:
            return url  # This is an error message
        
        return self.airtable_tool.download_file(url)
    
    def _analyze_document(self, file_path: str, analysis_type: str = "summarize", 
                         custom_prompt: Optional[str] = None) -> str:
        """
        Analyze a document using OpenAI.
        
        Args:
            file_path: Path to the document file
            analysis_type: Type of analysis to perform
            custom_prompt: Custom prompt for analysis
            
        Returns:
            Analysis result or error message
        """
        return self.openai_analysis_tool.analyze_document(
            pdf_path=file_path,
            analysis_type=analysis_type,
            custom_prompt=custom_prompt
        )
    
    def execute(self, query: str, chat_history: List) -> Dict[str, Any]:
        """
        Execute the agent with a user query.
        
        Args:
            query: User query
            chat_history: Chat history in LangChain format
            
        Returns:
            Agent execution result
        """
        try:
            result = self.agent_executor.invoke({
                "input": query,
                MEMORY_KEY: chat_history
            })
            return result
        except Exception as e:
            logger.error(f"Agent execution error: {str(e)}", exc_info=True)
            return {"output": f"An error occurred: {str(e)}"}

# Create a singleton instance
agent_manager = AgentManager()
agent_executor = agent_manager.agent_executor

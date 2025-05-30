"""
Core agent logic for AI-powered announcement analysis.
"""

import os
import logging
from typing import Dict, List, Any, Optional
from langchain.chat_models import ChatOpenAI
from langchain.agents import initialize_agent, AgentType
from langchain.tools import Tool

from src.core.config import get_settings
from src.ai_analysis.tools.airtable_tool import AirtableTool
from src.ai_analysis.tools.openai_tool import OpenAIDocumentAnalysisTool
from src.ai_analysis.tools.google_calendar_tool import GoogleCalendarTool

logger = logging.getLogger("schoolconnect_ai")

# Memory key for chat history
MEMORY_KEY = "chat_history"

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
    
    def _create_calendar_event(self, title: str, start_time: str, 
                              end_time: Optional[str] = None, 
                              description: Optional[str] = None,
                              location: Optional[str] = None,
                              attendees: Optional[str] = None,
                              reminder_minutes: Optional[int] = None) -> str:
        """
        Wrapper for calendar event creation that handles multiple arguments.
        
        Args:
            title: Title of the event
            start_time: Start time in ISO format (YYYY-MM-DDTHH:MM:SS)
            end_time: End time in ISO format (YYYY-MM-DDTHH:MM:SS)
            description: Description of the event
            location: Location of the event
            attendees: Comma-separated list of attendee email addresses
            reminder_minutes: Reminder time in minutes before the event
            
        Returns:
            Success or error message
        """
        # Convert attendees from string to list if provided
        attendees_list = None
        if attendees:
            attendees_list = [email.strip() for email in attendees.split(',')]
        
        return self.calendar_tool.create_event(
            title=title,
            start_time=start_time,
            end_time=end_time,
            description=description,
            location=location,
            attendees=attendees_list,
            reminder_minutes=reminder_minutes
        )
    
    def _create_calendar_reminder(self, title: str, due_date: str, 
                                 description: Optional[str] = None) -> str:
        """
        Wrapper for calendar reminder creation that handles multiple arguments.
        
        Args:
            title: Title of the reminder
            due_date: Due date in ISO format (YYYY-MM-DDTHH:MM:SS)
            description: Description of the reminder
            
        Returns:
            Success or error message
        """
        return self.calendar_tool.create_reminder(
            title=title,
            due_date=due_date,
            description=description
        )
    
    def _search_calendar_events(self, query: Optional[str] = None, 
                               start_date: Optional[str] = None,
                               end_date: Optional[str] = None,
                               max_results: int = 10) -> Dict:
        """
        Wrapper for calendar event search that handles multiple arguments.
        
        Args:
            query: Search term to find events
            start_date: Start date in 'YYYY-MM-DD' format
            end_date: End date in 'YYYY-MM-DD' format
            max_results: Maximum number of results to return
            
        Returns:
            Search results or error message
        """
        return self.calendar_tool.search_events(
            query=query,
            start_date=start_date,
            end_date=end_date,
            max_results=max_results
        )
    
    def _delete_calendar_event(self, event_id: str) -> str:
        """
        Wrapper for calendar event deletion.
        
        Args:
            event_id: ID of the event to delete
            
        Returns:
            Success or error message
        """
        return self.calendar_tool.delete_event(event_id=event_id)
    
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
            Tool(
                name="create_calendar_event",
                func=self._create_calendar_event,
                description="Create a Google Calendar event. Required: title (string), start_time (ISO format YYYY-MM-DDTHH:MM:SS). Optional: end_time, description, location, attendees (comma-separated emails), reminder_minutes."
            ),
            Tool(
                name="search_calendar_events",
                func=self._search_calendar_events,
                description="Search for events in Google Calendar. Optional: query (search term), start_date (YYYY-MM-DD), end_date (YYYY-MM-DD), max_results (default 10)."
            ),
            Tool(
                name="create_calendar_reminder",
                func=self._create_calendar_reminder,
                description="Create a reminder in Google Calendar. Required: title (string), due_date (ISO format YYYY-MM-DDTHH:MM:SS). Optional: description."
            ),
            Tool(
                name="delete_calendar_event",
                func=self._delete_calendar_event,
                description="Delete an event from Google Calendar. Required: event_id (string)."
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

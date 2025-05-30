"""
Core agent logic for AI-powered announcement analysis.
"""

import os
import logging
from typing import Dict, List, Any, Optional
from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor
from langchain.agents.openai_functions_agent.base import create_openai_functions_agent
from langchain.prompts import MessagesPlaceholder
from langchain_core.messages import SystemMessage
from langchain_core.tools import Tool

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
        self.calendar_tool = None
        
        if settings.GOOGLE_CALENDAR_CREDENTIALS:
            self.calendar_tool = GoogleCalendarTool()
        
        # Set up agent
        self.agent_executor = self._setup_agent()
    
    def _setup_agent(self) -> AgentExecutor:
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
                description="Search for announcements by text in the Title or Description fields."
            ),
            Tool(
                name="filter_announcements_by_date",
                func=self.airtable_tool.filter_announcements_by_date,
                description="Filter announcements by date based on the SentTime field. Examples: 'in May', 'last week', '2023-01-01'."
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
            )
        ]
        
        # Add calendar tool if available
        if self.calendar_tool:
            tools.append(
                Tool(
                    name="create_calendar_event",
                    func=self.calendar_tool.create_event,
                    description="Create a Google Calendar event. Requires title, start_time, end_time, and optionally description and attendees."
                )
            )
        
        # Define system message content
        system_message_content = """You are an AI assistant that helps users manage and analyze announcements and their attachments.
            
You can:
1. Fetch all announcements from the database
2. Search for specific announcements by text
3. Filter announcements by date (e.g., "in May", "last week", "2023-01-01")
4. Get attachments from announcements
5. Analyze PDF documents (summarize, extract action items, analyze sentiment)
6. Create calendar events based on document content

When reporting the number of announcements, always use the exact 'count' value provided by the get_all_announcements or filter_announcements_by_date tools.

Always be helpful, clear, and concise in your responses. If you encounter any errors, explain them clearly and suggest alternatives.
"""
        
        # Create agent - using the correct signature for langchain-openai 0.0.5
        # The system_message is passed as part of the prompt instead
        from langchain.prompts import ChatPromptTemplate
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_message_content),
            MessagesPlaceholder(variable_name=MEMORY_KEY),
            ("user", "{input}"),
            ("user", "{agent_scratchpad}")  # Add the required agent_scratchpad variable
        ])
        
        agent = create_openai_functions_agent(
            llm=llm,
            tools=tools,
            prompt=prompt
        )
        
        # Create agent executor
        agent_executor = AgentExecutor(
            agent=agent,
            tools=tools,
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

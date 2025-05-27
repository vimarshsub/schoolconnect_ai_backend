"""
Chat history management for AI agent conversations.
"""

import logging
from typing import Dict, List, Tuple, Optional
from langchain_core.messages import HumanMessage, AIMessage

logger = logging.getLogger("schoolconnect_ai")

class ChatHistoryManager:
    """Manager for chat history across multiple sessions."""
    
    def __init__(self):
        """Initialize the chat history manager."""
        self.histories = {}
    
    def add_message(self, session_id: str, role: str, content: str) -> None:
        """
        Add a message to the chat history for a specific session.
        
        Args:
            session_id: Unique session identifier
            role: Message role ('user' or 'assistant')
            content: Message content
        """
        if session_id not in self.histories:
            self.histories[session_id] = []
        
        self.histories[session_id].append((role, content))
        logger.debug(f"Added {role} message to session {session_id}")
    
    def get_history(self, session_id: str) -> List[Tuple[str, str]]:
        """
        Get the chat history for a specific session.
        
        Args:
            session_id: Unique session identifier
            
        Returns:
            List of (role, content) tuples
        """
        return self.histories.get(session_id, [])
    
    def get_langchain_history(self, session_id: str) -> List:
        """
        Get the chat history in LangChain format for a specific session.
        
        Args:
            session_id: Unique session identifier
            
        Returns:
            List of LangChain message objects
        """
        history = self.get_history(session_id)
        langchain_history = []
        
        for role, content in history:
            if role == "user":
                langchain_history.append(HumanMessage(content=content))
            elif role == "assistant":
                langchain_history.append(AIMessage(content=content))
        
        return langchain_history
    
    def clear_history(self, session_id: str) -> None:
        """
        Clear the chat history for a specific session.
        
        Args:
            session_id: Unique session identifier
        """
        if session_id in self.histories:
            self.histories[session_id] = []
            logger.info(f"Cleared chat history for session {session_id}")
    
    def get_all_session_ids(self) -> List[str]:
        """
        Get all active session IDs.
        
        Returns:
            List of session IDs
        """
        return list(self.histories.keys())

# Create a singleton instance
chat_history_manager = ChatHistoryManager()

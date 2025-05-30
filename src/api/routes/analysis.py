"""
API routes for AI analysis operations.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
import uuid

from src.api.routes.auth import get_current_user
from src.ai_analysis.agent.agent_logic import agent_manager
from src.ai_analysis.agent.chat_history import chat_history_manager
from src.storage.airtable.client import AirtableClient

router = APIRouter()

class ChatRequest(BaseModel):
    """Request model for chat messages."""
    message: str

class ChatResponse(BaseModel):
    """Response model for chat messages."""
    session_id: str
    response: str
    additional_data: Optional[Dict[str, Any]] = None

class AnnouncementResponse(BaseModel):
    """Response model for announcements."""
    announcements: List[Dict[str, Any]]

class SearchRequest(BaseModel):
    """Request model for announcement search."""
    search_text: str

# Use header for session identification
async def get_session_id(session_id: Optional[str] = None):
    """Get or create a session ID for the chat."""
    if not session_id:
        # Generate a new session ID if none provided
        return str(uuid.uuid4())
    return session_id

@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    session_id: str = Depends(get_session_id),
    current_user = Depends(get_current_user)
):
    """
    Send a message to the AI agent and get a response.
    """
    try:
        # Add user message to chat history
        chat_history_manager.add_message(session_id, "user", request.message)
        
        # Get chat history in LangChain format
        langchain_chat_history = chat_history_manager.get_langchain_history(session_id)
        
        # Execute agent with query
        result = agent_manager.execute(request.message, langchain_chat_history)
        
        agent_response = result.get("output", "Sorry, I didn't get a clear response.")
        
        # Add assistant response to chat history
        chat_history_manager.add_message(session_id, "assistant", agent_response)
        
        return ChatResponse(
            session_id=session_id,
            response=agent_response,
            additional_data=None
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/chat/{session_id}", response_model=List[Dict[str, str]])
async def get_chat_history(
    session_id: str,
    current_user = Depends(get_current_user)
):
    """
    Get the chat history for a specific session.
    """
    history = chat_history_manager.get_history(session_id)
    return [{"role": role, "content": content} for role, content in history]

@router.delete("/chat/{session_id}")
async def clear_chat_history(
    session_id: str,
    current_user = Depends(get_current_user)
):
    """
    Clear the chat history for a specific session.
    """
    chat_history_manager.clear_history(session_id)
    return {"status": "success", "message": f"Chat history cleared for session {session_id}"}

@router.get("/announcements", response_model=AnnouncementResponse)
async def get_announcements(current_user = Depends(get_current_user)):
    """
    Get all announcements from Airtable.
    """
    client = AirtableClient()
    records = client.get_all_records()
    announcements = [record["fields"] for record in records if "fields" in record]
    
    return AnnouncementResponse(announcements=announcements)

@router.get("/announcements/search", response_model=AnnouncementResponse)
async def search_announcements(
    search_text: str,
    current_user = Depends(get_current_user)
):
    """
    Search announcements by text.
    """
    client = AirtableClient()
    records = client.search_records(search_text)
    announcements = [record["fields"] for record in records if "fields" in record]
    
    return AnnouncementResponse(announcements=announcements)

@router.get("/announcements/{announcement_id}/attachments")
async def get_announcement_attachments(
    announcement_id: str,
    current_user = Depends(get_current_user)
):
    """
    Get attachments for a specific announcement.
    """
    client = AirtableClient()
    record = client.get_record_by_id(announcement_id)
    
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Announcement with ID {announcement_id} not found"
        )
    
    attachments = record["fields"].get("Attachments", [])
    return {"attachments": attachments}

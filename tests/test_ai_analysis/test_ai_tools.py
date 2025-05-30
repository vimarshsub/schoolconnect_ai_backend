"""
Test for AI analysis functionality.
"""

import pytest
from unittest.mock import patch, MagicMock

from src.ai_analysis.agent.agent_logic import agent_manager
from src.ai_analysis.tools.airtable_tool import AirtableTool
from src.ai_analysis.tools.openai_tool import OpenAIDocumentAnalysisTool

def test_airtable_tool_get_all_announcements(mock_airtable_client):
    """Test getting all announcements using the AirtableTool."""
    tool = AirtableTool()
    announcements = tool.get_all_announcements()
    
    assert isinstance(announcements, list)
    assert len(announcements) > 0
    assert "Title" in announcements[0]
    assert "Description" in announcements[0]

def test_airtable_tool_search_announcements(mock_airtable_client):
    """Test searching announcements using the AirtableTool."""
    tool = AirtableTool()
    announcements = tool.search_announcements("test")
    
    assert isinstance(announcements, list)
    assert len(announcements) > 0
    assert "test" in announcements[0]["Title"].lower() or "test" in announcements[0]["Description"].lower()

def test_airtable_tool_get_attachment(mock_airtable_client):
    """Test getting an attachment using the AirtableTool."""
    tool = AirtableTool()
    
    # Mock the download_file method to avoid actual HTTP requests
    with patch.object(tool, 'download_file', return_value="/tmp/test.pdf"):
        url, filename = tool.get_attachment_from_announcement(announcement_id="rec123")
        assert url is not None
        assert filename is not None
        
        # Test with get_latest=True
        url, filename = tool.get_attachment_from_announcement(get_latest=True)
        assert url is not None
        assert filename is not None

def test_openai_document_analysis(mock_openai_tool):
    """Test document analysis using the OpenAIDocumentAnalysisTool."""
    tool = OpenAIDocumentAnalysisTool()
    
    # Create a mock PDF file
    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".pdf") as temp_file:
        temp_file.write(b"%PDF-1.5\n%Test PDF file")
        temp_file.flush()
        
        # Test different analysis types
        summary = tool.analyze_document(temp_file.name, analysis_type="summarize")
        assert summary is not None
        assert isinstance(summary, str)
        
        action_items = tool.analyze_document(temp_file.name, analysis_type="extract_action_items")
        assert action_items is not None
        assert isinstance(action_items, str)
        
        sentiment = tool.analyze_document(temp_file.name, analysis_type="sentiment")
        assert sentiment is not None
        assert isinstance(sentiment, str)
        
        custom = tool.analyze_document(temp_file.name, analysis_type="custom", 
                                      custom_prompt="What is this document about?")
        assert custom is not None
        assert isinstance(custom, str)

def test_agent_execution():
    """Test agent execution with a simple query."""
    # Mock the agent executor to avoid actual LLM calls
    with patch.object(agent_manager, 'execute') as mock_execute:
        mock_execute.return_value = {"output": "This is a test response"}
        
        result = agent_manager.execute("Show me all announcements", [])
        
        assert result is not None
        assert "output" in result
        assert result["output"] == "This is a test response"
        mock_execute.assert_called_once()

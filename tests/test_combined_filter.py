"""
Test script for the combined filtering functionality.
"""

import sys
import os
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.ai_analysis.agent.agent_logic import agent_manager
from src.ai_analysis.tools.airtable_tool import AirtableTool

def test_direct_combined_filter():
    """Test the combined filter method directly."""
    print("\n=== Testing Direct Combined Filter ===")
    
    # Create an instance of the AirtableTool
    airtable_tool = AirtableTool()
    
    # Test with multiple filter criteria
    results = airtable_tool.combined_filter_announcements(
        search_text="easter",
        sender_name="Sierra Robbins",
        date_query="in May"
    )
    
    # Print the results
    print(f"Results: {results.get('message')}")
    print(f"Count: {results.get('count')}")
    
    # Print first few announcements if available
    announcements = results.get('announcements', [])
    for i, announcement in enumerate(announcements[:3]):  # Show up to 3 announcements
        print(f"\nAnnouncement {i+1}:")
        print(f"Title: {announcement.get('Title', 'N/A')}")
        print(f"Sender: {announcement.get('SentByUser', 'N/A')}")
        print(f"Date: {announcement.get('SentTime', 'N/A')}")
        print(f"Description: {announcement.get('Description', 'N/A')[:100]}...")  # Truncate long descriptions

def test_agent_query():
    """Test the agent with a combined filter query."""
    print("\n=== Testing Agent with Combined Filter Query ===")
    
    # Test queries
    queries = [
        "Show me all easter related announcements sent by Sierra Robbins in May",
        "Find announcements about school events from Jane Smith last week",
        "Get me all announcements from March about field trips"
    ]
    
    for query in queries:
        print(f"\nQuery: '{query}'")
        
        # Execute the query
        result = agent_manager.execute(query)
        
        # Print the result
        print(f"Response: {result.get('response')[:500]}...")  # Truncate long responses
        print(f"Success: {result.get('success')}")

if __name__ == "__main__":
    # Run the tests
    test_direct_combined_filter()
    test_agent_query() 
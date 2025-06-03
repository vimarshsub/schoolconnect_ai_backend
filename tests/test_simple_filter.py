"""
Simple test for the combined filtering logic with mocked dependencies.
"""

from unittest.mock import MagicMock, patch
import sys
import os
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

def test_combined_filter_logic():
    """Test the combined filter method with mocked dependencies."""
    print("\n=== Testing Combined Filter Logic ===")
    
    # Import only after patching
    with patch('src.storage.airtable.client.AirtableClient'):
        from src.ai_analysis.tools.airtable_tool import AirtableTool
        
        # Create an instance with mocked client
        airtable_tool = AirtableTool()
        airtable_tool.client = MagicMock()
        
        # Setup mock data
        mock_announcements = [
            {
                "fields": {
                    "AnnouncementId": "1",
                    "Title": "Easter Party Invitation",
                    "Description": "Join us for an Easter celebration!",
                    "SentByUser": "Sierra Robbins",
                    "SentTime": "2025-05-10T10:00:00.000Z"
                }
            },
            {
                "fields": {
                    "AnnouncementId": "2",
                    "Title": "Math Test Next Week",
                    "Description": "Preparing for final exams",
                    "SentByUser": "Sierra Robbins",
                    "SentTime": "2025-05-15T14:30:00.000Z"
                }
            },
            {
                "fields": {
                    "AnnouncementId": "3",
                    "Title": "School Play Announcement",
                    "Description": "Easter themed play next month",
                    "SentByUser": "Jane Smith",
                    "SentTime": "2025-05-20T09:15:00.000Z"
                }
            }
        ]
        
        # Mock search_announcements_by_sender
        def mock_search_by_sender(sender_name):
            results = [r for r in mock_announcements if sender_name.lower() in r["fields"]["SentByUser"].lower()]
            return {
                "count": len(results),
                "announcements": [r["fields"] for r in results],
                "message": f"Found {len(results)} announcements from sender '{sender_name}'."
            }
        
        # Mock the AirtableTool methods
        airtable_tool.search_announcements_by_sender = mock_search_by_sender
        
        # Mock the get_all_announcements method
        airtable_tool.get_all_announcements = lambda: {
            "count": len(mock_announcements),
            "announcements": [r["fields"] for r in mock_announcements],
            "message": f"Found {len(mock_announcements)} announcements."
        }
        
        # Test case 1: Filter by sender only
        print("\nTest 1: Filter by sender only")
        results = airtable_tool.combined_filter_announcements(
            sender_name="Sierra Robbins"
        )
        print(f"Results: {results.get('message')}")
        print(f"Count: {results.get('count')}")
        
        # Test case 2: Filter by sender and text
        print("\nTest 2: Filter by sender and text")
        results = airtable_tool.combined_filter_announcements(
            search_text="easter",
            sender_name="Sierra Robbins"
        )
        print(f"Results: {results.get('message')}")
        print(f"Count: {results.get('count')}")
        
        # Test case 3: Filter by text only
        print("\nTest 3: Filter by text only")
        airtable_tool.search_announcements = lambda text: [
            r["fields"] for r in mock_announcements 
            if text.lower() in r["fields"]["Title"].lower() or text.lower() in r["fields"]["Description"].lower()
        ]
        
        results = airtable_tool.combined_filter_announcements(
            search_text="easter"
        )
        print(f"Results: {results.get('message')}")
        print(f"Count: {results.get('count')}")

if __name__ == "__main__":
    # Run the test
    test_combined_filter_logic() 
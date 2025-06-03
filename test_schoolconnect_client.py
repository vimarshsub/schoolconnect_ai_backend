#!/usr/bin/env python
"""
Test script for SchoolConnect GraphQL API client.
This demonstrates how to authenticate with SchoolConnect and make GraphQL calls.
"""

import os
import json
from dotenv import load_dotenv
from src.data_ingestion.schoolconnect.client import SchoolConnectClient
from src.core.config import get_settings

# Load environment variables
load_dotenv()

# Get the settings with credentials
settings = get_settings()

def test_schoolconnect_graphql():
    """Test SchoolConnect GraphQL API with session authentication."""
    
    # Initialize the client
    client = SchoolConnectClient()
    
    # Get credentials from settings (or set them directly)
    username = settings.SCHOOLCONNECT_USERNAME
    password = settings.SCHOOLCONNECT_PASSWORD
    
    if not username or not password:
        print("❌ SchoolConnect credentials not set in environment variables!")
        print("Please set SCHOOLCONNECT_USERNAME and SCHOOLCONNECT_PASSWORD in .env file")
        return
    
    print(f"Attempting to login as {username}...")
    
    # Authenticate with SchoolConnect
    login_success, error = client.login(username, password)
    
    if not login_success:
        print(f"❌ Authentication failed: {error}")
        return
    
    print("✅ Authentication successful! Now fetching announcements...")
    
    # Fetch announcements using the authenticated session
    result = client.fetch_paginated_announcements(items_per_page=5)
    
    if result.get("error"):
        print(f"❌ Error fetching announcements: {result.get('error')}")
        return
    
    # Print results
    announcements = result.get("announcements", [])
    print(f"Found {len(announcements)} announcements")
    
    for idx, announcement in enumerate(announcements, 1):
        print(f"\nAnnouncement {idx}:")
        print(f"  Title: {announcement.get('title')}")
        print(f"  Created: {announcement.get('createdAt')}")
        print(f"  Documents: {announcement.get('documentsCount')}")
    
    # Test fetching documents for the first announcement if available
    if announcements:
        first_announcement = announcements[0]
        announcement_id = f"Announcement:{first_announcement.get('dbId')}"
        
        print(f"\nFetching documents for announcement: {announcement_id}")
        documents = client.fetch_announcement_documents(announcement_id)
        
        if documents:
            print(f"Found {len(documents)} documents")
            for idx, doc in enumerate(documents, 1):
                print(f"  Document {idx}: {doc.get('fileFilename')} ({doc.get('contentType')})")
        else:
            print("No documents found or error fetching documents")

if __name__ == "__main__":
    test_schoolconnect_graphql() 
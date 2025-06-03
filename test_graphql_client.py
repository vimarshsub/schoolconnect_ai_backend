#!/usr/bin/env python
"""
Test script for SchoolConnect GraphQL client.
This demonstrates how to make direct GraphQL calls to SchoolConnect's API.
"""

import os
import json
import requests
from dotenv import load_dotenv
from src.core.config import get_settings

# Load environment variables
load_dotenv()

# Get settings with SchoolConnect credentials
settings = get_settings()
GRAPHQL_URL = settings.SCHOOLCONNECT_GRAPHQL_URL

def test_direct_graphql_call():
    """Test direct GraphQL call to SchoolConnect API."""
    
    # Get credentials from settings
    username = settings.SCHOOLCONNECT_USERNAME
    password = settings.SCHOOLCONNECT_PASSWORD
    
    if not username or not password:
        print("❌ SchoolConnect credentials not set in environment variables!")
        print("Please set SCHOOLCONNECT_USERNAME and SCHOOLCONNECT_PASSWORD in .env file")
        return
    
    print(f"Attempting to login to SchoolConnect as {username}...")
    
    # Create a session to maintain cookies between requests
    session = requests.Session()
    
    # Step 1: Login to SchoolConnect
    login_success, session = login_to_schoolconnect(session, username, password)
    
    if not login_success:
        return
    
    # Step 2: Make a GraphQL query to fetch announcements
    fetch_announcements(session)

def login_to_schoolconnect(session, username, password):
    """
    Login to SchoolConnect using GraphQL mutation.
    
    Args:
        session: requests Session
        username: SchoolConnect username
        password: SchoolConnect password
        
    Returns:
        Tuple of (success, session)
    """
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Origin': 'https://connect.schoolstatus.com',
        'Referer': 'https://connect.schoolstatus.com/'
    }
    
    login_payload = {
        "query": "mutation SessionCreateMutation($input: Session__CreateInput!) { sessionCreate(input: $input) { error location user { id dbId churnZeroId userCredentials { id dbId credential credentialType } } } }",
        "variables": {
            "input": {
                "credential": username,
                "password": password,
                "rememberMe": True
            }
        }
    }
    
    try:
        login_response = session.post(GRAPHQL_URL, json=login_payload, headers=headers, timeout=30)
        login_response.raise_for_status()
        login_data = login_response.json()
        
        # Check for GraphQL errors
        if login_data.get("errors") or login_data.get("data", {}).get("sessionCreate", {}).get("error"):
            error_message = login_data.get("errors", [{}])[0].get("message") or login_data.get("data", {}).get("sessionCreate", {}).get("error")
            print(f"❌ Login failed: {error_message}")
            return False, session
        
        print("✅ Login successful!")
        
        # Print session cookies for debugging
        print("Session cookies:")
        for cookie in session.cookies:
            print(f"  {cookie.name}: {cookie.value[:10]}...")
        
        return True, session
    except Exception as e:
        print(f"❌ Login failed with exception: {str(e)}")
        return False, session

def fetch_announcements(session):
    """
    Fetch announcements using GraphQL query.
    
    Args:
        session: authenticated requests Session
    """
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Origin': 'https://connect.schoolstatus.com',
        'Referer': 'https://connect.schoolstatus.com/'
    }
    
    announcements_payload = {
        "query": """
            query AnnouncementsListQuery($first: Int, $after: String) {
              viewer {
                id
                dbId
                announcements(first: $first, after: $after) {
                  edges {
                    node {
                      id
                      dbId
                      titleInfo {
                        origin
                      }
                      messageInfo {
                        origin
                      }
                      createdAt
                      user {
                        permittedName
                        avatarUrl
                      }
                      documentsCount
                    }
                  }
                  pageInfo {
                    hasNextPage
                    endCursor
                  }
                }
              }
            }
        """,
        "variables": {
            "first": 5,
            "after": None
        }
    }
    
    try:
        print("\nFetching announcements...")
        
        announcements_response = session.post(GRAPHQL_URL, json=announcements_payload, headers=headers, timeout=30)
        announcements_response.raise_for_status()
        announcements_data = announcements_response.json()
        
        # Check for GraphQL errors
        if "errors" in announcements_data:
            error_message = announcements_data.get("errors", [{}])[0].get("message", "Unknown GraphQL error")
            print(f"❌ GraphQL errors: {error_message}")
            return
        
        # Process the response
        viewer_data = announcements_data.get("data", {}).get("viewer", {})
        announcements_info = viewer_data.get("announcements", {})
        edges = announcements_info.get("edges", [])
        
        print(f"✅ Successfully fetched {len(edges)} announcements")
        
        # Print first announcement as an example
        if edges:
            first_announcement = edges[0].get("node", {})
            print("\nExample announcement:")
            print(f"  Title: {first_announcement.get('titleInfo', {}).get('origin')}")
            print(f"  Message: {first_announcement.get('messageInfo', {}).get('origin')[:100]}...")
            print(f"  Created: {first_announcement.get('createdAt')}")
            print(f"  Documents: {first_announcement.get('documentsCount')}")
        else:
            print("No announcements found")
        
    except Exception as e:
        print(f"❌ Error fetching announcements: {str(e)}")

if __name__ == "__main__":
    print("=" * 50)
    print("TESTING DIRECT GRAPHQL CALL TO SCHOOLCONNECT")
    print("=" * 50)
    test_direct_graphql_call()
    print("=" * 50) 
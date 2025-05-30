"""
SchoolConnect API client for fetching announcements and documents.
"""

import logging
import time
import json
import os
import tempfile
import requests
from typing import Dict, List, Optional, Any, Tuple

logger = logging.getLogger("schoolconnect_ai")

class SchoolConnectClient:
    """Client for interacting with SchoolConnect API."""
    
    def __init__(self, session: requests.Session = None):
        """
        Initialize the SchoolConnect client.
        
        Args:
            session: Optional requests session to use
        """
        self.session = session or requests.Session()
        self.graphql_url = "https://connect.schoolstatus.com/graphql"
        self.username = None
        self.password = None
    
    def login(self, username: str, password: str) -> Tuple[bool, Optional[str]]:
        """
        Login to SchoolConnect.
        
        Args:
            username: SchoolConnect username
            password: SchoolConnect password
            
        Returns:
            Tuple of (success, error_message)
        """
        logger.info(f"Logging in to SchoolConnect as {username}")
        
        # Store credentials for re-authentication
        self.username = username
        self.password = password
        
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
            login_response = self.session.post(self.graphql_url, json=login_payload, headers=headers, timeout=30)
            login_response.raise_for_status()
            login_data = login_response.json()
            
            if login_data.get("errors") or login_data.get("data", {}).get("sessionCreate", {}).get("error"):
                error_message = login_data.get("errors", [{}])[0].get("message") or login_data.get("data", {}).get("sessionCreate", {}).get("error")
                logger.error(f"Login failed: {error_message}")
                return False, error_message
            
            logger.info("Login successful")
            return True, None
        except Exception as e:
            logger.error(f"Login failed: {str(e)}", exc_info=True)
            return False, str(e)
    
    def fetch_paginated_announcements(self, after_cursor: Optional[str] = None, items_per_page: int = 20) -> Dict[str, Any]:
        """
        Fetch paginated announcements.
        
        Args:
            after_cursor: Cursor for pagination
            items_per_page: Number of items per page
            
        Returns:
            Dictionary with announcements, pagination info, and error
        """
        logger.info(f"Fetching paginated announcements (after_cursor: {after_cursor}, items_per_page: {items_per_page})")
        
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
                "first": items_per_page,
                "after": after_cursor
            }
        }
        
        try:
            announcements_response = self.session.post(self.graphql_url, json=announcements_payload, headers=headers, timeout=30)
            announcements_response.raise_for_status()
            announcements_data = announcements_response.json()
            
            if "errors" in announcements_data:
                error_message = announcements_data.get("errors", [{}])[0].get("message", "Unknown GraphQL error")
                logger.error(f"GraphQL errors: {error_message}")
                return {"announcements": [], "hasNextPage": False, "endCursor": None, "error": error_message}
            
            # Process the response
            viewer_data = announcements_data.get("data", {}).get("viewer", {})
            announcements_info = viewer_data.get("announcements", {})
            page_info = announcements_info.get("pageInfo", {})
            
            processed_announcements = []
            if announcements_info.get("edges"):
                for edge in announcements_info["edges"]:
                    if edge and edge.get("node"):
                        node = edge["node"]
                        announcement = {
                            "id": node.get("id"),
                            "dbId": node.get("dbId"),
                            "title": node.get("titleInfo", {}).get("origin"),
                            "message": node.get("messageInfo", {}).get("origin"),
                            "createdAt": node.get("createdAt"),
                            "documentsCount": node.get("documentsCount", 0),
                            "user": node.get("user", {})
                        }
                        processed_announcements.append(announcement)
            
            return {
                "announcements": processed_announcements,
                "hasNextPage": page_info.get("hasNextPage", False),
                "endCursor": page_info.get("endCursor"),
                "error": None
            }
        except Exception as e:
            logger.error(f"Error fetching paginated announcements: {str(e)}", exc_info=True)
            return {"announcements": [], "hasNextPage": False, "endCursor": None, "error": str(e)}
    
    def fetch_announcement_documents(self, announcement_id: str) -> List[Dict[str, Any]]:
        """
        Fetch documents for a specific announcement.
        
        Args:
            announcement_id: ID of the announcement
            
        Returns:
            List of document dictionaries
        """
        logger.info(f"Fetching documents for announcement {announcement_id}")
        
        # Re-authenticate before fetching documents to ensure fresh session
        if self.username and self.password:
            logger.info("Re-authenticating before fetching documents to ensure fresh session")
            self.login(self.username, self.password)
        else:
            logger.warning("Cannot re-authenticate before fetching documents: missing credentials")
        
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Origin': 'https://connect.schoolstatus.com',
            'Referer': 'https://connect.schoolstatus.com/'
        }
        
        documents_payload = {
            "query": """
                query AnnouncementDocumentsQuery($id: ID!) {
                    announcement(id: $id) {
                        id
                        dbId
                        documents {
                            id
                            fileFilename
                            fileUrl
                            contentType
                        }
                    }
                }
            """,
            "variables": {
                "id": announcement_id
            }
        }
        
        try:
            response = self.session.post(self.graphql_url, json=documents_payload, headers=headers, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if "errors" in data:
                error_message = data.get("errors", [{}])[0].get("message", "Unknown GraphQL error")
                logger.error(f"Error fetching documents: {error_message}")
                return []
            
            documents = data.get("data", {}).get("announcement", {}).get("documents", [])
            logger.info(f"Found {len(documents)} documents for announcement {announcement_id}")
            
            return documents
        except Exception as e:
            logger.error(f"Error fetching documents: {str(e)}", exc_info=True)
            return []
    
    # The download_document method has been removed as it's not used in the document processing flow.
    # The system uses _download_document in FetchAnnouncementsTask which only verifies accessibility.

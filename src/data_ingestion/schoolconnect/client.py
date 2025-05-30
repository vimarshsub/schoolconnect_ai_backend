"""
SchoolConnect API client for authentication and data retrieval.
"""

import requests
import json
import logging
import os
from typing import Dict, List, Optional, Any

from src.core.config import get_settings

logger = logging.getLogger("schoolconnect_ai")

class SchoolConnectClient:
    """Client for interacting with the SchoolConnect GraphQL API."""
    
    def __init__(self):
        """Initialize the SchoolConnect client."""
        settings = get_settings()
        self.graphql_url = settings.SCHOOLCONNECT_GRAPHQL_URL
        self.session = requests.Session()
        self.headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Origin': 'https://connect.schoolstatus.com',
            'Referer': 'https://connect.schoolstatus.com/'
        }
        self.authenticated = False
        self.username = None
        self.password = None
    
    def login(self, username: str, password: str) -> bool:
        """
        Authenticate with SchoolConnect.
        
        Args:
            username: SchoolConnect username
            password: SchoolConnect password
            
        Returns:
            True if login successful, False otherwise
        """
        logger.info("Attempting login to SchoolConnect")
        logger.debug(f"Login attempt with username: {username}")
        
        # Store credentials for potential re-authentication
        self.username = username
        self.password = password
        
        # Create login payload - matching exactly what the original backend used
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
            logger.debug(f"Sending login request to: {self.graphql_url}")
            logger.debug(f"Login payload: {json.dumps(login_payload)}")
            
            # Send login request
            login_response = self.session.post(
                self.graphql_url, 
                json=login_payload, 
                headers=self.headers, 
                timeout=30
            )
            
            logger.debug(f"Login response status code: {login_response.status_code}")
            
            # Log cookies - this is critical for session management
            logger.info(f"Session cookies after login: {self.session.cookies.get_dict()}")
            
            # Log the raw response for debugging
            try:
                response_text = login_response.text
                logger.debug(f"Login response body: {response_text[:1000]}")  # Log first 1000 chars to avoid excessive logging
            except Exception as e:
                logger.debug(f"Could not log response body: {str(e)}")
            
            login_response.raise_for_status()
            login_data = login_response.json()
            
            # Check for GraphQL errors
            if login_data.get("errors"):
                error_message = login_data["errors"][0]["message"]
                logger.error(f"Login error from GraphQL: {error_message}")
                return False
            
            # Check for error in the sessionCreate response
            session_create = login_data.get("data", {}).get("sessionCreate", {})
            if session_create.get("error"):
                error_message = session_create.get("error")
                logger.error(f"Login error from sessionCreate: {error_message}")
                return False
                
            if not session_create.get("user"):
                logger.error("Login failed: No user data in response")
                return False
                
            logger.info("SchoolConnect login successful")
            self.authenticated = True
            return True
            
        except Exception as e:
            logger.error(f"Login error: {str(e)}", exc_info=True)
            return False
    
    def fetch_paginated_announcements(self, after_cursor: Optional[str] = None, items_per_page: int = 20) -> Dict[str, Any]:
        """
        Fetch paginated announcements from SchoolConnect.
        
        Args:
            after_cursor: Pagination cursor
            items_per_page: Number of items per page
            
        Returns:
            Dictionary containing announcements, pagination info, and error status
        """
        logger.info(f"Fetching paginated announcements. After cursor: {after_cursor}, Items per page: {items_per_page}")
        
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
                          title
                          message
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
            # Log cookies before request to ensure they're being maintained
            logger.debug(f"Session cookies before announcements request: {self.session.cookies.get_dict()}")
            
            response = self.session.post(
                self.graphql_url, 
                json=announcements_payload, 
                headers=self.headers, 
                timeout=30
            )
            
            # Log cookies after request
            logger.debug(f"Session cookies after announcements request: {self.session.cookies.get_dict()}")
            
            response.raise_for_status()
            data = response.json()

            if "errors" in data:
                logger.error(f"GraphQL errors: {data['errors']}")
                return {
                    "announcements": [], 
                    "hasNextPage": False, 
                    "endCursor": None, 
                    "error": data['errors']
                }

            # Process the response
            viewer_data = data.get("data", {}).get("viewer", {})
            announcements_info = viewer_data.get("announcements", {})
            page_info = announcements_info.get("pageInfo", {})
            
            processed_announcements = []
            if announcements_info.get("edges"):
                for edge in announcements_info["edges"]:
                    if edge and edge.get("node"):
                        node = edge["node"]
                        processed_announcements.append({
                            "id": node.get("id"),  # This is the GraphQL ID already in the correct format
                            "dbId": node.get("dbId"),  # This is the numeric ID
                            "title": node.get("title"),
                            "message": node.get("message"),
                            "createdAt": node.get("createdAt"),
                            "user": node.get("user", {}),
                            "documentsCount": node.get("documentsCount", 0)
                        })
            
            return {
                "announcements": processed_announcements,
                "hasNextPage": page_info.get("hasNextPage", False),
                "endCursor": page_info.get("endCursor"),
                "error": None
            }
            
        except Exception as e:
            logger.error(f"Error fetching announcements: {str(e)}", exc_info=True)
            return {
                "announcements": [], 
                "hasNextPage": False, 
                "endCursor": None, 
                "error": str(e)
            }
    
    def fetch_announcement_documents(self, announcement_id: str) -> List[Dict[str, Any]]:
        """
        Fetch documents for a specific announcement.
        
        Args:
            announcement_id: ID of the announcement (must be the GraphQL ID from pagination, not the numeric dbId)
            
        Returns:
            List of document dictionaries
        """
        logger.info(f"Fetching documents for announcement {announcement_id}")
        
        # Re-authenticate before fetching documents to ensure a fresh session
        # This is the key fix based on the original ClassTagWorkflowApp implementation
        if self.username and self.password:
            logger.info("Re-authenticating before fetching documents to ensure fresh session")
            self.login(self.username, self.password)
        else:
            logger.warning("Cannot re-authenticate before fetching documents: missing credentials")
        
        # IMPORTANT: Use the announcement_id directly from pagination results (already in correct format)
        # Do NOT attempt to encode or modify the ID - this was the source of the 404 errors
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
                "id": announcement_id  # Use the ID directly as provided
            }
        }

        try:
            # Log cookies before request
            logger.debug(f"Session cookies before documents request: {self.session.cookies.get_dict()}")
            
            # Log the request details for debugging
            logger.info(f"Sending document fetch request to: {self.graphql_url}")
            logger.info(f"Document fetch payload: {json.dumps(documents_payload)}")
            
            response = self.session.post(
                self.graphql_url, 
                json=documents_payload, 
                headers=self.headers,
                timeout=30
            )
            
            # Log response details for debugging
            logger.info(f"Document fetch response status: {response.status_code}")
            logger.debug(f"Document fetch response headers: {dict(response.headers)}")
            
            # Log cookies after request
            logger.debug(f"Session cookies after documents request: {self.session.cookies.get_dict()}")
            
            # Log the raw response for debugging
            try:
                response_text = response.text
                logger.debug(f"Document fetch response body: {response_text[:1000]}")
            except Exception as e:
                logger.debug(f"Could not log response body: {str(e)}")
            
            response.raise_for_status()
            data = response.json()

            if "errors" in data:
                error_message = data["errors"][0]["message"]
                logger.error(f"GraphQL errors: {error_message}")
                return []

            documents = data.get("data", {}).get("announcement", {}).get("documents", [])
            logger.info(f"Found {len(documents)} documents for announcement {announcement_id}")
            
            # Log document details for debugging
            for idx, doc in enumerate(documents, 1):
                logger.info(f"Document {idx}:")
                logger.info(f"  - Filename: {doc.get('fileFilename')}")
                logger.info(f"  - Type: {doc.get('contentType')}")
                logger.info(f"  - URL: {doc.get('fileUrl')}")
            
            return documents
            
        except Exception as e:
            logger.error(f"Error fetching documents: {str(e)}", exc_info=True)
            return []
    
    def download_document(self, url: str, filename: str) -> Optional[str]:
        """
        Download a document using the authenticated session.
        
        Args:
            url: URL of the document
            filename: Filename to save as
            
        Returns:
            Path to the downloaded file or None if download failed
        """
        try:
            logger.info(f"Downloading document from URL: {url}")
            
            # Log cookies before request
            logger.debug(f"Session cookies before document download: {self.session.cookies.get_dict()}")
            
            response = self.session.get(url, timeout=30)
            
            # Log cookies after request
            logger.debug(f"Session cookies after document download: {self.session.cookies.get_dict()}")
            
            response.raise_for_status()
            
            # Get the content
            content = response.content
            logger.info(f"Successfully downloaded document: {filename}, size: {len(content)} bytes")
            
            # Create a temporary file
            settings = get_settings()
            os.makedirs(settings.TEMP_FILE_DIR, exist_ok=True)
            temp_file_path = f"{settings.TEMP_FILE_DIR}/{filename}"
            
            with open(temp_file_path, "wb") as f:
                f.write(content)
            
            logger.info(f"Saved document to file: {temp_file_path}")
            return temp_file_path
            
        except Exception as e:
            logger.error(f"Error downloading document: {str(e)}", exc_info=True)
            return None

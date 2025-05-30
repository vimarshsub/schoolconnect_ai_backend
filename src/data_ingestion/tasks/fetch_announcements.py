"""
Task for fetching announcements from SchoolConnect and storing them in Airtable.
"""

import logging
import time
import json
import os
from typing import Dict, List, Optional, Any, Set

from src.core.config import get_settings
from src.data_ingestion.schoolconnect.auth import SchoolConnectAuth
from src.data_ingestion.schoolconnect.client import SchoolConnectClient
from src.storage.airtable.client import AirtableClient

logger = logging.getLogger("schoolconnect_ai")

class FetchAnnouncementsTask:
    """Task for fetching announcements from SchoolConnect and storing them in Airtable."""
    
    def __init__(self):
        """Initialize the task."""
        self.settings = get_settings()
        self.auth = SchoolConnectAuth()
        self.airtable_client = AirtableClient()
        
        # Target announcement IDs to specifically debug
        self.target_announcement_ids = {"15992525", "15929951", "15957863"}
        self.target_found = set()
    
    def execute(self, username: str, password: str, max_pages: int = 20) -> Dict[str, Any]:
        """
        Execute the task to fetch announcements and store them in Airtable.
        
        Args:
            username: SchoolConnect username
            password: SchoolConnect password
            max_pages: Maximum number of pages to fetch (increased default to 20)
            
        Returns:
            Dictionary with task results
        """
        logger.info("Starting announcement fetch task with enhanced debugging")
        logger.info(f"Targeting specific announcements: {', '.join(self.target_announcement_ids)}")
        
        # Authenticate with SchoolConnect
        client, error = self.auth.get_authenticated_client(username, password)
        if error:
            logger.error(f"Authentication failed: {error}")
            return {
                "success": False,
                "error": error,
                "announcements_processed": 0,
                "announcements_saved": 0
            }
        
        logger.info("Authentication successful, proceeding to fetch announcements")
        
        # Fetch announcements with pagination
        all_announcements = []
        
        # First try to directly fetch the target announcements if we have their IDs
        for announcement_id in self.target_announcement_ids:
            target_announcement = self._fetch_specific_announcement(client, announcement_id)
            if target_announcement:
                logger.info(f"Successfully fetched target announcement {announcement_id} directly")
                all_announcements.append(target_announcement)
                self.target_found.add(announcement_id)
                
                # Log the target announcement data
                logger.info(f"Target announcement {announcement_id} data: {json.dumps(target_announcement)}")
        
        # Continue with normal pagination to get other announcements
        has_next_page = True
        end_cursor = None
        page_count = 0
        
        while has_next_page and page_count < max_pages:
            logger.info(f"Fetching announcements page {page_count + 1}")
            result = client.fetch_paginated_announcements(after_cursor=end_cursor)
            
            if result.get("error"):
                logger.error(f"Error fetching announcements: {result['error']}")
                break
            
            announcements = result.get("announcements", [])
            
            # Check if target announcements are in this batch
            for announcement in announcements:
                if announcement.get("dbId") in self.target_announcement_ids:
                    announcement_id = announcement.get("dbId")
                    logger.info(f"Found target announcement {announcement_id} in page {page_count+1}")
                    self.target_found.add(announcement_id)
                    
                    # Log the target announcement data
                    logger.info(f"Target announcement {announcement_id} data: {json.dumps(announcement)}")
            
            all_announcements.extend(announcements)
            
            has_next_page = result.get("hasNextPage", False)
            end_cursor = result.get("endCursor")
            page_count += 1
            
            logger.info(f"Fetched {len(announcements)} announcements on page {page_count}")
            
            # Add a small delay between requests
            time.sleep(1)
        
        logger.info(f"Total announcements fetched: {len(all_announcements)}")
        logger.info(f"Target announcements found: {', '.join(self.target_found)}")
        logger.info(f"Target announcements not found: {', '.join(self.target_announcement_ids - self.target_found)}")
        
        # Process announcements and fetch documents
        processed_announcements = []
        for announcement in all_announcements:
            try:
                # Check if this is a target announcement
                is_target_announcement = announcement.get("dbId") in self.target_announcement_ids
                if is_target_announcement:
                    announcement_id = announcement.get("dbId")
                    logger.info(f"Processing target announcement {announcement_id}: {announcement.get('title')}")
                
                # Fetch documents for this announcement
                documents = client.fetch_announcement_documents(announcement["id"])
                announcement["documents"] = documents
                
                # Debug log for target announcement
                if is_target_announcement:
                    logger.info(f"Documents for announcement {announcement_id}: {len(documents)} found")
                    logger.info(f"Documents data: {json.dumps(documents)}")
                    
                    # Log each document's details
                    for i, doc in enumerate(documents):
                        logger.info(f"Document {i+1} details for {announcement_id}: filename={doc.get('fileFilename')}, type={doc.get('contentType')}, url={doc.get('fileUrl')}")
                
                processed_announcements.append(announcement)
                logger.info(f"Processed announcement {announcement.get('dbId')} with {len(documents)} documents")
            except Exception as e:
                logger.error(f"Error processing announcement {announcement.get('dbId')}: {str(e)}", exc_info=True)
                
                # Log error details for debugging
                if announcement.get("dbId") in self.target_announcement_ids:
                    logger.error(f"Error processing target announcement {announcement.get('dbId')}: {str(e)}")
        
        # Save to Airtable
        saved_count = self._save_to_airtable(processed_announcements)
        
        return {
            "success": True,
            "announcements_processed": len(processed_announcements),
            "announcements_saved": saved_count,
            "target_found": list(self.target_found)
        }
    
    def _fetch_specific_announcement(self, client: SchoolConnectClient, announcement_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch a specific announcement by ID.
        
        Args:
            client: Authenticated SchoolConnect client
            announcement_id: ID of the announcement to fetch
            
        Returns:
            Announcement data or None if not found
        """
        logger.info(f"Attempting to fetch specific announcement with ID: {announcement_id}")
        
        try:
            # Construct a GraphQL query to fetch a specific announcement
            query = {
                "query": """
                    query AnnouncementQuery($id: ID!) {
                        announcement(id: $id) {
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
                """,
                "variables": {
                    "id": f"Announcement:{announcement_id}"
                }
            }
            
            # Execute the query
            response = client.session.post(
                client.graphql_url,
                json=query,
                headers=client.headers,
                timeout=30
            )
            
            # Log raw response for debugging
            logger.info(f"Response status for announcement {announcement_id}: {response.status_code}")
            logger.debug(f"Response text for announcement {announcement_id}: {response.text[:500]}...")
            
            response.raise_for_status()
            data = response.json()
            
            # Check for errors
            if "errors" in data:
                error_message = data["errors"][0]["message"]
                logger.error(f"GraphQL error fetching announcement {announcement_id}: {error_message}")
                return None
            
            # Extract announcement data
            announcement_data = data.get("data", {}).get("announcement")
            if not announcement_data:
                logger.warning(f"Announcement {announcement_id} not found")
                return None
            
            logger.info(f"Successfully fetched specific announcement: {announcement_data.get('title')}")
            return announcement_data
            
        except Exception as e:
            logger.error(f"Error fetching specific announcement {announcement_id}: {str(e)}", exc_info=True)
            return None
    
    def _save_to_airtable(self, announcements: List[Dict[str, Any]]) -> int:
        """
        Save announcements to Airtable.
        
        Args:
            announcements: List of processed announcements
            
        Returns:
            Number of successfully saved announcements
        """
        logger.info(f"Saving {len(announcements)} announcements to Airtable")
        
        success_count = 0
        
        for announcement in announcements:
            try:
                # Check if this is a target announcement
                is_target_announcement = announcement.get("dbId") in self.target_announcement_ids
                announcement_id = announcement.get("dbId", "unknown")
                
                # Extract document URLs (PDF only)
                attachments = []
                if announcement.get("documents"):
                    # Log all document types for debugging
                    if is_target_announcement:
                        doc_types = [
                            f"{doc.get('fileFilename', 'unknown')} - {doc.get('contentType', 'unknown')}"
                            for doc in announcement.get("documents", [])
                        ]
                        logger.info(f"Document types for announcement {announcement_id}: {doc_types}")
                    
                    # Enhanced PDF detection logic - more inclusive
                    pdf_docs = []
                    for doc in announcement.get("documents", []):
                        is_pdf = False
                        # Check content type
                        if doc.get("contentType") == "application/pdf":
                            is_pdf = True
                            if is_target_announcement:
                                logger.info(f"PDF detected by content type for {announcement_id}: {doc.get('contentType')}")
                        # Check filename extension
                        elif doc.get("fileFilename") and doc.get("fileFilename").lower().endswith('.pdf'):
                            is_pdf = True
                            if is_target_announcement:
                                logger.info(f"PDF detected by filename for {announcement_id}: {doc.get('fileFilename')}")
                        # Check URL extension as fallback
                        elif doc.get("fileUrl") and doc.get("fileUrl").lower().endswith('.pdf'):
                            is_pdf = True
                            if is_target_announcement:
                                logger.info(f"PDF detected by URL for {announcement_id}: {doc.get('fileUrl')}")
                        # If still not detected as PDF but has a URL and filename, try as PDF anyway
                        elif doc.get("fileUrl") and doc.get("fileFilename"):
                            is_pdf = True
                            if is_target_announcement:
                                logger.info(f"Treating as PDF despite no indicators for {announcement_id}: {doc.get('fileFilename')}")
                            
                        if is_pdf:
                            pdf_docs.append(doc)
                            if is_target_announcement:
                                logger.info(f"PDF added to processing list for {announcement_id}: {doc.get('fileFilename')} with content type {doc.get('contentType')}")
                    
                    # Process all PDF documents (removed limit of 5)
                    docs_to_process = pdf_docs
                    
                    if is_target_announcement:
                        logger.info(f"PDF documents found for announcement {announcement_id}: {len(pdf_docs)}")
                    
                    for doc in docs_to_process:
                        if doc.get("fileUrl"):
                            # Ensure filename exists, create one if missing
                            filename = doc.get("fileFilename")
                            if not filename:
                                # Extract filename from URL or use default
                                url_parts = doc.get("fileUrl", "").split("/")
                                filename = url_parts[-1] if url_parts else f"document_{len(attachments)}.pdf"
                            
                            attachment = {
                                "url": doc.get("fileUrl"),
                                "filename": filename
                            }
                            attachments.append(attachment)
                            
                            if is_target_announcement:
                                logger.info(f"Adding attachment for {announcement_id}: {attachment}")
                
                # Prepare record for Airtable
                record = {
                    "AnnouncementId": announcement["dbId"],
                    "Title": announcement["title"],
                    "Description": announcement["message"],
                    "SentByUser": announcement["user"]["permittedName"],
                    "DocumentsCount": announcement["documentsCount"],
                    "SentTime": announcement["createdAt"]
                }
                
                # Add attachments if we have any
                if attachments:
                    record["Attachments"] = attachments
                    if is_target_announcement:
                        logger.info(f"Adding {len(attachments)} attachments to record for {announcement_id}")
                
                # Debug log for target announcement
                if is_target_announcement:
                    logger.info(f"Airtable record for announcement {announcement_id}: {json.dumps(record)}")
                
                # Save to Airtable
                result = self.airtable_client.create_record(record)
                if result:
                    success_count += 1
                    logger.info(f"Successfully saved announcement {announcement['dbId']} to Airtable")
                    
                    # Debug log for target announcement
                    if is_target_announcement:
                        logger.info(f"Airtable result for announcement {announcement_id}: {json.dumps(result)}")
                else:
                    logger.error(f"Failed to save announcement {announcement['dbId']} to Airtable")
                    
                    # Debug log for target announcement failure
                    if is_target_announcement:
                        logger.error(f"Failed to save target announcement {announcement_id} to Airtable")
                
                # Add a small delay between requests to avoid rate limiting
                time.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Error saving announcement {announcement.get('dbId')} to Airtable: {str(e)}", exc_info=True)
                
                # Log error details for debugging
                if announcement.get("dbId") in self.target_announcement_ids:
                    logger.error(f"Error saving target announcement {announcement.get('dbId')}: {str(e)}")
        
        logger.info(f"Successfully saved {success_count} announcements to Airtable")
        return success_count

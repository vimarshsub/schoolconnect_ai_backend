"""
Task for fetching announcements from SchoolConnect and storing them in Airtable.
"""

import logging
import time
import json
import os
from typing import Dict, List, Optional, Any

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
        
        # Set up debug logging directory
        self.debug_dir = os.path.join(os.getcwd(), "debug_logs")
        os.makedirs(self.debug_dir, exist_ok=True)
        
        # Target announcement ID to specifically debug
        self.target_announcement_id = "15992525"
        self.target_found = False
    
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
        
        # Log execution parameters
        with open(os.path.join(self.debug_dir, "execution_params.json"), "w") as f:
            json.dump({
                "max_pages": max_pages,
                "target_announcement_id": self.target_announcement_id,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }, f, indent=2)
        
        # Authenticate with SchoolConnect
        client, error = self.auth.get_authenticated_client(username, password)
        if error:
            logger.error(f"Authentication failed: {error}")
            with open(os.path.join(self.debug_dir, "auth_error.txt"), "w") as f:
                f.write(f"Authentication error: {error}")
            return {
                "success": False,
                "error": error,
                "announcements_processed": 0,
                "announcements_saved": 0
            }
        
        logger.info("Authentication successful, proceeding to fetch announcements")
        
        # Fetch announcements with pagination
        all_announcements = []
        has_next_page = True
        end_cursor = None
        page_count = 0
        
        # First try to directly fetch the target announcement if we have its ID
        target_announcement = self._fetch_specific_announcement(client, self.target_announcement_id)
        if target_announcement:
            logger.info(f"Successfully fetched target announcement {self.target_announcement_id} directly")
            all_announcements.append(target_announcement)
            self.target_found = True
            
            # Save the target announcement data
            with open(os.path.join(self.debug_dir, f"announcement_{self.target_announcement_id}_direct.json"), "w") as f:
                json.dump(target_announcement, f, indent=2)
        
        # Continue with normal pagination to get other announcements
        while has_next_page and page_count < max_pages:
            logger.info(f"Fetching announcements page {page_count + 1}")
            result = client.fetch_paginated_announcements(after_cursor=end_cursor)
            
            # Save raw API response for debugging
            with open(os.path.join(self.debug_dir, f"page_{page_count+1}_response.json"), "w") as f:
                json.dump(result, f, indent=2)
            
            if result.get("error"):
                logger.error(f"Error fetching announcements: {result['error']}")
                break
            
            announcements = result.get("announcements", [])
            
            # Check if target announcement is in this batch
            for announcement in announcements:
                if announcement.get("dbId") == self.target_announcement_id:
                    logger.info(f"Found target announcement {self.target_announcement_id} in page {page_count+1}")
                    self.target_found = True
                    
                    # Save the target announcement data
                    with open(os.path.join(self.debug_dir, f"announcement_{self.target_announcement_id}_pagination.json"), "w") as f:
                        json.dump(announcement, f, indent=2)
            
            all_announcements.extend(announcements)
            
            has_next_page = result.get("hasNextPage", False)
            end_cursor = result.get("endCursor")
            page_count += 1
            
            logger.info(f"Fetched {len(announcements)} announcements on page {page_count}")
            
            # Add a small delay between requests
            time.sleep(1)
        
        logger.info(f"Total announcements fetched: {len(all_announcements)}")
        logger.info(f"Target announcement found: {self.target_found}")
        
        # Save summary of fetched announcements
        with open(os.path.join(self.debug_dir, "fetched_announcements_summary.json"), "w") as f:
            summary = [{
                "dbId": a.get("dbId"),
                "title": a.get("title"),
                "createdAt": a.get("createdAt"),
                "documentsCount": a.get("documentsCount", 0)
            } for a in all_announcements]
            json.dump(summary, f, indent=2)
        
        # Process announcements and fetch documents
        processed_announcements = []
        for announcement in all_announcements:
            try:
                # Check if this is the target announcement
                is_target_announcement = announcement.get("dbId") == self.target_announcement_id
                if is_target_announcement:
                    logger.info(f"Processing target announcement {self.target_announcement_id}: {announcement.get('title')}")
                
                # Fetch documents for this announcement
                documents = client.fetch_announcement_documents(announcement["id"])
                announcement["documents"] = documents
                
                # Debug log for target announcement
                if is_target_announcement:
                    logger.info(f"Documents for announcement {self.target_announcement_id}: {len(documents)} found")
                    with open(os.path.join(self.debug_dir, f"documents_{self.target_announcement_id}.json"), "w") as f:
                        json.dump(documents, f, indent=2)
                    
                    # Log each document's details
                    for i, doc in enumerate(documents):
                        logger.info(f"Document {i+1} details: filename={doc.get('fileFilename')}, type={doc.get('contentType')}, url={doc.get('fileUrl')}")
                
                processed_announcements.append(announcement)
                logger.info(f"Processed announcement {announcement.get('dbId')} with {len(documents)} documents")
            except Exception as e:
                logger.error(f"Error processing announcement {announcement.get('dbId')}: {str(e)}", exc_info=True)
                
                # Save error details for debugging
                if announcement.get("dbId") == self.target_announcement_id:
                    with open(os.path.join(self.debug_dir, f"error_processing_{self.target_announcement_id}.txt"), "w") as f:
                        f.write(f"Error processing announcement: {str(e)}")
        
        # Save to Airtable
        saved_count = self._save_to_airtable(processed_announcements)
        
        return {
            "success": True,
            "announcements_processed": len(processed_announcements),
            "announcements_saved": saved_count,
            "target_found": self.target_found
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
            
            # Save raw response for debugging
            with open(os.path.join(self.debug_dir, f"specific_announcement_{announcement_id}_response.json"), "w") as f:
                try:
                    f.write(response.text)
                except:
                    f.write("Failed to write response text")
            
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
                # Check if this is the target announcement
                is_target_announcement = announcement.get("dbId") == self.target_announcement_id
                
                # Extract document URLs (PDF only)
                attachments = []
                if announcement.get("documents"):
                    # Log all document types for debugging
                    if is_target_announcement:
                        doc_types = [
                            f"{doc.get('fileFilename', 'unknown')} - {doc.get('contentType', 'unknown')}"
                            for doc in announcement.get("documents", [])
                        ]
                        logger.info(f"Document types for announcement {self.target_announcement_id}: {doc_types}")
                    
                    # Enhanced PDF detection logic - more inclusive
                    pdf_docs = []
                    for doc in announcement.get("documents", []):
                        is_pdf = False
                        # Check content type
                        if doc.get("contentType") == "application/pdf":
                            is_pdf = True
                        # Check filename extension
                        elif doc.get("fileFilename") and doc.get("fileFilename").lower().endswith('.pdf'):
                            is_pdf = True
                        # Check URL extension as fallback
                        elif doc.get("fileUrl") and doc.get("fileUrl").lower().endswith('.pdf'):
                            is_pdf = True
                            
                        if is_pdf:
                            pdf_docs.append(doc)
                            if is_target_announcement:
                                logger.info(f"PDF detected: {doc.get('fileFilename')} with content type {doc.get('contentType')}")
                    
                    # Process all PDF documents (removed limit of 5)
                    docs_to_process = pdf_docs
                    
                    if is_target_announcement:
                        logger.info(f"PDF documents found for announcement {self.target_announcement_id}: {len(pdf_docs)}")
                    
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
                                logger.info(f"Adding attachment for {self.target_announcement_id}: {attachment}")
                
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
                
                # Debug log for target announcement
                if is_target_announcement:
                    logger.info(f"Airtable record for announcement {self.target_announcement_id}: {json.dumps(record)}")
                    with open(os.path.join(self.debug_dir, f"airtable_record_{self.target_announcement_id}.json"), "w") as f:
                        json.dump(record, f, indent=2)
                
                # Save to Airtable
                result = self.airtable_client.create_record(record)
                if result:
                    success_count += 1
                    logger.info(f"Successfully saved announcement {announcement['dbId']} to Airtable")
                    
                    # Debug log for target announcement
                    if is_target_announcement:
                        logger.info(f"Airtable result for announcement {self.target_announcement_id}: {json.dumps(result)}")
                        with open(os.path.join(self.debug_dir, f"airtable_result_{self.target_announcement_id}.json"), "w") as f:
                            json.dump(result, f, indent=2)
                else:
                    logger.error(f"Failed to save announcement {announcement['dbId']} to Airtable")
                    
                    # Debug log for target announcement failure
                    if is_target_announcement:
                        logger.error(f"Failed to save target announcement {self.target_announcement_id} to Airtable")
                        with open(os.path.join(self.debug_dir, f"airtable_failure_{self.target_announcement_id}.txt"), "w") as f:
                            f.write(f"Failed to save announcement to Airtable at {time.strftime('%Y-%m-%d %H:%M:%S')}")
                
                # Add a small delay between requests to avoid rate limiting
                time.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Error saving announcement {announcement.get('dbId')} to Airtable: {str(e)}", exc_info=True)
                
                # Save error details for debugging
                if announcement.get("dbId") == self.target_announcement_id:
                    with open(os.path.join(self.debug_dir, f"error_saving_{self.target_announcement_id}.txt"), "w") as f:
                        f.write(f"Error saving announcement: {str(e)}")
        
        logger.info(f"Successfully saved {success_count} announcements to Airtable")
        return success_count

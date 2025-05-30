"""
Task for fetching announcements from SchoolConnect and storing them in Airtable.
"""

import logging
import time
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
    
    def execute(self, username: str, password: str, max_pages: int = 5) -> Dict[str, Any]:
        """
        Execute the task to fetch announcements and store them in Airtable.
        
        Args:
            username: SchoolConnect username
            password: SchoolConnect password
            max_pages: Maximum number of pages to fetch
            
        Returns:
            Dictionary with task results
        """
        logger.info("Starting announcement fetch task")
        
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
        
        # Fetch announcements with pagination
        all_announcements = []
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
            all_announcements.extend(announcements)
            
            has_next_page = result.get("hasNextPage", False)
            end_cursor = result.get("endCursor")
            page_count += 1
            
            logger.info(f"Fetched {len(announcements)} announcements on page {page_count}")
            
            # Add a small delay between requests
            time.sleep(1)
        
        logger.info(f"Total announcements fetched: {len(all_announcements)}")
        
        # Process announcements and fetch documents
        processed_announcements = []
        for announcement in all_announcements:
            try:
                # Fetch documents for this announcement
                documents = client.fetch_announcement_documents(announcement["id"])
                announcement["documents"] = documents
                
                processed_announcements.append(announcement)
                logger.info(f"Processed announcement {announcement['dbId']} with {len(documents)} documents")
            except Exception as e:
                logger.error(f"Error processing announcement {announcement.get('dbId')}: {str(e)}", exc_info=True)
        
        # Save to Airtable
        saved_count = self._save_to_airtable(processed_announcements)
        
        return {
            "success": True,
            "announcements_processed": len(processed_announcements),
            "announcements_saved": saved_count
        }
    
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
                # Extract document URLs (PDF only)
                attachments = []
                if announcement.get("documents"):
                    pdf_docs = [doc for doc in announcement["documents"] 
                               if doc.get("contentType") == "application/pdf" or 
                               (doc.get("fileFilename") and doc.get("fileFilename").lower().endswith('.pdf'))]
                    
                    # Process up to 5 PDF documents
                    docs_to_process = pdf_docs[:5]
                    
                    for doc in docs_to_process:
                        if doc.get("fileUrl") and doc.get("fileFilename"):
                            attachments.append({
                                "url": doc.get("fileUrl"),
                                "filename": doc.get("fileFilename")
                            })
                
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
                
                # Save to Airtable
                result = self.airtable_client.create_record(record)
                if result:
                    success_count += 1
                    logger.info(f"Successfully saved announcement {announcement['dbId']} to Airtable")
                else:
                    logger.error(f"Failed to save announcement {announcement['dbId']} to Airtable")
                
                # Add a small delay between requests to avoid rate limiting
                time.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Error saving announcement {announcement.get('dbId')} to Airtable: {str(e)}", exc_info=True)
        
        logger.info(f"Successfully saved {success_count} announcements to Airtable")
        return success_count

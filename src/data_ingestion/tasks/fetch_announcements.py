"""
Task for fetching announcements from SchoolConnect and storing them in Airtable.

Document Handling Flow:
1. Authentication: The system authenticates with SchoolConnect
2. Announcement Fetching: Paginated announcements are retrieved from the API
3. Document Fetching: For each announcement, documents are fetched using the announcement's dbId
4. PDF Filtering: Documents are filtered to include only PDFs (excluding images)
   - PDFs are identified by content type, filename extension, or URL extension
   - Images and other non-PDF files are explicitly excluded
5. Attachment Creation: Document URLs are used directly in Airtable attachments
   - The system verifies document accessibility by attempting to download each file
   - Only accessible documents are included as attachments

Important Notes:
- The SchoolConnect API requires re-authentication before document fetching
- Only PDF documents are included as attachments (images are excluded)
- Document URLs from SchoolConnect are directly usable by Airtable
"""

import logging
import time
import json
import os
import base64
import tempfile
import requests
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
    
    # The _encode_announcement_id method has been removed as it's no longer used.
    # The current implementation uses dbId directly with the format "Announcement:{dbId}"
    
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
        
        # Continue with normal pagination to get announcements
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
                # IMPORTANT: Use the 'dbId' field as in the original ClassTagWorkflowApp
                # This is the numeric ID that needs to be formatted as "Announcement:dbId"
                documents = client.fetch_announcement_documents(announcement["dbId"])
                announcement["documents"] = documents
                
                # Log document URLs for debugging
                logger.info(f"Document URLs for announcement {announcement.get('dbId')}: {[doc.get('fileUrl') for doc in documents]}")
                
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
        saved_count = self._save_to_airtable(processed_announcements, client)
        
        return {
            "success": True,
            "announcements_processed": len(processed_announcements),
            "announcements_saved": saved_count,
            "target_found": list(self.target_found)
        }
    
    def _download_document(self, client: SchoolConnectClient, url: str, filename: str) -> bool:
        """
        Download a document using the authenticated session to verify it exists.
        
        Args:
            client: SchoolConnectClient with authenticated session
            url: URL of the document
            filename: Name of the document
            
        Returns:
            True if download was successful, False otherwise
        """
        try:
            logger.info(f"Verifying document accessibility: {url}")
            
            # Use the client's session to download the file (just to verify it exists)
            response = client.session.get(url, timeout=30)
            response.raise_for_status()
            
            # If we got here, the file is accessible
            logger.info(f"Successfully verified document accessibility: {filename}, size: {len(response.content)} bytes")
            return True
        except Exception as e:
            logger.error(f"Error verifying document accessibility: {str(e)}", exc_info=True)
            return False
    
    def _save_to_airtable(self, announcements: List[Dict[str, Any]], client: SchoolConnectClient) -> int:
        """
        Save announcements to Airtable.
        
        Args:
            announcements: List of processed announcements
            client: SchoolConnectClient with authenticated session
            
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
                    
                    # Strict PDF detection logic - only include actual PDFs, exclude images
                    pdf_docs = []
                    for doc in announcement.get("documents", []):
                        is_pdf = False
                        # Check content type - primary method
                        if doc.get("contentType") == "application/pdf":
                            is_pdf = True
                            if is_target_announcement:
                                logger.info(f"PDF detected by content type for {announcement_id}: {doc.get('contentType')}")
                        # Check filename extension - secondary method
                        elif doc.get("fileFilename") and doc.get("fileFilename").lower().endswith('.pdf'):
                            is_pdf = True
                            if is_target_announcement:
                                logger.info(f"PDF detected by filename for {announcement_id}: {doc.get('fileFilename')}")
                        # Check URL extension - tertiary method
                        elif doc.get("fileUrl") and doc.get("fileUrl").lower().endswith('.pdf'):
                            is_pdf = True
                            if is_target_announcement:
                                logger.info(f"PDF detected by URL for {announcement_id}: {doc.get('fileUrl')}")
                        
                        # Explicitly exclude image files by checking content type and extensions
                        if is_pdf and doc.get("contentType"):
                            if "image/" in doc.get("contentType").lower():
                                is_pdf = False
                                if is_target_announcement:
                                    logger.info(f"Excluding image by content type: {doc.get('contentType')}")
                        
                        # Exclude by filename extension if it's an image format
                        if is_pdf and doc.get("fileFilename"):
                            image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp']
                            for ext in image_extensions:
                                if doc.get("fileFilename").lower().endswith(ext):
                                    is_pdf = False
                                    if is_target_announcement:
                                        logger.info(f"Excluding image by filename extension: {doc.get('fileFilename')}")
                                    break
                            
                        if is_pdf:
                            pdf_docs.append(doc)
                            if is_target_announcement:
                                logger.info(f"PDF added to processing list for {announcement_id}: {doc.get('fileFilename')} with content type {doc.get('contentType')}")
                    
                    # Process all PDF documents (removed limit of 5)
                    docs_to_process = pdf_docs
                    
                    if is_target_announcement:
                        logger.info(f"PDF documents found for announcement {announcement_id}: {len(pdf_docs)}")
                    
                    for doc in docs_to_process:
                        if doc.get("fileUrl") and doc.get("fileFilename"):
                            # Ensure filename exists, create one if missing
                            filename = doc.get("fileFilename")
                            if not filename:
                                # Extract filename from URL or use default
                                url_parts = doc.get("fileUrl", "").split("/")
                                filename = url_parts[-1] if url_parts else f"document_{len(attachments)}.pdf"
                            
                            # Verify document accessibility by downloading it with authenticated session
                            # This matches the original ClassTagWorkflowApp approach
                            is_accessible = self._download_document(client, doc.get("fileUrl"), filename)
                            
                            if is_accessible:
                                # Use direct URL format for Airtable attachments
                                # This matches the original ClassTagWorkflowApp approach
                                attachments.append({
                                    "url": doc.get("fileUrl"),
                                    "filename": filename
                                })
                                
                                if is_target_announcement:
                                    logger.info(f"Added attachment for {announcement_id}: {filename} with URL: {doc.get('fileUrl')}")
                            else:
                                logger.error(f"Document not accessible for {announcement_id}: {doc.get('fileUrl')}")
                
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
                
                # Save to Airtable (with duplicate check)
                result = self.airtable_client.create_record(record)
                if result:
                    if result.get("id") == "existing":
                        logger.info(f"Skipped duplicate announcement {announcement['dbId']} in Airtable")
                    else:
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

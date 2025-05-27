"""
Airtable tool for AI agent to access and analyze announcements.
"""

import os
import requests
import logging
from typing import Dict, List, Optional, Any, Tuple

from src.storage.airtable.client import AirtableClient
from src.core.config import get_settings

logger = logging.getLogger("schoolconnect_ai")

class AirtableTool:
    """Tool for AI agent to interact with Airtable data."""
    
    def __init__(self):
        """Initialize the Airtable tool."""
        self.client = AirtableClient()
        self.settings = get_settings()
        self.download_dir = os.path.join(self.settings.TEMP_FILE_DIR, "agent_downloads")
        os.makedirs(self.download_dir, exist_ok=True)
    
    def get_all_announcements(self) -> List[Dict[str, Any]]:
        """
        Fetch all announcements from Airtable.
        
        Returns:
            List of announcement records or error message
        """
        if not self.client.airtable:
            error_msg = "Error: Airtable connection not initialized."
            logger.error(error_msg)
            return error_msg
        
        try:
            records = self.client.get_all_records()
            if not records:
                return "No announcements found."
            
            return [record["fields"] for record in records if "fields" in record]
        except Exception as e:
            error_msg = f"Error fetching all announcements: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return error_msg
    
    def search_announcements(self, search_text: str) -> List[Dict[str, Any]]:
        """
        Search announcements by text in Title or Description fields.
        
        Args:
            search_text: Text to search for
            
        Returns:
            List of matching announcements or error message
        """
        if not self.client.airtable:
            error_msg = "Error: Airtable connection not initialized."
            logger.error(error_msg)
            return error_msg
        
        try:
            records = self.client.search_records(search_text)
            if not records:
                return f"No announcements found matching '{search_text}'."
            
            return [record["fields"] for record in records if "fields" in record]
        except Exception as e:
            error_msg = f"Error searching announcements for '{search_text}': {str(e)}"
            logger.error(error_msg, exc_info=True)
            return error_msg
    
    def _get_first_attachment_url(self, record_fields: Dict[str, Any]) -> Tuple[Optional[str], Optional[str]]:
        """
        Helper to get the URL and filename of the first attachment from a record.
        
        Args:
            record_fields: Record fields dictionary
            
        Returns:
            Tuple of (url, filename) or (None, None) if no attachment found
        """
        attachments = record_fields.get("Attachments")
        if attachments and isinstance(attachments, list) and len(attachments) > 0:
            first_attachment = attachments[0]
            if isinstance(first_attachment, dict) and "url" in first_attachment:
                return first_attachment["url"], first_attachment.get("filename", "downloaded_file")
        return None, None
    
    def get_attachment_from_announcement(self, announcement_id: Optional[str] = None, 
                                        search_term: Optional[str] = None, 
                                        get_latest: bool = False) -> Tuple[str, Optional[str]]:
        """
        Gets the attachment URL and filename from a specific announcement.
        Priority: announcement_id, then search_term, then get_latest.
        
        Args:
            announcement_id: Airtable record ID
            search_term: Text to search for in Title or Description
            get_latest: Whether to get the latest announcement
            
        Returns:
            Tuple of (url or error message, filename)
        """
        if not self.client.airtable:
            return "Error: Airtable connection not initialized.", None
        
        target_record = None
        try:
            if announcement_id:
                record = self.client.get_record_by_id(announcement_id)
                if record:
                    target_record = record
                else:
                    return f"Error: Announcement with ID '{announcement_id}' not found.", None
            elif search_term:
                results = self.search_announcements(search_term)
                if isinstance(results, str):  # Error or no results
                    return f"Could not find announcement via search term '{search_term}' to get attachment: {results}", None
                if results:  # results is a list of records
                    target_record = {"fields": results[0]}  # Get the first matching announcement
                else:
                    return f"No announcement found matching search term '{search_term}' to get attachment from.", None
            elif get_latest:
                record = self.client.get_latest_record()
                if record:
                    target_record = record
                else:
                    return "Error: Could not retrieve the latest announcement or no announcements exist.", None
            else:
                return "Error: No criteria (ID, search term, or latest) provided to find an announcement.", None
            
            if target_record:
                url, filename = self._get_first_attachment_url(target_record["fields"])
                if url and filename:
                    return url, filename
                else:
                    ann_title = target_record["fields"].get("Title", "[Unknown Title]")
                    return f"No attachment found in the announcement titled '{ann_title}'.", None
            else:
                # This case should ideally be caught by earlier checks
                return "Error: No matching announcement found to get attachment from.", None
        except Exception as e:
            error_msg = f"Error getting attachment: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return error_msg, None
    
    def download_file(self, url: str) -> str:
        """
        Downloads a file from a URL to a local path.
        
        Args:
            url: URL of the file to download
            
        Returns:
            Filepath or error string
        """
        if not url:
            return "Error: No URL provided for download."
        
        try:
            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()
            
            # Try to get filename from content-disposition header
            content_disposition = response.headers.get("content-disposition")
            filename = None
            if content_disposition:
                import re
                fname = re.findall("filename=(.+)", content_disposition)
                if fname:
                    filename = fname[0].strip("\"").strip("'")
            
            # If not found in header, extract from URL
            if not filename:
                from urllib.parse import unquote
                filename = unquote(url.split("/")[-1].split("?")[0])
            
            # Fallback filename
            if not filename:
                filename = "downloaded_attachment"
            
            # Ensure filename has an extension
            if "." not in os.path.basename(filename):
                content_type = response.headers.get("content-type", "").lower()
                if "pdf" in content_type:
                    filename += ".pdf"
                elif "openxmlformats-officedocument.wordprocessingml.document" in content_type:
                    filename += ".docx"
                elif "plain" in content_type:
                    filename += ".txt"
                else:
                    filename += ".pdf"  # Default
            
            # Sanitize filename
            filename = "".join(c for c in filename if c.isalnum() or c in (".", "-", "_")).rstrip()
            if not filename:
                filename = "sanitized_download.pdf"
            
            local_filepath = os.path.join(self.download_dir, filename)
            
            with open(local_filepath, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            logger.info(f"File downloaded successfully to {local_filepath}")
            return local_filepath
        except Exception as e:
            error_msg = f"Error downloading file from {url}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return error_msg

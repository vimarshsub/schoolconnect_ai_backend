"""
Airtable tool for AI agent to access and analyze announcements.
"""

import os
import requests
import logging
import calendar
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import dateutil.parser
import dateutil.tz

from src.storage.airtable.client import AirtableClient
from src.core.config import get_settings
from src.utils.date_utils import DateUtils

logger = logging.getLogger("schoolconnect_ai")

class AirtableTool:
    """Tool for AI agent to interact with Airtable data."""
    
    def __init__(self):
        """Initialize the Airtable tool."""
        self.client = AirtableClient()
        self.settings = get_settings()
        self.download_dir = os.path.join(self.settings.TEMP_FILE_DIR, "agent_downloads")
        os.makedirs(self.download_dir, exist_ok=True)
    
    def get_all_announcements(self, input_text: Optional[str] = None) -> Dict[str, Any]:
        """
        Fetch all announcements from Airtable.
        
        Args:
            input_text: Optional input text (not used, but required for agent tool compatibility)
            
        Returns:
            Dictionary with announcements list and count
        """
        if not self.client.airtable:
            error_msg = "Error: Airtable connection not initialized."
            logger.error(error_msg)
            return {"count": 0, "announcements": [], "error": error_msg}
        
        try:
            records = self.client.get_all_records()
            if not records:
                return {"count": 0, "announcements": [], "message": "No announcements found."}
            
            announcements = [record["fields"] for record in records if "fields" in record]
            return {
                "count": len(announcements),
                "announcements": announcements,
                "message": f"Found {len(announcements)} announcements."
            }
        except Exception as e:
            error_msg = f"Error fetching all announcements: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {"count": 0, "announcements": [], "error": error_msg}
    
    def search_announcements(self, search_text: str) -> List[Dict[str, Any]]:
        """
        Search announcements by text in Title, Description, or Sender fields.
        
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
            # Escape single quotes in search text to prevent formula syntax errors
            escaped_search_text = search_text.replace("'", "\\'")
            
            # Create a formula that searches across multiple fields using FIND()
            # FIND() returns position of substring (1-based) or error if not found
            # We use OR to check if any field contains the search text
            formula = (
                f"OR("
                f"FIND(LOWER('{escaped_search_text}'), LOWER({{Title}})), "
                f"FIND(LOWER('{escaped_search_text}'), LOWER({{Description}})), "
                f"FIND(LOWER('{escaped_search_text}'), LOWER({{SentByUser}}))"
                f")"
            )
            
            # Use native Airtable filtering instead of fetching all records
            matched_records = self.client.get_records_with_formula(formula)
            
            if not matched_records:
                return f"No announcements found matching '{search_text}'."
            
            return [record["fields"] for record in matched_records if "fields" in record]
        except Exception as e:
            error_msg = f"Error searching announcements for '{search_text}': {str(e)}"
            logger.error(error_msg, exc_info=True)
            return error_msg
    
    def search_announcements_by_sender(self, sender_name: str) -> Dict[str, Any]:
        """
        Search announcements by sender name.
        
        Args:
            sender_name: Name of the sender to search for
            
        Returns:
            Dictionary with filtered announcements list and count
        """
        if not self.client.airtable:
            error_msg = "Error: Airtable connection not initialized."
            logger.error(error_msg)
            return {"count": 0, "announcements": [], "error": error_msg}
        
        try:
            # HYBRID APPROACH: First try optimized search with Airtable formula
            # Escape single quotes in sender name to prevent formula syntax errors
            escaped_sender_name = sender_name.replace("'", "\\'")
            
            # Create a formula that searches for the sender name in the SentByUser field
            formula = f"FIND(LOWER('{escaped_sender_name}'), LOWER({{SentByUser}}))"
            
            # Use native Airtable filtering first
            matched_records = self.client.get_records_with_formula(formula)
            announcements = [record["fields"] for record in matched_records if "fields" in record]
            
            # If no results found with exact matching, fall back to fuzzy matching
            if not announcements:
                logger.info(f"No exact matches found for sender '{sender_name}', falling back to fuzzy matching")
                
                # Import fuzzy matching library
                from rapidfuzz import fuzz, process
                
                # Get all records to perform fuzzy matching
                all_records = self.client.get_all_records()
                
                # Extract unique sender names
                all_senders = set()
                for record in all_records:
                    if "fields" in record and "SentByUser" in record["fields"]:
                        all_senders.add(record["fields"]["SentByUser"])
                
                # Find the best matching sender name with a similarity threshold
                SIMILARITY_THRESHOLD = 80  # Minimum similarity score (0-100)
                best_matches = process.extract(
                    sender_name, 
                    all_senders, 
                    scorer=fuzz.token_sort_ratio,
                    limit=3,
                    score_cutoff=SIMILARITY_THRESHOLD
                )
                
                # If we found fuzzy matches
                if best_matches:
                    logger.info(f"Found fuzzy matches for '{sender_name}': {best_matches}")
                    
                    # Filter records by the best matching sender names
                    fuzzy_matched_records = []
                    for record in all_records:
                        if ("fields" in record and 
                            "SentByUser" in record["fields"] and 
                            any(record["fields"]["SentByUser"] == match[0] for match in best_matches)):
                            fuzzy_matched_records.append(record)
                    
                    announcements = [record["fields"] for record in fuzzy_matched_records]
                    
                    return {
                        "count": len(announcements),
                        "announcements": announcements,
                        "message": f"Found {len(announcements)} announcements from sender similar to '{sender_name}'."
                    }
            
            # Return results from either exact or fuzzy matching
            if not announcements:
                return {"count": 0, "announcements": [], "message": f"No announcements found from sender '{sender_name}'."}
            
            return {
                "count": len(announcements),
                "announcements": announcements,
                "message": f"Found {len(announcements)} announcements from sender '{sender_name}'."
            }
        except Exception as e:
            error_msg = f"Error searching announcements by sender '{sender_name}': {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {"count": 0, "announcements": [], "error": error_msg}
    
    def filter_announcements_by_date(self, date_query: str) -> Dict[str, Any]:
        """
        Filter announcements by date based on the SentTime field.
        
        Args:
            date_query: Date query string (e.g., "in May", "last week", "2023-01-01")
            
        Returns:
            Dictionary with filtered announcements list and count
        """
        if not self.client.airtable:
            error_msg = "Error: Airtable connection not initialized."
            logger.error(error_msg)
            return {"count": 0, "announcements": [], "error": error_msg}
        
        try:
            # Parse the date query
            date_query = date_query.lower().strip()
            
            # Handle month names (e.g., "in May", "sent in May")
            month_names = {month.lower(): i for i, month in enumerate(calendar.month_name) if month}
            for month_name, month_num in month_names.items():
                if month_name in date_query:
                    # Get current year for default
                    current_year = datetime.now().year
                    
                    # Create start and end dates for the month (as timezone-aware)
                    start_date = datetime(current_year, month_num, 1).replace(tzinfo=dateutil.tz.UTC)
                    
                    # Handle December correctly
                    if month_num == 12:
                        end_date = datetime(current_year + 1, 1, 1).replace(tzinfo=dateutil.tz.UTC)
                    else:
                        end_date = datetime(current_year, month_num + 1, 1).replace(tzinfo=dateutil.tz.UTC)
                    
                    # Format dates for Airtable formula
                    start_date_str = start_date.strftime('%Y-%m-%dT%H:%M:%S.000Z')
                    end_date_str = end_date.strftime('%Y-%m-%dT%H:%M:%S.000Z')
                    
                    # Create formula for date range filtering
                    formula = f"AND(IS_AFTER({{SentTime}}, '{start_date_str}'), IS_BEFORE({{SentTime}}, '{end_date_str}'))"
                    
                    # Use native Airtable filtering
                    matched_records = self.client.get_records_with_formula(formula)
                    
                    announcements = [record["fields"] for record in matched_records if "fields" in record]
                    return {
                        "count": len(announcements),
                        "announcements": announcements,
                        "message": f"Found {len(announcements)} announcements from {calendar.month_name[month_num]}."
                    }
            
            # Try to extract a date range
            start_date, end_date = DateUtils.extract_date_time_range(date_query)
            
            # If we got a valid date range, add timezone info and filter by it
            if start_date and end_date:
                # Make timezone-aware
                start_date = start_date.replace(tzinfo=dateutil.tz.UTC)
                end_date = end_date.replace(tzinfo=dateutil.tz.UTC)
                
                # Format dates for Airtable formula
                start_date_str = start_date.strftime('%Y-%m-%dT%H:%M:%S.000Z')
                end_date_str = end_date.strftime('%Y-%m-%dT%H:%M:%S.000Z')
                
                # Create formula for date range filtering
                formula = f"AND(IS_AFTER({{SentTime}}, '{start_date_str}'), IS_BEFORE({{SentTime}}, '{end_date_str}'))"
                
                # Use native Airtable filtering
                matched_records = self.client.get_records_with_formula(formula)
                
                announcements = [record["fields"] for record in matched_records if "fields" in record]
                return {
                    "count": len(announcements),
                    "announcements": announcements,
                    "message": f"Found {len(announcements)} announcements between {start_date.strftime('%Y-%m-%d')} and {end_date.strftime('%Y-%m-%d')}."
                }
            
            # Try to parse a single date
            single_date = DateUtils.parse_date_time(date_query)
            if single_date:
                # Make timezone-aware
                single_date = single_date.replace(tzinfo=dateutil.tz.UTC)
                # For a single date, get announcements from that day
                next_day = single_date + timedelta(days=1)
                
                # Format dates for Airtable formula
                start_date_str = single_date.strftime('%Y-%m-%dT%H:%M:%S.000Z')
                end_date_str = next_day.strftime('%Y-%m-%dT%H:%M:%S.000Z')
                
                # Create formula for date range filtering
                formula = f"AND(IS_AFTER({{SentTime}}, '{start_date_str}'), IS_BEFORE({{SentTime}}, '{end_date_str}'))"
                
                # Use native Airtable filtering
                matched_records = self.client.get_records_with_formula(formula)
                
                announcements = [record["fields"] for record in matched_records if "fields" in record]
                return {
                    "count": len(announcements),
                    "announcements": announcements,
                    "message": f"Found {len(announcements)} announcements from {single_date.strftime('%Y-%m-%d')}."
                }
            
            # If we couldn't parse the date query, return an error
            return {
                "count": 0, 
                "announcements": [], 
                "error": f"Could not parse date query: '{date_query}'. Please try a different format."
            }
            
        except Exception as e:
            error_msg = f"Error filtering announcements by date: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {"count": 0, "announcements": [], "error": error_msg}
    
    def _filter_records_by_date_range(self, records: List[Dict[str, Any]], 
                                     start_date: datetime, 
                                     end_date: datetime) -> List[Dict[str, Any]]:
        """
        Filter records by date range based on SentTime field.
        
        Args:
            records: List of records to filter
            start_date: Start date (inclusive)
            end_date: End date (exclusive)
            
        Returns:
            Filtered list of records
        """
        filtered_records = []
        
        for record in records:
            fields = record.get("fields", {})
            sent_time = fields.get("SentTime")
            
            if not sent_time:
                continue
            
            # Parse the sent time with dateutil which handles ISO 8601 with timezone
            try:
                # Use dateutil.parser which properly handles ISO 8601 with timezone
                sent_datetime = dateutil.parser.parse(sent_time)
                
                # Ensure both dates are timezone-aware for comparison
                if sent_datetime.tzinfo is None:
                    sent_datetime = sent_datetime.replace(tzinfo=dateutil.tz.UTC)
                
                if start_date <= sent_datetime < end_date:
                    filtered_records.append(record)
            except Exception as e:
                logger.warning(f"Error parsing date '{sent_time}': {str(e)}")
                continue
        
        return filtered_records
    
    def _parse_sent_time(self, sent_time_str: str) -> Optional[datetime]:
        """
        Parse the SentTime field from Airtable format to a datetime object.
        
        Args:
            sent_time_str: Date/time string to parse
            
        Returns:
            Parsed datetime object or None if parsing failed
        """
        if not sent_time_str:
            return None
        
        try:
            # First try dateutil parser which handles most formats including ISO 8601
            try:
                return dateutil.parser.parse(sent_time_str)
            except Exception:
                pass
            
            # Check for ISO 8601 format with 'T' and possible 'Z' or timezone offset
            if 'T' in sent_time_str:
                # Handle ISO 8601 format
                # Remove milliseconds and timezone for simpler parsing
                iso_basic = re.sub(r'\.[\d]+', '', sent_time_str)  # Remove milliseconds
                iso_basic = re.sub(r'Z$', '', iso_basic)  # Remove Z suffix
                iso_basic = re.sub(r'[+-][\d:]+$', '', iso_basic)  # Remove timezone offset
                
                try:
                    return datetime.fromisoformat(iso_basic)
                except ValueError:
                    # If fromisoformat fails, try strptime with common ISO formats
                    iso_formats = [
                        "%Y-%m-%dT%H:%M:%S",
                        "%Y-%m-%dT%H:%M"
                    ]
                    for fmt in iso_formats:
                        try:
                            return datetime.strptime(iso_basic, fmt)
                        except ValueError:
                            continue
            
            # Remove timezone abbreviation as it's not easily parsed by datetime
            sent_time_str = re.sub(r'\s+[A-Z]{3,4}$', '', sent_time_str)
            
            # Try multiple date formats
            formats = [
                "%m/%d/%Y %I:%M%p",  # 5/7/2025 2:29pm
                "%m/%d/%Y %H:%M",    # 5/7/2025 14:29
                "%m/%d/%Y",          # 5/7/2025
                "%Y-%m-%d %H:%M:%S", # 2025-05-07 14:29:00
                "%Y-%m-%d %H:%M",    # 2025-05-07 14:29
                "%Y-%m-%d"           # 2025-05-07
            ]
            
            for fmt in formats:
                try:
                    return datetime.strptime(sent_time_str, fmt)
                except ValueError:
                    continue
            
            return None
        except Exception as e:
            logger.warning(f"Error parsing date '{sent_time_str}': {str(e)}")
            return None
    
    def _get_first_attachment_url(self, record_fields: Dict[str, Any]) -> Tuple[Optional[str], Optional[str]]:
        """
        Helper to get the URL and filename of the first attachment from a record.
        
        Args:
            record_fields: Record fields dictionary
            
        Returns:
            Tuple of (URL, filename) or (None, None) if no attachment found
        """
        # Try different field names for attachments (for compatibility)
        attachment_field_names = ["Attachments", "Documents", "Files", "Attachment"]
        
        for field_name in attachment_field_names:
            attachments = record_fields.get(field_name)
            if attachments and isinstance(attachments, list) and len(attachments) > 0:
                first_attachment = attachments[0]
                if isinstance(first_attachment, dict) and "url" in first_attachment:
                    url = first_attachment.get("url")
                    filename = first_attachment.get("filename", "downloaded_file")
                    logger.info(f"Found attachment in field '{field_name}': {url}, filename: {filename}")
                    return url, filename
        
        # If we get here, no attachment was found
        logger.warning(f"No attachments found in record fields: {list(record_fields.keys())}")
        return None, None
    
    def get_attachment_from_announcement(self, announcement_id: Optional[str] = None, 
                                        search_term: Optional[str] = None,
                                        get_latest: bool = False) -> Tuple[str, Optional[str]]:
        """
        Get attachment URL from an announcement.
        
        Args:
            announcement_id: Airtable record ID
            search_term: Text to search for in Title or Description
            get_latest: Whether to get the latest announcement
            
        Returns:
            Tuple of (URL, filename) or (error message, None)
        """
        if not self.client.airtable:
            error_msg = "Error: Airtable connection not initialized."
            logger.error(error_msg)
            return error_msg, None
        
        try:
            # Get the announcement record
            record = None
            target_record_fields = None
            
            logger.info(f"Attempting to get attachment: id={announcement_id}, search='{search_term}', latest={get_latest}")
            
            if announcement_id:
                # First try direct record retrieval by ID
                logger.info(f"Attempting to get record by ID: {announcement_id}")
                record = self.client.get_record_by_id(announcement_id)
                
                if record and "fields" in record:
                    target_record_fields = record["fields"]
                    logger.info(f"Found record by ID: {announcement_id}")
                else:
                    # If direct ID lookup fails, try searching by title (in case announcement_id is actually a title)
                    logger.info(f"Record not found by ID, trying as search term: {announcement_id}")
                    search_results = self.search_announcements(announcement_id)
                    
                    if isinstance(search_results, list) and search_results:
                        # Use the first matching record
                        target_record_fields = search_results[0]
                        logger.info(f"Found record by searching for: {announcement_id}")
                    else:
                        error_msg = f"Error: Announcement with ID or title '{announcement_id}' not found."
                        logger.warning(error_msg)
                        return error_msg, None
            
            elif search_term:
                # Search for the announcement
                logger.info(f"Searching for announcement with term: {search_term}")
                search_results = self.search_announcements(search_term)
                
                if isinstance(search_results, list) and search_results:
                    # Use the first matching record
                    target_record_fields = search_results[0]
                    logger.info(f"Found record by search term: {search_term}")
                else:
                    error_msg = f"No announcement found matching search term '{search_term}'."
                    logger.warning(error_msg)
                    return error_msg, None
            
            elif get_latest:
                # Get the latest announcement
                logger.info("Getting latest announcement")
                latest_record = self.client.get_latest_record()
                
                if latest_record and "fields" in latest_record:
                    target_record_fields = latest_record["fields"]
                    logger.info("Found latest record")
                else:
                    error_msg = "Error: Could not retrieve the latest announcement or no announcements exist."
                    logger.warning(error_msg)
                    return error_msg, None
            
            else:
                error_msg = "Error: No criteria (ID, search term, or latest) provided to find an announcement."
                logger.warning(error_msg)
                return error_msg, None
            
            # Get attachment URL from the record fields
            if target_record_fields:
                url, filename = self._get_first_attachment_url(target_record_fields)
                
                if url and filename:
                    logger.info(f"Found attachment URL: {url}, filename: {filename}")
                    return url, filename
                else:
                    ann_title = target_record_fields.get("Title", "[Unknown Title]")
                    error_msg = f"No attachment found in the announcement titled '{ann_title}'."
                    logger.warning(error_msg)
                    return error_msg, None
            else:
                # This case should ideally be caught by earlier checks
                error_msg = "Error: No matching announcement found to get attachment from."
                logger.warning(error_msg)
                return error_msg, None
        
        except Exception as e:
            error_msg = f"Error getting attachment: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return error_msg, None
    
    def download_file(self, url: str) -> str:
        """
        Download a file from a URL.
        
        Args:
            url: URL to download from
            
        Returns:
            Local file path or error message
        """
        if not url:
            error_msg = "Error: No URL provided for download."
            logger.error(error_msg)
            return error_msg
        
        try:
            logger.info(f"Attempting to download file from URL: {url}")
            
            # Create download directory if it doesn't exist
            os.makedirs(self.download_dir, exist_ok=True)
            
            # Get response with stream=True for large files
            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()
            
            # Try to get filename from Content-Disposition header
            content_disposition = response.headers.get("content-disposition")
            filename = None
            
            if content_disposition:
                import re
                fname = re.findall("filename=(.+)", content_disposition)
                if fname:
                    filename = fname[0].strip("\"").strip("'")  # Handle both quote types
            
            # If no filename in header, extract from URL
            if not filename:
                from urllib.parse import unquote
                filename = unquote(url.split("/")[-1].split("?")[0])
            
            # Fallback filename if still not found
            if not filename or filename == "":
                filename = "downloaded_attachment"
            
            # Ensure filename has an extension based on content-type
            if "." not in os.path.basename(filename):
                content_type = response.headers.get("content-type", "").lower()
                if "pdf" in content_type:
                    filename += ".pdf"
                elif "openxmlformats-officedocument.wordprocessingml.document" in content_type:
                    filename += ".docx"
                elif "plain" in content_type:
                    filename += ".txt"
                else:
                    filename += ".pdf"  # Default to PDF
            
            # Sanitize filename to prevent path traversal or invalid characters
            filename = "".join(c for c in filename if c.isalnum() or c in (".", "-", "_")).rstrip()
            if not filename:
                filename = "sanitized_download.pdf"
            
            # Create full local path
            local_filepath = os.path.join(self.download_dir, filename)
            
            # Download the file in chunks
            with open(local_filepath, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            logger.info(f"File downloaded successfully to {local_filepath}")
            return local_filepath
        
        except requests.exceptions.Timeout:
            error_msg = f"Error downloading file from {url}: Request timed out."
            logger.error(error_msg)
            return error_msg
        
        except requests.exceptions.RequestException as e:
            error_msg = f"Error downloading file from {url}: {str(e)}"
            logger.error(error_msg)
            return error_msg
        
        except IOError as e:
            error_msg = f"Error saving file: {str(e)}"
            logger.error(error_msg)
            return error_msg
        
        except Exception as e:
            error_msg = f"An unexpected error occurred during download: {str(e)}"
            logger.error(error_msg)
            return error_msg

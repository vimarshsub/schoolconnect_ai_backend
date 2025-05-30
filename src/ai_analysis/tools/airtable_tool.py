"""
Airtable tool for AI agent to access and analyze announcements.
"""

import os
import requests
import logging
<<<<<<< HEAD
import calendar
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import dateutil.parser
import dateutil.tz

from src.storage.airtable.client import AirtableClient
from src.core.config import get_settings
from src.utils.date_utils import DateUtils
=======
from typing import Dict, List, Optional, Any, Tuple

from src.storage.airtable.client import AirtableClient
from src.core.config import get_settings
>>>>>>> 2253f288b9c4533346f3133f2f1128116c5c12c8

logger = logging.getLogger("schoolconnect_ai")

class AirtableTool:
    """Tool for AI agent to interact with Airtable data."""
    
    def __init__(self):
        """Initialize the Airtable tool."""
        self.client = AirtableClient()
        self.settings = get_settings()
        self.download_dir = os.path.join(self.settings.TEMP_FILE_DIR, "agent_downloads")
        os.makedirs(self.download_dir, exist_ok=True)
    
<<<<<<< HEAD
    def get_all_announcements(self) -> Dict[str, Any]:
        """
        Fetch all announcements from Airtable.
        
        Returns:
            Dictionary with announcements list and count
=======
    def get_all_announcements(self, input_text: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Fetch all announcements from Airtable.
        
        Args:
            input_text: Optional input text (not used, but required for agent tool compatibility)
            
        Returns:
            List of announcement records or error message
>>>>>>> 2253f288b9c4533346f3133f2f1128116c5c12c8
        """
        if not self.client.airtable:
            error_msg = "Error: Airtable connection not initialized."
            logger.error(error_msg)
<<<<<<< HEAD
            return {"count": 0, "announcements": [], "error": error_msg}
=======
            return error_msg
>>>>>>> 2253f288b9c4533346f3133f2f1128116c5c12c8
        
        try:
            records = self.client.get_all_records()
            if not records:
<<<<<<< HEAD
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
=======
                return "No announcements found."
            
            return [record["fields"] for record in records if "fields" in record]
        except Exception as e:
            error_msg = f"Error fetching all announcements: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return error_msg
    
    def search_announcements(self, search_text: str) -> List[Dict[str, Any]]:
        """
        Search announcements by text in Title or Description fields.
>>>>>>> 2253f288b9c4533346f3133f2f1128116c5c12c8
        
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
<<<<<<< HEAD
            # Get all records and filter locally for more flexible searching
            all_records = self.client.get_all_records()
            if not all_records:
                return f"No announcements found matching '{search_text}'."
            
            search_text_lower = search_text.lower()
            matched_records = []
            
            for record in all_records:
                fields = record.get("fields", {})
                title = fields.get("Title", "").lower()
                description = fields.get("Description", "").lower()
                sender = fields.get("SentByUser", "").lower()
                
                # Check if the search text matches any of the fields
                if (search_text_lower in title or 
                    search_text_lower in description or 
                    search_text_lower in sender):
                    matched_records.append(record)
            
            if not matched_records:
                return f"No announcements found matching '{search_text}'."
            
            return [record["fields"] for record in matched_records if "fields" in record]
=======
            records = self.client.search_records(search_text)
            if not records:
                return f"No announcements found matching '{search_text}'."
            
            return [record["fields"] for record in records if "fields" in record]
>>>>>>> 2253f288b9c4533346f3133f2f1128116c5c12c8
        except Exception as e:
            error_msg = f"Error searching announcements for '{search_text}': {str(e)}"
            logger.error(error_msg, exc_info=True)
            return error_msg
    
<<<<<<< HEAD
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
            # Get all records and filter locally
            all_records = self.client.get_all_records()
            if not all_records:
                return {"count": 0, "announcements": [], "message": f"No announcements found from sender '{sender_name}'."}
            
            sender_name_lower = sender_name.lower()
            matched_records = []
            
            for record in all_records:
                fields = record.get("fields", {})
                sender = fields.get("SentByUser", "").lower()
                
                if sender_name_lower in sender:
                    matched_records.append(record)
            
            announcements = [record["fields"] for record in matched_records if "fields" in record]
            
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
            # Get all announcements first
            all_records = self.client.get_all_records()
            if not all_records:
                return {"count": 0, "announcements": [], "message": "No announcements found."}
            
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
                    
                    # Filter records by this date range
                    filtered_records = self._filter_records_by_date_range(all_records, start_date, end_date)
                    
                    announcements = [record["fields"] for record in filtered_records if "fields" in record]
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
                
                filtered_records = self._filter_records_by_date_range(all_records, start_date, end_date)
                
                announcements = [record["fields"] for record in filtered_records if "fields" in record]
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
                filtered_records = self._filter_records_by_date_range(all_records, single_date, next_day)
                
                announcements = [record["fields"] for record in filtered_records if "fields" in record]
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
                "%Y-%m-%d %I:%M%p",  # 2025-05-07 2:29pm
                "%Y-%m-%d %H:%M",    # 2025-05-07 14:29
                "%m/%d/%Y",          # 5/7/2025 (date only)
                "%Y-%m-%d"           # 2025-05-07 (date only)
            ]
            
            for fmt in formats:
                try:
                    return datetime.strptime(sent_time_str, fmt)
                except ValueError:
                    continue
            
            # If none of the formats match, try a more flexible approach
            # Extract date and time parts
            date_match = re.search(r'(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})', sent_time_str)
            time_match = re.search(r'(\d{1,2}):(\d{2})(?:am|pm|AM|PM)?', sent_time_str)
            am_pm_match = re.search(r'(am|pm|AM|PM)', sent_time_str)
            
            if date_match:
                month, day, year = date_match.groups()
                # Handle 2-digit years
                if len(year) == 2:
                    year = f"20{year}" if int(year) < 50 else f"19{year}"
                
                if time_match:
                    hour, minute = time_match.groups()
                    hour = int(hour)
                    # Handle AM/PM
                    if am_pm_match:
                        am_pm = am_pm_match.group(1).lower()
                        if am_pm == 'pm' and hour < 12:
                            hour += 12
                        elif am_pm == 'am' and hour == 12:
                            hour = 0
                    
                    return datetime(int(year), int(month), int(day), hour, int(minute))
                else:
                    # Date only
                    return datetime(int(year), int(month), int(day))
            
            # If all parsing attempts fail
            logger.warning(f"Could not parse date string: {sent_time_str}")
            return None
            
        except Exception as e:
            logger.error(f"Error parsing date '{sent_time_str}': {str(e)}", exc_info=True)
            return None
    
=======
>>>>>>> 2253f288b9c4533346f3133f2f1128116c5c12c8
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

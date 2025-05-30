"""
Airtable client for storing and retrieving data.
"""

import os
import logging
from typing import Dict, List, Optional, Any
from airtable import Airtable

from src.core.config import get_settings

logger = logging.getLogger("schoolconnect_ai")

class AirtableClient:
    """Client for interacting with Airtable."""
    
    def __init__(self):
        """Initialize the Airtable client."""
        settings = get_settings()
        self.api_key = settings.AIRTABLE_API_KEY
        self.base_id = settings.AIRTABLE_BASE_ID
        self.table_name = settings.AIRTABLE_TABLE_NAME
        
        try:
            self.airtable = Airtable(self.base_id, self.table_name, self.api_key)
            # Test connection with a simple call
            self.airtable.get_all(max_records=1)
            logger.info("Airtable connection initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing Airtable connection: {str(e)}", exc_info=True)
            self.airtable = None
    
    def create_record(self, record_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Create a new record in Airtable.
        
        Args:
            record_data: Dictionary of field values
            
        Returns:
            Created record or None if creation failed
        """
        if not self.airtable:
            logger.error("Airtable connection not initialized")
            return None
        
        try:
            # Check if record_data contains attachments
            if "Attachments" in record_data:
                logger.info(f"Record contains attachments: {len(record_data['Attachments'])} files")
                
                # Ensure record is properly formatted for Airtable with fields wrapper
                # This is critical for attachments to work correctly
                formatted_record = {"fields": record_data}
                result = self.airtable.insert(formatted_record["fields"])
            else:
                # For records without attachments, use the standard approach
                result = self.airtable.insert(record_data)
                
            logger.info(f"Created record in Airtable with ID: {result.get('id')}")
            return result
        except Exception as e:
            logger.error(f"Error creating record in Airtable: {str(e)}", exc_info=True)
            return None
    
    def get_all_records(self) -> List[Dict[str, Any]]:
        """
        Get all records from Airtable.
        
        Returns:
            List of records
        """
        if not self.airtable:
            logger.error("Airtable connection not initialized")
            return []
        
        try:
            records = self.airtable.get_all()
            logger.info(f"Retrieved {len(records)} records from Airtable")
            return [{"id": record["id"], "fields": record["fields"]} for record in records]
        except Exception as e:
            logger.error(f"Error retrieving records from Airtable: {str(e)}", exc_info=True)
            return []
    
    def search_records(self, search_text: str) -> List[Dict[str, Any]]:
        """
        Search records in Airtable.
        
        Args:
            search_text: Text to search for in Title or Description fields
            
        Returns:
            List of matching records
        """
        if not self.airtable:
            logger.error("Airtable connection not initialized")
            return []
        
        try:
            all_records = self.get_all_records()
            search_text_lower = search_text.lower()
            
            matched_records = []
            for record in all_records:
                fields = record.get("fields", {})
                title = fields.get("Title", "").lower()
                description = fields.get("Description", "").lower()
                
                if search_text_lower in title or search_text_lower in description:
                    matched_records.append(record)
            
            logger.info(f"Found {len(matched_records)} records matching '{search_text}'")
            return matched_records
        except Exception as e:
            logger.error(f"Error searching records in Airtable: {str(e)}", exc_info=True)
            return []
    
    def get_record_by_id(self, record_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a record by ID.
        
        Args:
            record_id: Airtable record ID
            
        Returns:
            Record or None if not found
        """
        if not self.airtable:
            logger.error("Airtable connection not initialized")
            return None
        
        try:
            record = self.airtable.get(record_id)
            if record:
                logger.info(f"Retrieved record with ID: {record_id}")
                return {"id": record["id"], "fields": record["fields"]}
            else:
                logger.warning(f"Record with ID {record_id} not found")
                return None
        except Exception as e:
            logger.error(f"Error retrieving record from Airtable: {str(e)}", exc_info=True)
            return None
    
    def get_latest_record(self) -> Optional[Dict[str, Any]]:
        """
        Get the latest record based on SentTime.
        
        Returns:
            Latest record or None if no records found
        """
        if not self.airtable:
            logger.error("Airtable connection not initialized")
            return None
        
        try:
            records = self.airtable.get_all(sort=[("SentTime", "desc")])
            if records:
                latest_record = records[0]
                logger.info(f"Retrieved latest record with ID: {latest_record['id']}")
                return {"id": latest_record["id"], "fields": latest_record["fields"]}
            else:
                logger.warning("No records found")
                return None
        except Exception as e:
            logger.error(f"Error retrieving latest record from Airtable: {str(e)}", exc_info=True)
            return None

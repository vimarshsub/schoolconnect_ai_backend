"""
Announcement processor for calendar integration.

This module provides functionality to extract event details from announcements
using OpenAI's language models.
"""

import logging
import re
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List

from .config import MAX_RETRIES, OPENAI_MODEL
from .utils import calculate_reminder_date
from src.ai_analysis.agent.agent_logic import AgentManager

class AnnouncementProcessor:
    """
    Processes announcements to extract event details using OpenAI.
    """
    
    def __init__(self, agent_manager=None, logger=None):
        """
        Initialize the AnnouncementProcessor.
        
        Args:
            agent_manager: Agent manager for OpenAI API calls
            logger: Logger instance
        """
        self.agent_manager = agent_manager or AgentManager()
        self.logger = logger or logging.getLogger(__name__)
        
    def process_announcement(self, announcement: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Process an announcement to extract event details.
        
        Args:
            announcement: Dict containing announcement data
            
        Returns:
            Dict with extracted event details or None if extraction failed
        """
        try:
            self.logger.info(f"Processing announcement: {announcement.get('id')} - {announcement.get('Title', 'No title')}")
            
            # Prepare announcement text
            announcement_text = self._prepare_announcement_text(announcement)
            
            # Extract event details using OpenAI
            extraction_result = self._extract_event_details(announcement_text)
            
            if not extraction_result:
                self.logger.warning(f"No event details extracted from announcement {announcement.get('id')}")
                return None
                
            # Validate extracted data
            if not self._validate_extraction(extraction_result):
                self.logger.warning(f"Invalid event details extracted from announcement {announcement.get('id')}")
                return None
                
            # Add announcement metadata
            extraction_result['announcement_id'] = announcement.get('id')
            extraction_result['announcement_title'] = announcement.get('Title', 'No title')
            
            self.logger.info(f"Successfully extracted event details: {extraction_result['EVENT']}")
            return extraction_result
            
        except Exception as e:
            self.logger.error(f"Error processing announcement {announcement.get('id')}: {str(e)}", exc_info=True)
            return None
            
    def _prepare_announcement_text(self, announcement: Dict[str, Any]) -> str:
        """
        Prepare announcement text for extraction.
        
        Args:
            announcement: Dict containing announcement data
            
        Returns:
            Formatted announcement text
        """
        title = announcement.get('Title', '')
        description = announcement.get('Description', '')
        sent_by = announcement.get('SentByUser', '')
        
        return f"TITLE: {title}\n\nDESCRIPTION: {description}\n\nSENT BY: {sent_by}"
        
    def _extract_event_details(self, announcement_text: str) -> Optional[Dict[str, Any]]:
        """
        Extract event details using OpenAI.
        
        Args:
            announcement_text: Formatted announcement text
            
        Returns:
            Dict with extracted event details or None if extraction failed
        """
        prompt = self._build_extraction_prompt(announcement_text)
        
        for attempt in range(MAX_RETRIES):
            try:
                self.logger.debug(f"Extraction attempt {attempt+1}/{MAX_RETRIES}")
                result = self.agent_manager.agent_executor.invoke({"input": prompt})
                extraction = self._parse_extraction_result(result.get('output', ''))
                if extraction:
                    return extraction
                self.logger.warning(f"Failed to parse extraction result (attempt {attempt+1}/{MAX_RETRIES})")
            except Exception as e:
                self.logger.warning(f"Extraction attempt {attempt+1}/{MAX_RETRIES} failed: {str(e)}")
                
        return None
        
    def _build_extraction_prompt(self, announcement_text: str) -> str:
        """
        Build the prompt for OpenAI extraction.
        
        Args:
            announcement_text: Formatted announcement text
            
        Returns:
            Prompt string for OpenAI
        """
        return f"""
        You are an event extraction assistant for SchoolConnect. Analyze the following announcement and extract key event details.

        ANNOUNCEMENT:
        {announcement_text}

        Extract the following information in this exact format. DO NOT include any conversational text, explanations, or tool calls. Only provide the extracted information in the specified format:
        EVENT: [Name or title of the event]
        DATE OF EVENT: [Date when the event will occur, in YYYY-MM-DD format]
        SUPPLIES NEEDED: [List any materials, items, or forms that need to be provided by parents/students]
        SUPPLIES DUE DATE: [Date by when supplies must be submitted, in YYYY-MM-DD format]
        REMINDER DATE: [Suggested date for reminding about supplies, typically 3-5 days before the SUPPLIES DUE DATE, in YYYY-MM-DD format]

        Special instructions:
        1. If this is a field trip, identify when the permission slip is due and list "permission slip" under SUPPLIES NEEDED
        2. If no supplies are needed, write "None" for SUPPLIES NEEDED and "N/A" for SUPPLIES DUE DATE and REMINDER DATE
        3. If no due date is specified for supplies, use the event date as the SUPPLIES DUE DATE
        4. For REMINDER DATE, suggest a date 3-5 days before the SUPPLIES DUE DATE
        5. If you cannot determine any field with high confidence, write "Unknown"
        6. Only extract concrete events with specific dates, not general announcements
        """
        
    def _parse_extraction_result(self, response_text: str) -> Optional[Dict[str, Any]]:
        """
        Parse the extraction result from OpenAI response.
        
        Args:
            response_text: Response text from OpenAI
            
        Returns:
            Dict with extracted event details or None if parsing failed
        """
        try:
            # Split by '---' to handle multiple potential event extractions and take the first one
            event_blocks = response_text.strip().split('---\n')
            
            for block in event_blocks:
                extraction = {}
                lines = block.strip().split('\n')
                
                for line in lines:
                    match = re.match(r'^(EVENT|DATE OF EVENT|SUPPLIES NEEDED|SUPPLIES DUE DATE|REMINDER DATE):\s*(.*)$', line.strip())
                    if match:
                        key = match.group(1).strip()
                        value = match.group(2).strip()
                        extraction[key] = value
                
                # Check if we have the minimum required fields for this block
                if 'EVENT' in extraction and 'DATE OF EVENT' in extraction:
                    return extraction
                    
            return None
            
        except Exception as e:
            self.logger.error(f"Error parsing extraction result: {str(e)}")
            return None
            
    def _validate_extraction(self, extraction: Dict[str, Any]) -> bool:
        """
        Validate the extracted event details.
        
        Args:
            extraction: Dict with extracted event details
            
        Returns:
            True if extraction is valid, False otherwise
        """
        # Check if event has a name
        if not extraction.get('EVENT') or extraction.get('EVENT') == 'Unknown':
            return False
            
        # Check if event date is valid
        event_date = extraction.get('DATE OF EVENT')
        if not event_date or event_date == 'Unknown':
            return False
            
        try:
            datetime.strptime(event_date, '%Y-%m-%d')
        except ValueError:
            return False
            
        # If supplies are needed, check due date and reminder date
        if extraction.get('SUPPLIES NEEDED') and extraction.get('SUPPLIES NEEDED') != 'None':
            supplies_due = extraction.get('SUPPLIES DUE DATE')
            if supplies_due and supplies_due != 'N/A' and supplies_due != 'Unknown':
                try:
                    datetime.strptime(supplies_due, '%Y-%m-%d')
                except ValueError:
                    return False
                    
            reminder_date = extraction.get('REMINDER DATE')
            if reminder_date and reminder_date != 'N/A' and reminder_date != 'Unknown':
                try:
                    datetime.strptime(reminder_date, '%Y-%m-%d')
                except ValueError:
                    return False
                    
        return True

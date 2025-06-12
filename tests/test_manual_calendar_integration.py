"""
Manual test script for calendar integration.

This script allows for manual testing of the calendar integration functionality
by processing a sample announcement and creating calendar events.
"""

import os
import sys
import logging
from datetime import datetime

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.calendar_integration.announcement_processor import AnnouncementProcessor
from src.calendar_integration.calendar_sync import CalendarSync
from src.calendar_integration.utils import setup_logging

def test_with_sample_announcement():
    """
    Test the calendar integration with a sample announcement.
    """
    # Set up logging
    logger = setup_logging("manual_test")
    logger.setLevel(logging.DEBUG)
    
    logger.info("Starting manual test of calendar integration")
    
    # Sample announcement
    sample_announcement = {
        'id': 'sample_123',
        'Title': 'Field Trip to Science Museum',
        'Description': 'We will be going to the science museum on June 20, 2025. '
                      'Please bring $5 for admission and a packed lunch. '
                      'Permission slips are due by June 15, 2025.',
        'SentByUser': 'Ms. Johnson'
    }
    
    try:
        # Initialize components
        processor = AnnouncementProcessor(logger=logger)
        calendar_sync = CalendarSync(logger=logger)
        
        # Process the announcement
        logger.info("Processing sample announcement")
        event_details = processor.process_announcement(sample_announcement)
        
        if not event_details:
            logger.error("Failed to extract event details from sample announcement")
            return
            
        logger.info(f"Extracted event details: {event_details}")
        
        # Create calendar events
        logger.info("Creating calendar events")
        calendar_result = calendar_sync.create_calendar_events(event_details)
        
        if not calendar_result:
            logger.error("Failed to create calendar events")
            return
            
        logger.info(f"Calendar events created: {calendar_result}")
        logger.info("Manual test completed successfully")
        
    except Exception as e:
        logger.error(f"Error during manual test: {str(e)}", exc_info=True)

if __name__ == "__main__":
    test_with_sample_announcement()

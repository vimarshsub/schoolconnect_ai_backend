"""
Calendar sync job for SchoolConnect AI.

This module provides the main entry point for the calendar sync job,
which extracts event details from announcements and creates corresponding
events in Google Calendar.
"""

import logging
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from ..config import LOOKBACK_DAYS, BATCH_SIZE, PROCESSED_FIELD, EVENT_ID_FIELD, REMINDER_ID_FIELD
from src.calendar_integration.utils import setup_logging
from ..announcement_processor import AnnouncementProcessor
from ..calendar_sync import CalendarSync
from ...storage.airtable.client import AirtableClient

def run_sync_job() -> Dict[str, Any]:
    """
    Main entry point for the calendar sync job.
    
    Returns:
        Dict with job status and log file path
    """
    # Set up logging
    logger = setup_logging("calendar_sync")
    
    logger.info("Starting calendar sync job")
    
    try:
        # Initialize components
        airtable_client = AirtableClient()
        processor = AnnouncementProcessor(logger=logger)
        calendar_sync = CalendarSync(logger=logger)
        
        # Get unprocessed announcements from last LOOKBACK_DAYS
        cutoff_date = (datetime.now() - timedelta(days=LOOKBACK_DAYS)).strftime('%Y-%m-%d')
        
        logger.info(f"Fetching announcements since {cutoff_date}")
        announcements = airtable_client.filter_announcements_by_date(cutoff_date)
        
        # Filter to only get unprocessed announcements
        unprocessed = []
        for announcement in announcements:
            if not announcement.get('fields', {}).get(PROCESSED_FIELD, False):
                unprocessed.append(announcement)
                
        logger.info(f"Found {len(unprocessed)} unprocessed announcements")
        
        # Process announcements in batches
        processed_count = 0
        failed_count = 0
        
        for i in range(0, len(unprocessed), BATCH_SIZE):
            batch = unprocessed[i:i+BATCH_SIZE]
            logger.info(f"Processing batch {i//BATCH_SIZE + 1} ({len(batch)} announcements)")
            
            for announcement in batch:
                try:
                    event_details = processor.process_announcement(announcement.get("fields", {}))
                    if not event_details:
                        logger.info(f"No event details found in announcement {announcement.get('id')}")
                        # Mark as processed to avoid reprocessing
                        airtable_client.update_record(announcement.get("id"), {PROCESSED_FIELD: True})
                        continue

                    # Create calendar events
                    calendar_result = calendar_sync.create_calendar_events(event_details)

                    # Prepare update data for Airtable
                    update_data = {
                        PROCESSED_FIELD: True,
                        EVENT_ID_FIELD: ''
                    }

                    if calendar_result:
                        update_data[EVENT_ID_FIELD] = calendar_result.get("main_event_id", "")
                        if calendar_result.get("reminder_event_id"):
                            update_data[REMINDER_ID_FIELD] = calendar_result.get("reminder_event_id")
                        processed_count += 1
                    else:
                        logger.warning(f"Failed to create calendar events for announcement {announcement.get(\'id\')}")
                        failed_count += 1

                    # Update Airtable record with event IDs and mark as processed
                    airtable_client.update_record(announcement.get("id"), update_data)           
                except Exception as e:
                    logger.error(f"Error processing announcement {announcement.get(\'id\')}: {str(e)}", exc_info=True)                   
        logger.info(f"Calendar sync job completed. Processed: {processed_count}, Failed: {failed_count}")
        
        return {
            "status": "completed",
            "processed_count": processed_count,
            "failed_count": failed_count,
            "log_file": logger.handlers[0].baseFilename if logger.handlers else None
        }
        
    except Exception as e:
        logger.error(f"Calendar sync job failed: {str(e)}", exc_info=True)
        
        return {
            "status": "failed",
            "error": str(e),
            "log_file": logger.handlers[0].baseFilename if logger.handlers else None
        }

if __name__ == "__main__":
    # This allows the script to be run directly for testing
    result = run_sync_job()
    print(f"Job completed with status: {result['status']}")

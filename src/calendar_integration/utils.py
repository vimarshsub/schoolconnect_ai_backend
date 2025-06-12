"""
Utility functions for calendar integration.

This module provides helper functions for date handling, logging, and other
common operations used throughout the calendar integration process.
"""

import logging
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from ..utils.date_utils import DateUtils

def setup_logging(job_name: str) -> logging.Logger:
    """
    Set up logging for a calendar integration job.
    
    Args:
        job_name: Name of the job for the logger
        
    Returns:
        Logger instance configured with file and console handlers
    """
    from .config import LOG_LEVEL, LOG_FORMAT, LOG_DIR
    
    # Create logger
    logger = logging.getLogger(job_name)
    logger.setLevel(getattr(logging, LOG_LEVEL))
    
    # Remove existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Create log directory if it doesn't exist
    os.makedirs(LOG_DIR, exist_ok=True)
    
    # Add file handler
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = os.path.join(LOG_DIR, f"{job_name}_{timestamp}.log")
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(logging.Formatter(LOG_FORMAT))
    logger.addHandler(file_handler)
    
    # Add console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(LOG_FORMAT))
    logger.addHandler(console_handler)
    
    return logger

def calculate_reminder_date(due_date: str, days_before: int = 3) -> Optional[str]:
    """
    Calculate a reminder date based on a due date.
    
    Args:
        due_date: Due date in YYYY-MM-DD format
        days_before: Number of days before the due date for the reminder
        
    Returns:
        Reminder date in YYYY-MM-DD format or None if calculation failed
    """
    try:
        date_utils = DateUtils()
        due_date_obj = datetime.strptime(due_date, '%Y-%m-%d')
        reminder_date_obj = due_date_obj - timedelta(days=days_before)
        return reminder_date_obj.strftime('%Y-%m-%d')
    except Exception:
        return None

def format_event_description(event_details: Dict[str, Any]) -> str:
    """
    Format event details into a description for Google Calendar.
    
    Args:
        event_details: Dictionary containing event details
        
    Returns:
        Formatted description string
    """
    description = f"Event extracted from SchoolConnect announcement\n\n"
    
    # Add announcement title and ID if available
    if event_details.get('announcement_title'):
        description += f"Announcement: {event_details.get('announcement_title')}\n\n"
    
    # Add supplies information if available
    if event_details.get('SUPPLIES NEEDED') and event_details.get('SUPPLIES NEEDED') != 'None':
        description += f"Supplies needed: {event_details.get('SUPPLIES NEEDED')}\n"
        
        if event_details.get('SUPPLIES DUE DATE') and event_details.get('SUPPLIES DUE DATE') not in ['N/A', 'Unknown']:
            description += f"Supplies due date: {event_details.get('SUPPLIES DUE DATE')}\n"
    
    # Add extraction timestamp
    description += f"\nExtracted on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    
    return description

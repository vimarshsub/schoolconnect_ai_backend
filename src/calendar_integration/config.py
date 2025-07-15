"""
Configuration settings for calendar integration.

This module contains all configurable parameters for the calendar integration process,
including lookback days, reminder settings, and other options.
"""

# How many days back to look for unprocessed announcements
LOOKBACK_DAYS = 100

# Days before supplies due date to set reminder
REMINDER_DAYS_BEFORE = 3

# Maximum retries for API calls
MAX_RETRIES = 3

# Number of announcements to process in one batch
BATCH_SIZE = 20

# OpenAI model to use for extraction
OPENAI_MODEL = "gpt-4"

# Field name in Airtable to track processed status
PROCESSED_FIELD = "CalendarProcessed"

# Field name in Airtable to store calendar event IDs
EVENT_ID_FIELD = "CalendarEventId"
REMINDER_ID_FIELD = "CalendarReminderEventId"

# Event creation preferences
DEFAULT_EVENT_TYPE = "all_day"  # Options: "all_day", "timed"
DEFAULT_EVENT_START_TIME = "09:00"  # Default start time for timed events (HH:MM)
DEFAULT_EVENT_DURATION_HOURS = 1  # Default duration for timed events

# Log settings
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_DIR = "/tmp"

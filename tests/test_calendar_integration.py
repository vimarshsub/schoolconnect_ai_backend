"""
Tests for calendar integration functionality.

This module contains tests for the calendar integration components,
including announcement processing and calendar event creation.
"""

import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime

from src.calendar_integration.announcement_processor import AnnouncementProcessor
from src.calendar_integration.calendar_sync import CalendarSync
from src.calendar_integration.tasks.sync_calendar import run_sync_job

class TestAnnouncementProcessor(unittest.TestCase):
    """Test the AnnouncementProcessor class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_agent_manager = MagicMock()
        self.mock_logger = MagicMock()
        self.processor = AnnouncementProcessor(
            agent_manager=self.mock_agent_manager,
            logger=self.mock_logger
        )
        
    def test_prepare_announcement_text(self):
        """Test preparing announcement text for extraction."""
        announcement = {
            'Title': 'Field Trip to Museum',
            'Description': 'We will be going to the science museum on June 20, 2025. Please bring $5 for admission.',
            'SentByUser': 'Ms. Johnson'
        }
        
        expected_text = "TITLE: Field Trip to Museum\n\nDESCRIPTION: We will be going to the science museum on June 20, 2025. Please bring $5 for admission.\n\nSENT BY: Ms. Johnson"
        result = self.processor._prepare_announcement_text(announcement)
        
        self.assertEqual(result, expected_text)
        
    def test_parse_extraction_result_valid(self):
        """Test parsing a valid extraction result."""
        response_text = """
        EVENT: Field Trip to Science Museum
        DATE OF EVENT: 2025-06-20
        SUPPLIES NEEDED: $5 for admission, lunch, water bottle
        SUPPLIES DUE DATE: 2025-06-20
        REMINDER DATE: 2025-06-17
        """
        
        expected_result = {
            'EVENT': 'Field Trip to Science Museum',
            'DATE OF EVENT': '2025-06-20',
            'SUPPLIES NEEDED': '$5 for admission, lunch, water bottle',
            'SUPPLIES DUE DATE': '2025-06-20',
            'REMINDER DATE': '2025-06-17'
        }
        
        result = self.processor._parse_extraction_result(response_text)
        self.assertEqual(result, expected_result)
        
    def test_parse_extraction_result_invalid(self):
        """Test parsing an invalid extraction result."""
        response_text = """
        Sorry, I couldn't find any event details in this announcement.
        """
        
        result = self.processor._parse_extraction_result(response_text)
        self.assertIsNone(result)
        
    def test_validate_extraction_valid(self):
        """Test validating a valid extraction."""
        extraction = {
            'EVENT': 'Field Trip to Science Museum',
            'DATE OF EVENT': '2025-06-20',
            'SUPPLIES NEEDED': '$5 for admission, lunch, water bottle',
            'SUPPLIES DUE DATE': '2025-06-20',
            'REMINDER DATE': '2025-06-17'
        }
        
        result = self.processor._validate_extraction(extraction)
        self.assertTrue(result)
        
    def test_validate_extraction_invalid_date(self):
        """Test validating an extraction with invalid date."""
        extraction = {
            'EVENT': 'Field Trip to Science Museum',
            'DATE OF EVENT': 'next Friday',  # Invalid format
            'SUPPLIES NEEDED': '$5 for admission, lunch, water bottle',
            'SUPPLIES DUE DATE': '2025-06-20',
            'REMINDER DATE': '2025-06-17'
        }
        
        result = self.processor._validate_extraction(extraction)
        self.assertFalse(result)
        
    def test_validate_extraction_missing_event(self):
        """Test validating an extraction with missing event."""
        extraction = {
            'DATE OF EVENT': '2025-06-20',
            'SUPPLIES NEEDED': '$5 for admission, lunch, water bottle',
            'SUPPLIES DUE DATE': '2025-06-20',
            'REMINDER DATE': '2025-06-17'
        }
        
        result = self.processor._validate_extraction(extraction)
        self.assertFalse(result)
        
    @patch('src.calendar_integration.announcement_processor.AnnouncementProcessor._extract_event_details')
    def test_process_announcement_success(self, mock_extract):
        """Test successful announcement processing."""
        announcement = {
            'id': '123',
            'Title': 'Field Trip to Museum',
            'Description': 'We will be going to the science museum on June 20, 2025.',
            'SentByUser': 'Ms. Johnson'
        }
        
        extraction = {
            'EVENT': 'Field Trip to Science Museum',
            'DATE OF EVENT': '2025-06-20',
            'SUPPLIES NEEDED': '$5 for admission, lunch, water bottle',
            'SUPPLIES DUE DATE': '2025-06-20',
            'REMINDER DATE': '2025-06-17'
        }
        
        mock_extract.return_value = extraction
        
        result = self.processor.process_announcement(announcement)
        
        self.assertEqual(result['EVENT'], 'Field Trip to Science Museum')
        self.assertEqual(result['announcement_id'], '123')
        self.assertEqual(result['announcement_title'], 'Field Trip to Museum')
        
    @patch('src.calendar_integration.announcement_processor.AnnouncementProcessor._extract_event_details')
    def test_process_announcement_no_event(self, mock_extract):
        """Test announcement processing with no event found."""
        announcement = {
            'id': '123',
            'Title': 'Weekly Newsletter',
            'Description': 'Here is this week\'s newsletter with updates.',
            'SentByUser': 'Principal Smith'
        }
        
        mock_extract.return_value = None
        
        result = self.processor.process_announcement(announcement)
        
        self.assertIsNone(result)
        self.mock_logger.warning.assert_called_once()

class TestCalendarSync(unittest.TestCase):
    """Test the CalendarSync class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_calendar_tool = MagicMock()
        self.mock_logger = MagicMock()
        self.calendar_sync = CalendarSync(
            calendar_tool=self.mock_calendar_tool,
            logger=self.mock_logger
        )
        
    def test_create_main_event_success(self):
        """Test successful creation of main event."""
        event_details = {
            'EVENT': 'Field Trip to Science Museum',
            'DATE OF EVENT': '2025-06-20',
            'SUPPLIES NEEDED': '$5 for admission, lunch, water bottle',
            'SUPPLIES DUE DATE': '2025-06-20',
            'REMINDER DATE': '2025-06-17'
        }
        
        self.mock_calendar_tool.create_event.return_value = "Successfully created calendar event: Field Trip to Science Museum with ID: event123"
        
        result = self.calendar_sync._create_main_event(event_details)
        
        self.assertEqual(result, "event123")
        self.mock_calendar_tool.create_event.assert_called_once()
        
    def test_create_main_event_invalid_date(self):
        """Test main event creation with invalid date."""
        event_details = {
            'EVENT': 'Field Trip to Science Museum',
            'DATE OF EVENT': 'Unknown',
            'SUPPLIES NEEDED': '$5 for admission, lunch, water bottle',
            'SUPPLIES DUE DATE': '2025-06-20',
            'REMINDER DATE': '2025-06-17'
        }
        
        result = self.calendar_sync._create_main_event(event_details)
        
        self.assertIsNone(result)
        self.mock_calendar_tool.create_event.assert_not_called()
        
    def test_create_reminder_event_success(self):
        """Test successful creation of reminder event."""
        event_details = {
            'EVENT': 'Field Trip to Science Museum',
            'DATE OF EVENT': '2025-06-20',
            'SUPPLIES NEEDED': '$5 for admission, lunch, water bottle',
            'SUPPLIES DUE DATE': '2025-06-20',
            'REMINDER DATE': '2025-06-17'
        }
        
        self.mock_calendar_tool.create_reminder.return_value = "Successfully created reminder: REMINDER: Field Trip to Science Museum - Supplies Due Soon with ID: reminder456"
        
        result = self.calendar_sync._create_reminder_event(event_details)
        
        self.assertEqual(result, "reminder456")
        self.mock_calendar_tool.create_reminder.assert_called_once()
        
    def test_create_reminder_event_no_reminder_date(self):
        """Test reminder event creation with no reminder date."""
        event_details = {
            'EVENT': 'Field Trip to Science Museum',
            'DATE OF EVENT': '2025-06-20',
            'SUPPLIES NEEDED': '$5 for admission, lunch, water bottle',
            'SUPPLIES DUE DATE': '2025-06-20',
            'REMINDER DATE': 'N/A'
        }
        
        result = self.calendar_sync._create_reminder_event(event_details)
        
        self.assertIsNone(result)
        self.mock_calendar_tool.create_reminder.assert_not_called()
        
    def test_create_calendar_events_success(self):
        """Test successful creation of all calendar events."""
        event_details = {
            'EVENT': 'Field Trip to Science Museum',
            'DATE OF EVENT': '2025-06-20',
            'SUPPLIES NEEDED': '$5 for admission, lunch, water bottle',
            'SUPPLIES DUE DATE': '2025-06-20',
            'REMINDER DATE': '2025-06-17'
        }
        
        self.mock_calendar_tool.create_event.return_value = "Successfully created calendar event: Field Trip to Science Museum with ID: event123"
        self.mock_calendar_tool.create_reminder.return_value = "Successfully created reminder: REMINDER: Field Trip to Science Museum - Supplies Due Soon with ID: reminder456"
        
        result = self.calendar_sync.create_calendar_events(event_details)
        
        self.assertEqual(result['main_event_id'], "event123")
        self.assertEqual(result['reminder_event_id'], "reminder456")
        
    def test_create_calendar_events_no_supplies(self):
        """Test calendar events creation with no supplies needed."""
        event_details = {
            'EVENT': 'School Assembly',
            'DATE OF EVENT': '2025-06-20',
            'SUPPLIES NEEDED': 'None',
            'SUPPLIES DUE DATE': 'N/A',
            'REMINDER DATE': 'N/A'
        }
        
        self.mock_calendar_tool.create_event.return_value = "Successfully created calendar event: School Assembly with ID: event123"
        
        result = self.calendar_sync.create_calendar_events(event_details)
        
        self.assertEqual(result['main_event_id'], "event123")
        self.assertIsNone(result['reminder_event_id'])
        self.mock_calendar_tool.create_reminder.assert_not_called()

@patch('src.calendar_integration.tasks.sync_calendar.AirtableClient')
@patch('src.calendar_integration.tasks.sync_calendar.AnnouncementProcessor')
@patch('src.calendar_integration.tasks.sync_calendar.CalendarSync')
def test_run_sync_job(mock_calendar_sync_class, mock_processor_class, mock_airtable_class):
    """Test the main sync job function."""
    # Set up mocks
    mock_airtable = MagicMock()
    mock_processor = MagicMock()
    mock_calendar_sync = MagicMock()
    
    mock_airtable_class.return_value = mock_airtable
    mock_processor_class.return_value = mock_processor
    mock_calendar_sync_class.return_value = mock_calendar_sync
    
    # Mock announcements
    mock_airtable.filter_announcements_by_date.return_value = [
        {
            'id': '123',
            'fields': {
                'Title': 'Field Trip to Museum',
                'Description': 'We will be going to the science museum on June 20, 2025.',
                'SentByUser': 'Ms. Johnson',
                'CalendarProcessed': False
            }
        },
        {
            'id': '456',
            'fields': {
                'Title': 'School Assembly',
                'Description': 'School assembly on June 25, 2025.',
                'SentByUser': 'Principal Smith',
                'CalendarProcessed': False
            }
        }
    ]
    
    # Mock event extraction
    mock_processor.process_announcement.side_effect = [
        {
            'EVENT': 'Field Trip to Science Museum',
            'DATE OF EVENT': '2025-06-20',
            'SUPPLIES NEEDED': '$5 for admission, lunch, water bottle',
            'SUPPLIES DUE DATE': '2025-06-20',
            'REMINDER DATE': '2025-06-17'
        },
        None  # No event found for second announcement
    ]
    
    # Mock calendar event creation
    mock_calendar_sync.create_calendar_events.return_value = {
        'main_event_id': 'event123',
        'reminder_event_id': 'reminder456'
    }
    
    # Run the job
    result = run_sync_job()
    
    # Verify results
    assert result['status'] == 'completed'
    assert result['processed_count'] == 1
    
    # Verify Airtable updates
    mock_airtable.update_record.assert_any_call('123', {
        'CalendarProcessed': True,
        'CalendarEventId': 'event123',
        'CalendarReminderEventId': 'reminder456'
    })
    mock_airtable.update_record.assert_any_call('456', {
        'CalendarProcessed': True
    })

if __name__ == '__main__':
    unittest.main()

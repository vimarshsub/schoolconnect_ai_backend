"""
Test for Airtable storage functionality.
"""

import pytest
from unittest.mock import patch

from src.storage.airtable.client import AirtableClient

def test_airtable_client_get_all_records(mock_airtable_client):
    """Test getting all records from Airtable."""
    client = AirtableClient()
    records = client.get_all_records()
    
    assert len(records) > 0
    assert "id" in records[0]
    assert "fields" in records[0]
    assert "Title" in records[0]["fields"]

def test_airtable_client_search_records(mock_airtable_client):
    """Test searching records in Airtable."""
    client = AirtableClient()
    records = client.search_records("test")
    
    assert len(records) > 0
    assert "Title" in records[0]["fields"]
    assert "test" in records[0]["fields"]["Title"].lower()
    
    # Test with no results
    empty_records = client.search_records("nonexistent")
    assert len(empty_records) == 0

def test_airtable_client_get_record_by_id(mock_airtable_client):
    """Test getting a record by ID from Airtable."""
    client = AirtableClient()
    record = client.get_record_by_id("rec123")
    
    assert record is not None
    assert record["id"] == "rec123"
    assert "Title" in record["fields"]
    
    # Test with nonexistent ID
    nonexistent_record = client.get_record_by_id("nonexistent")
    assert nonexistent_record is None

def test_airtable_client_create_record(mock_airtable_client):
    """Test creating a record in Airtable."""
    client = AirtableClient()
    record_data = {
        "AnnouncementId": "456",
        "Title": "New Test Announcement",
        "Description": "This is a new test announcement",
        "SentByUser": "Test User",
        "DocumentsCount": 0,
        "SentTime": "2025-05-26T14:00:00Z"
    }
    
    result = client.create_record(record_data)
    
    assert result is not None
    assert "id" in result
    assert "fields" in result
    assert result["fields"]["Title"] == "New Test Announcement"

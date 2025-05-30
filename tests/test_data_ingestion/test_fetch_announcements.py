"""
Test for data ingestion functionality.
"""

import pytest
from unittest.mock import patch

from src.data_ingestion.tasks.fetch_announcements import FetchAnnouncementsTask

def test_fetch_announcements_task(mock_schoolconnect_client, mock_airtable_client):
    """Test the FetchAnnouncementsTask."""
    task = FetchAnnouncementsTask()
    result = task.execute("testuser", "testpass", max_pages=1)
    
    assert result["success"] is True
    assert result["announcements_processed"] > 0
    assert result["announcements_saved"] > 0

def test_fetch_announcements_auth_failure(mock_schoolconnect_client, mock_airtable_client):
    """Test FetchAnnouncementsTask with authentication failure."""
    with patch("src.data_ingestion.schoolconnect.client.SchoolConnectClient.login", return_value=False):
        task = FetchAnnouncementsTask()
        result = task.execute("wronguser", "wrongpass", max_pages=1)
        
        assert result["success"] is False
        assert "error" in result

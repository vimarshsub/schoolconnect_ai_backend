"""
Test configuration for SchoolConnect-AI Backend.
"""

import os
import pytest
from fastapi.testclient import TestClient

from src.core.config import get_settings
from main import app

@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)

@pytest.fixture
def mock_airtable_client(monkeypatch):
    """Mock the AirtableClient for testing."""
    class MockAirtableClient:
        def __init__(self):
            self.airtable = True
        
        def get_all_records(self):
            return [
                {
                    "id": "rec123",
                    "fields": {
                        "AnnouncementId": "123",
                        "Title": "Test Announcement",
                        "Description": "This is a test announcement",
                        "SentByUser": "Test User",
                        "DocumentsCount": 1,
                        "SentTime": "2025-05-26T12:00:00Z",
                        "Attachments": [
                            {
                                "url": "https://example.com/test.pdf",
                                "filename": "test.pdf"
                            }
                        ]
                    }
                }
            ]
        
        def search_records(self, search_text):
            if "test" in search_text.lower():
                return self.get_all_records()
            return []
        
        def get_record_by_id(self, record_id):
            if record_id == "rec123":
                return self.get_all_records()[0]
            return None
        
        def get_latest_record(self):
            return self.get_all_records()[0]
        
        def create_record(self, record_data):
            return {
                "id": "rec456",
                "fields": record_data
            }
    
    from src.storage.airtable import client
    monkeypatch.setattr(client, "AirtableClient", MockAirtableClient)

@pytest.fixture
def mock_schoolconnect_client(monkeypatch):
    """Mock the SchoolConnectClient for testing."""
    class MockSchoolConnectClient:
        def __init__(self):
            self.session = None
            self.headers = {}
            self.graphql_url = "https://connect.schoolstatus.com/graphql"
        
        def login(self, username, password):
            return username == "testuser" and password == "testpass"
        
        def fetch_paginated_announcements(self, after_cursor=None, items_per_page=20):
            return {
                "announcements": [
                    {
                        "id": "123",
                        "dbId": "123",
                        "title": "Test Announcement",
                        "message": "This is a test announcement",
                        "createdAt": "2025-05-26T12:00:00Z",
                        "user": {
                            "permittedName": "Test User"
                        },
                        "documentsCount": 1
                    }
                ],
                "hasNextPage": False,
                "endCursor": None,
                "error": None
            }
        
        def fetch_announcement_documents(self, announcement_id):
            return [
                {
                    "id": "doc123",
                    "fileFilename": "test.pdf",
                    "fileUrl": "https://example.com/test.pdf",
                    "contentType": "application/pdf"
                }
            ]
    
    from src.data_ingestion.schoolconnect import client
    monkeypatch.setattr(client, "SchoolConnectClient", MockSchoolConnectClient)

@pytest.fixture
def mock_openai_tool(monkeypatch):
    """Mock the OpenAIDocumentAnalysisTool for testing."""
    class MockOpenAIDocumentAnalysisTool:
        def analyze_document(self, pdf_path, analysis_type="summarize", custom_prompt=None):
            return "This is a mock analysis of the document."
    
    from src.ai_analysis.tools import openai_tool
    monkeypatch.setattr(openai_tool, "OpenAIDocumentAnalysisTool", MockOpenAIDocumentAnalysisTool)

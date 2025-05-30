"""
Test for API endpoints.
"""

import pytest
from fastapi.testclient import TestClient

def test_health_endpoint(client):
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert "status" in response.json()
    assert "metrics" in response.json()

def test_auth_endpoints(client):
    """Test the authentication endpoints."""
    # Test login
    login_data = {
        "username": "testuser",
        "password": "testpass"
    }
    response = client.post("/api/auth/login", data=login_data)
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert "token_type" in response.json()
    
    # Get the token for subsequent requests
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test token refresh
    response = client.post("/api/auth/refresh", headers=headers)
    assert response.status_code == 200
    assert "access_token" in response.json()

def test_ingestion_endpoints(client, mock_schoolconnect_client, mock_airtable_client):
    """Test the data ingestion endpoints."""
    # First login to get token
    login_data = {
        "username": "testuser",
        "password": "testpass"
    }
    response = client.post("/api/auth/login", data=login_data)
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test sync endpoint
    sync_data = {
        "username": "testuser",
        "password": "testpass",
        "max_pages": 1
    }
    response = client.post("/api/ingestion/sync", json=sync_data, headers=headers)
    assert response.status_code == 200
    assert response.json()["success"] is True
    
    # Test status endpoint
    response = client.get("/api/ingestion/status", headers=headers)
    assert response.status_code == 200
    
    # Test config endpoints
    response = client.get("/api/ingestion/config", headers=headers)
    assert response.status_code == 200
    assert "max_pages" in response.json()
    
    config_data = {
        "max_pages": 10,
        "schedule_enabled": True
    }
    response = client.put("/api/ingestion/config", json=config_data, headers=headers)
    assert response.status_code == 200
    assert response.json()["max_pages"] == 10

def test_analysis_endpoints(client, mock_airtable_client, mock_openai_tool):
    """Test the AI analysis endpoints."""
    # First login to get token
    login_data = {
        "username": "testuser",
        "password": "testpass"
    }
    response = client.post("/api/auth/login", data=login_data)
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test chat endpoint
    chat_data = {
        "message": "Show me all announcements"
    }
    response = client.post("/api/chat", json=chat_data, headers=headers)
    assert response.status_code == 200
    assert "session_id" in response.json()
    assert "response" in response.json()
    
    # Get the session ID
    session_id = response.json()["session_id"]
    
    # Test get chat history endpoint
    response = client.get(f"/api/chat/{session_id}", headers=headers)
    assert response.status_code == 200
    assert len(response.json()) > 0
    
    # Test clear chat history endpoint
    response = client.delete(f"/api/chat/{session_id}", headers=headers)
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    
    # Test announcements endpoint
    response = client.get("/api/announcements", headers=headers)
    assert response.status_code == 200
    assert "announcements" in response.json()
    assert len(response.json()["announcements"]) > 0
    
    # Test search announcements endpoint
    response = client.get("/api/announcements/search?search_text=test", headers=headers)
    assert response.status_code == 200
    assert "announcements" in response.json()
    
    # Test get announcement attachments endpoint
    response = client.get("/api/announcements/rec123/attachments", headers=headers)
    assert response.status_code == 200
    assert "attachments" in response.json()

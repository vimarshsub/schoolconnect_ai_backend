#!/usr/bin/env python
"""
Test script for cron job API key authentication.
This demonstrates how to use the CRON_API_KEY to authenticate with your backend API,
which then uses the SchoolConnect client to fetch data.
"""

import os
import json
import requests
from dotenv import load_dotenv
from src.core.config import get_settings

# Load environment variables
load_dotenv()

# Get the settings with API key
settings = get_settings()
CRON_API_KEY = settings.CRON_API_KEY
BASE_URL = "http://localhost:8000"  # Adjust if your server is running on a different port

def test_cron_api_key_auth():
    """Test the cron job API key authentication."""
    
    if not CRON_API_KEY:
        print("❌ CRON_API_KEY not set in environment variables!")
        print("Please set CRON_API_KEY in .env file")
        return
    
    print(f"Using CRON_API_KEY: {CRON_API_KEY}")
    
    # Test each endpoint with API key
    test_sync_endpoint()
    test_cron_endpoint()

def test_sync_endpoint():
    """Test the sync endpoint with API key."""
    url = f"{BASE_URL}/api/ingestion/sync?api_key={CRON_API_KEY}"
    
    print(f"\nTesting sync endpoint: {url}")
    
    # Define request body for sync endpoint
    request_body = {
        "username": "",  # Leave empty to use environment variables
        "password": "",  # Leave empty to use environment variables
        "max_pages": 5
    }
    
    try:
        response = requests.post(
            url,
            json=request_body,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ API key authentication successful!")
            print(json.dumps(response.json(), indent=2))
        elif response.status_code == 401:
            print("❌ API key authentication failed - 401 Unauthorized")
            print("This suggests the API key is not valid or not properly configured on the server.")
        else:
            print(f"ℹ️ Received status code: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")

def test_cron_endpoint():
    """Test the cron endpoint with API key."""
    url = f"{BASE_URL}/api/ingestion/cron?api_key={CRON_API_KEY}"
    
    print(f"\nTesting cron endpoint: {url}")
    
    try:
        response = requests.post(
            url,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ API key authentication successful!")
            print(json.dumps(response.json(), indent=2))
        elif response.status_code == 401:
            print("❌ API key authentication failed - 401 Unauthorized")
            print("This suggests the API key is not valid or not properly configured on the server.")
        else:
            print(f"ℹ️ Received status code: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")

def test_without_api_key():
    """Test the endpoints without API key to confirm it's required."""
    
    print("\n" + "=" * 50)
    print("TESTING WITHOUT API KEY")
    print("=" * 50)
    
    # Test sync endpoint without API key
    url = f"{BASE_URL}/api/ingestion/sync"
    
    print(f"Testing sync endpoint without API key: {url}")
    
    request_body = {
        "username": "",
        "password": "",
        "max_pages": 5
    }
    
    try:
        response = requests.post(
            url,
            json=request_body,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 401:
            print("✅ Expected result: 401 Unauthorized (API key authentication is working)")
        else:
            print(f"❌ Unexpected status code: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    
    # Test cron endpoint without API key
    url = f"{BASE_URL}/api/ingestion/cron"
    
    print(f"\nTesting cron endpoint without API key: {url}")
    
    try:
        response = requests.post(
            url,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 401:
            print("✅ Expected result: 401 Unauthorized (API key authentication is working)")
        else:
            print(f"❌ Unexpected status code: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    print("=" * 50)
    print("TESTING CRON API KEY AUTHENTICATION")
    print("=" * 50)
    test_cron_api_key_auth()
    test_without_api_key()
    print("=" * 50) 
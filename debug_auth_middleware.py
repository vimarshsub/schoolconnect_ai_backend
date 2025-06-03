#!/usr/bin/env python
"""
Debug script for auth middleware and API key handling.
This script helps identify issues with the API key authentication in the middleware.
"""

import os
import json
from dotenv import load_dotenv
from src.core.config import get_settings
from src.api.middleware.auth import AuthMiddleware
import requests

# Load environment variables
load_dotenv()

# Get the settings with API key
settings = get_settings()
CRON_API_KEY = settings.CRON_API_KEY

def inspect_api_key_settings():
    """Inspect the API key settings and configuration."""
    print("=" * 50)
    print("API KEY CONFIGURATION INSPECTION")
    print("=" * 50)
    
    # Check if CRON_API_KEY is set
    if not CRON_API_KEY:
        print("❌ CRON_API_KEY is not set in settings!")
        print("   Please check your .env file and ensure CRON_API_KEY is set.")
    else:
        print(f"✅ CRON_API_KEY is set: {CRON_API_KEY}")
    
    # Check environment variable directly
    env_api_key = os.getenv("CRON_API_KEY")
    if not env_api_key:
        print("❌ CRON_API_KEY environment variable is not set!")
    else:
        print(f"✅ CRON_API_KEY environment variable is set: {env_api_key}")
    
    # Check if they match
    if env_api_key and CRON_API_KEY and env_api_key == CRON_API_KEY:
        print("✅ Environment variable and settings API key match!")
    elif env_api_key and CRON_API_KEY:
        print("❌ Environment variable and settings API key DO NOT match!")
        print(f"   Env: {env_api_key}")
        print(f"   Settings: {CRON_API_KEY}")

def test_server_api_key_handling():
    """Test how the server is handling API key authentication."""
    print("\n" + "=" * 50)
    print("SERVER API KEY HANDLING TEST")
    print("=" * 50)
    
    BASE_URL = "http://localhost:8000"
    
    # Test endpoints with API key
    endpoints = [
        "/api/ingestion/sync",
        "/api/ingestion/cron"
    ]
    
    for endpoint in endpoints:
        url = f"{BASE_URL}{endpoint}?api_key={CRON_API_KEY}"
        print(f"Testing endpoint: {url}")
        
        try:
            response = requests.post(
                url,
                headers={"Content-Type": "application/json"},
                timeout=5
            )
            
            print(f"  Status: {response.status_code}")
            if response.status_code == 401:
                print("  ❌ Authentication failed (401 Unauthorized)")
                print("     This suggests the API key is not being properly recognized.")
            elif response.status_code == 200:
                print("  ✅ Authentication successful!")
            else:
                print(f"  ℹ️ Received status code: {response.status_code}")
                
            # Print short response
            if len(response.text) > 100:
                print(f"  Response: {response.text[:100]}...")
            else:
                print(f"  Response: {response.text}")
                
        except Exception as e:
            print(f"  ❌ Error: {str(e)}")
        
        print("-" * 40)

def suggest_fixes():
    """Suggest potential fixes for API key authentication issues."""
    print("\n" + "=" * 50)
    print("SUGGESTED FIXES")
    print("=" * 50)
    
    print("1. Check the .env file contains the correct CRON_API_KEY")
    print("   - The value should match what's expected by the server")
    
    print("\n2. Verify the middleware is correctly registered in your application")
    print("   - In main.py, ensure setup_middleware(app) is called after CORS middleware")
    
    print("\n3. Make sure the API key is being properly passed in the query parameters")
    print("   - The URL should include ?api_key=YOUR_API_KEY")
    
    print("\n4. Look for any errors in the server logs related to authentication")
    print("   - Enable debug logging in your application")
    
    print("\n5. Ensure the server has been restarted after any middleware changes")
    print("   - Kill any existing processes and start fresh")
    
    print("\n6. Check if there are conflicting middleware components")
    print("   - FastAPI's order of middleware registration matters")

if __name__ == "__main__":
    inspect_api_key_settings()
    try:
        test_server_api_key_handling()
    except Exception as e:
        print(f"Error testing server: {str(e)}")
    suggest_fixes() 
#!/usr/bin/env python
import requests
import os
import time
import sys

def test_cron_job(api_key=None, port=None):
    """
    Test the cron job by making a request to the ingestion/sync endpoint
    with the API key authentication
    """
    if not api_key:
        api_key = "test_cron_key_change_this_in_production"
    
    if not port:
        # Try different ports since we're not sure which one the app is running on
        ports = [8000, 8080, 5000, 3000]
    else:
        ports = [port]
    
    for port in ports:
        url = f"http://localhost:{port}/api/ingestion/sync"
        print(f"\nTesting API endpoint: {url} with API key: {api_key}")
        
        try:
            response = requests.post(f"{url}?api_key={api_key}", timeout=3)
            print(f"Status code: {response.status_code}")
            print(f"Response body: {response.text}")
            return port, response.status_code, response.text
        except requests.RequestException as e:
            print(f"Error making request to port {port}: {e}")
    
    return None, None, "Could not connect to any port"

if __name__ == "__main__":
    if len(sys.argv) > 1:
        api_key = sys.argv[1]
    else:
        api_key = "test_cron_key_change_this_in_production"
    
    port, status, response = test_cron_job(api_key=api_key)
    
    if port:
        print(f"\nSuccessfully connected to port {port}")
        print(f"For Koyeb deployment, use: https://your-app-name.koyeb.app/api/ingestion/sync?api_key={api_key}")
        print(f"GitHub Actions workflow is configured to call this endpoint with your API key") 
#!/bin/bash
#
# Simple test script for the worker service command
#

# Hardcoded API key for testing
API_KEY="test_cron_key_change_this_in_production"

# Define the URL (use localhost for testing)
API_URL="http://localhost:8000/api/ingestion/sync"

echo "Testing API endpoint with API key..."
curl -X POST "$API_URL?api_key=$API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"max_pages": 10}'

echo
echo
echo "Command for Koyeb Worker service:"
echo 'curl -X POST "https://your-app-name.koyeb.app/api/ingestion/sync?api_key=$CRON_API_KEY" -H "Content-Type: application/json" -d '"'"'{"max_pages": 10}'"'" 
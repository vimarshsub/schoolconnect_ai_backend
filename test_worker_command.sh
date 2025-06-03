#!/bin/bash
#
# Test script for the worker service command that will be used in Koyeb
# This simulates the curl command that the Worker will run
#

# Get API key from .env file or use default
if [ -f .env ]; then
  CRON_API_KEY=$(grep CRON_API_KEY .env | cut -d '=' -f2)
else
  CRON_API_KEY="test_cron_key_change_this_in_production"
fi

# URL-encode the API key
# This simple replacement handles basic cases
ENCODED_API_KEY=$(echo "$CRON_API_KEY" | sed 's/\//%2F/g' | sed 's/+/%2B/g' | sed 's/=/%3D/g' | sed 's/ /%20/g')

# Define the URL (use localhost for testing)
API_URL="http://localhost:8000/api/ingestion/sync"

# Display test information
echo "===================================================="
echo "TESTING WORKER SERVICE COMMAND"
echo "===================================================="
echo "API URL: $API_URL"
echo "CRON_API_KEY: ${CRON_API_KEY:0:8}..."
echo "===================================================="

# Perform the curl command that will be used in the Worker service
echo "Running curl command..."
curl -X POST "$API_URL?api_key=$ENCODED_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"max_pages": 10}'

echo
echo "===================================================="
echo "COMMAND FOR KOYEB WORKER:"
echo "curl -X POST \"https://your-app-name.koyeb.app/api/ingestion/sync?api_key=\$CRON_API_KEY\" -H \"Content-Type: application/json\" -d '{\"max_pages\": 10}'"
echo "===================================================="

# Alternative command using an environment variable directly
echo
echo "ALTERNATIVE COMMAND FOR KOYEB WORKER (recommended):"
echo 'curl -X POST "https://your-app-name.koyeb.app/api/ingestion/sync?api_key=$CRON_API_KEY" -H "Content-Type: application/json" -d '"'"'{"max_pages": 10}'"'"
echo "====================================================" 
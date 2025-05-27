#!/bin/bash

# Setup script for SchoolConnect-AI Backend

# Create virtual environment
echo "Creating virtual environment..."
python -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Install system dependencies
echo "Installing system dependencies..."
if command -v apt-get &> /dev/null; then
    sudo apt-get update
    sudo apt-get install -y poppler-utils
elif command -v yum &> /dev/null; then
    sudo yum install -y poppler-utils
elif command -v brew &> /dev/null; then
    brew install poppler
else
    echo "WARNING: Could not install poppler-utils automatically."
    echo "Please install poppler-utils manually for PDF processing."
fi

# Create directories
echo "Creating directories..."
mkdir -p /tmp/schoolconnect_ai/agent_downloads

# Create example .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating example .env file..."
    cat > .env << EOL
DEBUG=False
LOG_LEVEL=INFO
CORS_ORIGINS=["http://localhost:3000"]
AIRTABLE_API_KEY=your_airtable_api_key
AIRTABLE_BASE_ID=your_airtable_base_id
AIRTABLE_TABLE_NAME=Announcements
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4o
EOL
    echo "Please update the .env file with your API keys and configuration."
fi

echo "Setup complete!"
echo "To start the server, run: python main.py"

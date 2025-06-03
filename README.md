# SchoolConnect-AI Backend

This repository contains the unified backend for SchoolConnect data ingestion and AI analysis, combining functionality from the ClassTagWorkflowApp and ai_agent_project_new repositories.

## Overview

The SchoolConnect-AI Backend provides a comprehensive solution for:

1. **Data Ingestion**: Automatically fetching announcements and documents from SchoolConnect and storing them in Airtable
2. **AI Analysis**: Analyzing documents using OpenAI's GPT-4o vision capabilities and providing a conversational interface
3. **Unified API**: A single API that handles both data ingestion and AI analysis operations

## Critical Components

### Document Fetching

The document fetching functionality is sensitive to specific implementation details:

- **ID Formatting**: Documents must be fetched using the format `Announcement:{dbId}` where dbId is the numeric database ID
- **Session Handling**: Session cookies must be preserved between requests
- **Authentication Flow**: The authentication state must be maintained throughout the process

For detailed information, see [SchoolConnect API Integration Guide](docs/SchoolConnect_API_Integration.md).

## Troubleshooting

Common issues and their solutions:

1. **404 Errors When Fetching Documents**:
   - Verify the announcement ID is formatted correctly as `Announcement:{dbId}`
   - Ensure session cookies are preserved between requests
   - Check that authentication is successful and session is maintained

2. **Missing PDF Attachments**:
   - Verify document content type filtering is working correctly
   - Check Airtable API integration for attachment creation
   - Confirm document URLs are accessible

3. **Duplicate Announcements**:
   - The system checks for existing records before creation
   - Verify the duplicate detection logic is working correctly

## Architecture

The backend follows a modular architecture with clear separation of concerns:

```
┌─────────────────────────────────────────────────────────────────┐
│                      Unified Backend                            │
│                                                                 │
│  ┌───────────────────────┐           ┌─────────────────────┐    │
│  │                       │           │                     │    │
│  │  Data Ingestion       │           │  AI Analysis        │    │
│  │  Module               │           │  Module             │    │
│  │  (SchoolConnect)      │           │  (OpenAI)           │    │
│  │                       │           │                     │    │
│  └───────────┬───────────┘           └─────────┬───────────┘    │
│              │                                 │                │
│              ▼                                 ▼                │
│  ┌───────────────────────┐           ┌─────────────────────┐    │
│  │                       │           │                     │    │
│  │  Airtable Storage     │◄─────────►│  Airtable Access    │    │
│  │  Module               │           │  Module             │    │
│  │                       │           │                     │    │
│  └───────────────────────┘           └─────────────────────┘    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Features

### Data Ingestion
- Authentication with SchoolConnect
- Fetching announcements with pagination
- Retrieving document attachments
- Storing data in Airtable
- Scheduled synchronization via cron jobs

### AI Analysis
- Conversational AI agent interface
- Document analysis using OpenAI's GPT-4o
- PDF processing and image conversion
- Action item extraction
- Google Calendar integration

### API
- RESTful API endpoints
- Authentication and authorization
- Rate limiting and request validation
- Health monitoring

## Installation

### Prerequisites
- Python 3.11+
- poppler-utils (for PDF processing)
- Access to SchoolConnect and Airtable

### Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/schoolconnect-ai-backend.git
cd schoolconnect-ai-backend
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file with your configuration:
```
DEBUG=False
LOG_LEVEL=INFO
CORS_ORIGINS=["http://localhost:3000"]
AIRTABLE_API_KEY=your_airtable_api_key
AIRTABLE_BASE_ID=your_airtable_base_id
AIRTABLE_TABLE_NAME=Announcements
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4o
```

## Usage

### Running the Server

Start the server with:

```bash
python main.py
```

The server will be available at `http://localhost:8000`.

### API Endpoints

#### Data Ingestion
- `POST /api/ingestion/sync`: Manually trigger data synchronization
- `GET /api/ingestion/status`: Get the status of the last synchronization job
- `GET /api/ingestion/config`: Get the current configuration for data ingestion
- `PUT /api/ingestion/config`: Update the configuration for data ingestion

#### Automated Data Ingestion (Cron Jobs)
To set up automated data ingestion using a cron job, you can use the `/api/ingestion/sync` endpoint with API key authentication:

```bash
# Add to your server's crontab to run daily at midnight
0 0 * * * curl -X POST "https://your-api-url/api/ingestion/sync?api_key=your_cron_api_key"
```

Required environment variables for this approach:
- `CRON_API_KEY`: A secure API key to authenticate cron requests
- `SCHOOLCONNECT_USERNAME`: SchoolConnect username
- `SCHOOLCONNECT_PASSWORD`: SchoolConnect password

This approach avoids issues with expired authentication tokens and doesn't require storing credentials in the cron job itself.

#### AI Analysis
- `POST /api/chat`: Send a message to the AI agent and get a response
- `GET /api/chat/{session_id}`: Get the chat history for a specific session
- `DELETE /api/chat/{session_id}`: Clear the chat history for a specific session
- `GET /api/announcements`: Get all announcements from Airtable
- `GET /api/announcements/search`: Search announcements by text
- `GET /api/announcements/{id}/attachments`: Get attachments for a specific announcement

#### Authentication
- `POST /api/auth/login`: Authenticate with the backend
- `POST /api/auth/refresh`: Refresh authentication token

#### Health Check
- `GET /health`: Check the health of the backend service

## Development

### Best Practices

When working with the SchoolConnect API integration:

1. **Make Incremental Changes**: Any modifications to the document fetching or authentication flow should be done incrementally with testing after each change
2. **Preserve Session State**: Ensure session cookies are maintained between requests
3. **Verify ID Formatting**: Always use the correct ID format for document fetching
4. **Test Document Flow**: Always test the full flow from authentication to document fetching after changes

### Project Structure

```
/
├── src/
│   ├── api/                      # API endpoints
│   ├── core/                     # Core application logic
│   ├── data_ingestion/           # SchoolConnect data ingestion
│   ├── storage/                  # Data storage modules
│   ├── ai_analysis/              # AI analysis modules
│   └── utils/                    # Shared utilities
├── scripts/                      # Utility scripts
├── tests/                        # Test suite
├── main.py                       # Application entry point
└── requirements.txt              # Python dependencies
```

### Running Tests

```bash
pytest
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

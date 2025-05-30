# Unified Backend Architecture for SchoolConnect-AI Project

## Overview

This document outlines the architecture for the merged backend that combines the SchoolConnect data ingestion functionality from ClassTagWorkflowApp with the AI analysis capabilities from ai_agent_project_new. The unified backend is designed to be deployed as a single service on Koyeb while maintaining clear separation of concerns between the data ingestion and AI analysis components.

## Architecture Design

### High-Level Architecture

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

### Core Components

1. **Data Ingestion Module**
   - Handles authentication with SchoolConnect
   - Fetches announcements and documents
   - Implements pagination for data retrieval
   - Scheduled via cron jobs for regular updates

2. **Airtable Storage Module**
   - Manages writing data to Airtable
   - Handles attachments and document storage
   - Implements error handling and retry logic

3. **AI Analysis Module**
   - Provides conversational AI capabilities
   - Integrates with OpenAI for document analysis
   - Manages chat sessions and history

4. **Airtable Access Module**
   - Retrieves data from Airtable
   - Searches and filters announcements
   - Downloads attachments for analysis

5. **API Layer**
   - Unified REST API endpoints
   - Authentication and authorization
   - Rate limiting and request validation

6. **Shared Utilities**
   - Configuration management
   - Logging and monitoring
   - Error handling

## Folder Structure

```
/
├── src/
│   ├── api/                      # API endpoints
│   │   ├── __init__.py
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py           # Authentication routes
│   │   │   ├── ingestion.py      # Data ingestion routes
│   │   │   ├── analysis.py       # AI analysis routes
│   │   │   └── health.py         # Health check routes
│   │   └── middleware/
│   │       ├── __init__.py
│   │       ├── auth.py           # Authentication middleware
│   │       └── error_handler.py  # Error handling middleware
│   │
│   ├── core/                     # Core application logic
│   │   ├── __init__.py
│   │   ├── config.py             # Configuration management
│   │   ├── logging.py            # Logging setup
│   │   └── security.py           # Security utilities
│   │
│   ├── data_ingestion/           # SchoolConnect data ingestion
│   │   ├── __init__.py
│   │   ├── schoolconnect/
│   │   │   ├── __init__.py
│   │   │   ├── client.py         # SchoolConnect API client
│   │   │   ├── auth.py           # Authentication with SchoolConnect
│   │   │   └── models.py         # Data models for SchoolConnect
│   │   └── tasks/
│   │       ├── __init__.py
│   │       ├── fetch_announcements.py  # Announcement fetching logic
│   │       └── fetch_documents.py      # Document fetching logic
│   │
│   ├── storage/                  # Data storage modules
│   │   ├── __init__.py
│   │   └── airtable/
│   │       ├── __init__.py
│   │       ├── client.py         # Airtable client
│   │       ├── models.py         # Data models for Airtable
│   │       └── operations.py     # CRUD operations for Airtable
│   │
│   ├── ai_analysis/             # AI analysis modules
│   │   ├── __init__.py
│   │   ├── agent/
│   │   │   ├── __init__.py
│   │   │   ├── agent_logic.py    # Core agent logic
│   │   │   └── chat_history.py   # Chat history management
│   │   ├── tools/
│   │   │   ├── __init__.py
│   │   │   ├── airtable_tool.py  # Airtable access tool
│   │   │   ├── openai_tool.py    # OpenAI integration tool
│   │   │   ├── pdf_tool.py       # PDF processing tool
│   │   │   └── calendar_tool.py  # Google Calendar integration
│   │   └── models/
│   │       ├── __init__.py
│   │       └── message.py        # Message models
│   │
│   └── utils/                   # Shared utilities
│       ├── __init__.py
│       ├── date_utils.py        # Date handling utilities
│       ├── file_utils.py        # File handling utilities
│       └── validation.py        # Input validation utilities
│
├── scripts/                     # Utility scripts
│   ├── setup.sh                 # Setup script
│   └── cron_setup.sh            # Cron job setup script
│
├── tests/                       # Test suite
│   ├── __init__.py
│   ├── conftest.py              # Test configuration
│   ├── test_data_ingestion/     # Tests for data ingestion
│   ├── test_storage/            # Tests for storage
│   └── test_ai_analysis/        # Tests for AI analysis
│
├── .env.example                 # Example environment variables
├── .gitignore                   # Git ignore file
├── Dockerfile                   # Docker configuration
├── koyeb.yaml                   # Koyeb deployment configuration
├── main.py                      # Application entry point
├── Procfile                     # Process file for deployment
├── README.md                    # Project documentation
└── requirements.txt             # Python dependencies
```

## API Endpoints

### Data Ingestion Endpoints

- `POST /api/ingestion/sync`: Manually trigger data synchronization from SchoolConnect to Airtable
- `GET /api/ingestion/status`: Get the status of the last synchronization job
- `GET /api/ingestion/config`: Get the current configuration for data ingestion
- `PUT /api/ingestion/config`: Update the configuration for data ingestion

### AI Analysis Endpoints

- `POST /api/chat`: Send a message to the AI agent and get a response
- `GET /api/chat/{session_id}`: Get the chat history for a specific session
- `DELETE /api/chat/{session_id}`: Clear the chat history for a specific session
- `GET /api/announcements`: Get all announcements from Airtable
- `GET /api/announcements/search`: Search announcements by text
- `GET /api/announcements/{id}/attachments`: Get attachments for a specific announcement

### Authentication Endpoints

- `POST /api/auth/login`: Authenticate with the backend
- `POST /api/auth/refresh`: Refresh authentication token

### Health Check Endpoints

- `GET /health`: Check the health of the backend service

## Configuration Management

The unified backend will use a centralized configuration management approach with the following features:

1. **Environment Variables**: Core configuration via environment variables for deployment flexibility
2. **Configuration File**: Optional configuration file for local development
3. **Secure Credential Storage**: Sensitive credentials stored securely and not hardcoded
4. **Feature Flags**: Enable/disable specific features (e.g., AI analysis, data ingestion)
5. **Dynamic Configuration**: Some settings can be updated at runtime via API

## Scheduled Tasks

The backend will include scheduled tasks for regular data synchronization:

1. **Daily Announcement Sync**: Fetch new announcements from SchoolConnect daily
2. **Attachment Processing**: Process and store attachments for new announcements
3. **Error Recovery**: Retry failed synchronization tasks automatically
4. **Cleanup Jobs**: Remove temporary files and manage storage

## Security Considerations

1. **API Authentication**: Secure API endpoints with authentication
2. **Credential Management**: Store API keys and credentials securely
3. **Input Validation**: Validate all user inputs to prevent injection attacks
4. **Rate Limiting**: Implement rate limiting to prevent abuse
5. **Error Handling**: Ensure errors don't expose sensitive information

## Deployment Strategy

The unified backend is designed for deployment on Koyeb with the following considerations:

1. **Single Service Deployment**: Deploy as a single service for simplicity
2. **Environment Configuration**: Use environment variables for configuration
3. **Health Checks**: Implement health checks for monitoring
4. **Logging**: Structured logging for observability
5. **Scaling**: Design for horizontal scaling if needed

## Integration Points

### SchoolConnect to Airtable Integration

- Authentication with SchoolConnect
- Fetching announcements with pagination
- Processing attachments
- Storing data in Airtable

### Airtable to AI Analysis Integration

- Retrieving announcements from Airtable
- Accessing and downloading attachments
- Processing PDF documents for analysis
- Analyzing documents with OpenAI

## Next Steps

1. Implement the folder structure and core modules
2. Set up configuration management
3. Implement the data ingestion module
4. Implement the AI analysis module
5. Create unified API endpoints
6. Set up deployment configuration for Koyeb
7. Test the integrated system
8. Document the final implementation

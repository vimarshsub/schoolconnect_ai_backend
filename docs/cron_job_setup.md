# Cron Job Setup for SchoolConnect Data Ingestion

This document explains how to set up a cron job to periodically fetch data from SchoolConnect and sync it to Airtable.

## Authentication

The cron job uses API key authentication to securely access protected endpoints without requiring a JWT token. This is implemented in two parts:

1. API key validation in the middleware
2. API key handling in the ingestion endpoints

### API Key Configuration

1. The API key is stored in the `.env` file as `CRON_API_KEY` for local development.
2. For production, the API key is stored as a GitHub Actions secret.
3. For security, use a strong, random string for the API key value.

Example:
```
CRON_API_KEY=your_secure_random_key_here
```

## Middleware Configuration

The API key is checked in the `AuthMiddleware` class in `src/api/middleware/auth.py`. The middleware allows two authentication methods:

1. JWT token in the Authorization header
2. API key in the query parameters for specific endpoints

The middleware is properly implemented as an ASGI middleware that respects the FastAPI/Starlette middleware pattern.

## Protected Endpoints

The following endpoints support API key authentication:

1. `/api/ingestion/sync` - Main synchronization endpoint
2. `/api/ingestion/cron` - Simplified endpoint specifically for cron jobs

Both endpoints accept the API key as a query parameter:

```
POST /api/ingestion/cron?api_key=your_api_key
```

## Setting Up GitHub Actions Workflow

The cron job is implemented as a GitHub Actions workflow in `.github/workflows/cron-job.yml`. The workflow:

1. Create a workflow file at `.github/workflows/cron-job.yml`.
2. Configure it to run on a schedule (daily at midnight UTC by default).
3. Add the API key as a GitHub secret.

Example workflow:
```yaml
name: SchoolConnect Ingestion Cron Job

on:
  schedule:
    # Runs every day at midnight UTC
    - cron: '0 0 * * *'
  # Allow manual triggering for testing
  workflow_dispatch:

jobs:
  trigger-ingestion:
    runs-on: ubuntu-latest
    steps:
      - name: Trigger Ingestion API
        run: |
          curl -X POST "https://your-app-name.koyeb.app/api/ingestion/cron?api_key=${{ secrets.CRON_API_KEY }}" \
            -H "Content-Type: application/json" \
            -d '{"max_pages": 10}'
```

## Testing API Key Authentication

Several test scripts are provided to verify the API key authentication:

1. `test_cron_api_key.py` - Tests both authentication endpoints
2. `debug_auth_middleware.py` - Debug script to identify authentication issues

## Troubleshooting

If you encounter 401 Unauthorized errors:

1. Verify that the `CRON_API_KEY` is properly set in the GitHub repository secrets
2. Check that the API key is correctly passed as a query parameter
3. Ensure the server has been restarted after any middleware changes
4. Look for any errors in the server logs
5. Use the debug scripts to identify potential issues

## SchoolConnect Credentials

For the data ingestion to work properly, ensure these environment variables are set on your server:

1. `SCHOOLCONNECT_USERNAME` - Your SchoolConnect username
2. `SCHOOLCONNECT_PASSWORD` - Your SchoolConnect password
3. `SCHOOLCONNECT_GRAPHQL_URL` - The GraphQL API endpoint

These are required to authenticate with SchoolConnect and fetch announcements. 
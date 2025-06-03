# Cron Job Setup for SchoolConnect Data Ingestion

This document explains how to set up a cron job to periodically fetch data from SchoolConnect and sync it to Airtable.

## Authentication

The cron job uses API key authentication to securely access protected endpoints without requiring a JWT token. This is implemented in two parts:

1. API key validation in the middleware
2. API key handling in the ingestion endpoints

### API Key Configuration

1. The API key is stored in the `.env` file as `CRON_API_KEY`.
2. For security, use a strong, random string for the API key value.
3. The same API key must be configured in both the main app and the cron job worker.

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
POST /api/ingestion/sync?api_key=your_api_key
```

## Setting Up the Koyeb Worker

To set up a cron job in Koyeb:

1. Create a new Worker service using the `curlimages/curl:latest` Docker image.
2. Set up the Worker to call your backend API with the API key.
3. Configure the environment variable `CRON_API_KEY` with the same value as your main app.

Example Worker command:
```
curl -X POST "https://your-app-name.koyeb.app/api/ingestion/sync?api_key=$CRON_API_KEY" -H "Content-Type: application/json" -d '{"max_pages": 10}'
```

## Testing API Key Authentication

Several test scripts are provided to verify the API key authentication:

1. `test_cron_api_key.py` - Tests both authentication endpoints
2. `test_worker_simple.sh` - Simple bash script to test the API key with curl
3. `debug_auth_middleware.py` - Debug script to identify authentication issues

## Troubleshooting

If you encounter 401 Unauthorized errors:

1. Verify that the `CRON_API_KEY` is properly set in both environments
2. Check that the API key is correctly passed as a query parameter
3. Ensure the server has been restarted after any middleware changes
4. Look for any errors in the server logs
5. Use the debug scripts to identify potential issues

## SchoolConnect Credentials

For the data ingestion to work properly, ensure these environment variables are set:

1. `SCHOOLCONNECT_USERNAME` - Your SchoolConnect username
2. `SCHOOLCONNECT_PASSWORD` - Your SchoolConnect password
3. `SCHOOLCONNECT_GRAPHQL_URL` - The GraphQL API endpoint

These are required by the worker to authenticate with SchoolConnect and fetch announcements. 
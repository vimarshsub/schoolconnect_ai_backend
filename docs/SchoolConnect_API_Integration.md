# SchoolConnect API Integration Guide

This document provides critical information about integrating with the SchoolConnect API, with a focus on document fetching and handling. It is based on lessons learned during troubleshooting and development.

## Authentication Flow

1. **Login Process**
   - Authentication is performed via GraphQL mutation
   - Session cookies must be preserved between requests
   - The API uses multiple cookies to maintain authentication state

2. **Session Handling**
   - Session cookies are critical for maintaining authentication
   - Key cookies include: `_classtag_session`, `user.id`, and `remember_user_token`
   - Re-authentication can reset cookies and break document fetching
   - Use a persistent session object for all requests

## Announcement Fetching

1. **Pagination**
   - Announcements are fetched in paginated batches
   - Each page contains multiple announcement objects
   - The API returns a cursor for fetching subsequent pages

2. **ID Formats**
   - Announcements have two ID formats:
     - GraphQL ID: Used in the GraphQL response (`announcement["id"]`)
     - Database ID: Numeric ID (`announcement["dbId"]`)
   - **IMPORTANT**: Always use the database ID (dbId) for document fetching

## Document Fetching

1. **ID Formatting**
   - Documents must be fetched using the format: `Announcement:{dbId}`
   - Example: `Announcement:15992525`
   - Using incorrect ID format will result in 404 errors

2. **API Quirks**
   - The document fetching endpoint is sensitive to session state
   - Avoid re-authenticating before document fetching
   - Maintain the same session object throughout the entire process
   - The API may return 404 errors if any parameters are incorrect

3. **Document Processing**
   - Filter documents by content type to identify PDFs
   - Verify file extensions for additional validation
   - Handle document URLs carefully as they may be temporary

## Error Handling

1. **Common Errors**
   - 404 errors often indicate incorrect ID format or session issues
   - Authentication failures may not be immediately obvious
   - Session expiration can cause intermittent failures

2. **Debugging Tips**
   - Log session cookies to verify authentication state
   - Log request and response headers for API calls
   - Verify ID formats before making requests
   - Check for session continuity between requests

## Best Practices

1. **Code Changes**
   - Make incremental changes to API integration code
   - Test document fetching after each change
   - Avoid large-scale refactoring without step-by-step testing

2. **Testing**
   - Always test the full flow from authentication to document fetching
   - Verify PDF attachments appear in Airtable
   - Test with various announcement types and document formats

3. **Maintenance**
   - Document any API changes or new requirements
   - Keep this guide updated with new findings
   - Consider implementing automated tests for critical paths

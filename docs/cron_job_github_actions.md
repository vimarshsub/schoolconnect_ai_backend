# SchoolConnect Cron Job Setup with GitHub Actions

This documentation explains how the automated data ingestion is set up using GitHub Actions.

## Overview

GitHub Actions is used to periodically trigger the data ingestion API endpoint on the SchoolConnect backend server. This allows for regular, automated synchronization of data from SchoolConnect to our database.

## Configuration

The cron job is configured in `.github/workflows/cron-job.yml` and includes:

1. A schedule that runs every day at midnight UTC (configurable)
2. A manual trigger option for testing
3. A simple job that uses curl to call the API endpoint with the necessary API key

## API Key Security

The API key is stored as a GitHub secret (`CRON_API_KEY`) to keep it secure. It's never exposed in the code or logs.

## Setup Instructions

To set up the GitHub Actions cron job:

1. Navigate to your GitHub repository settings
2. Go to "Secrets and variables" → "Actions"
3. Add a new repository secret with the name `CRON_API_KEY`
4. Set the value to your actual API key: `891ea42d2aab554ea57e4437dcd6938ca80b4f7759934a05559936c617359ca3`

## Customizing the Schedule

The cron job is currently set to run every day at midnight UTC. To modify this schedule:

1. Edit the `.github/workflows/cron-job.yml` file
2. Update the cron expression in the `schedule` section

### Common Cron Examples:

- Every day at midnight: `0 0 * * *`
- Every hour: `0 * * * *`
- Every Monday at 9 AM: `0 9 * * 1`
- Every 15 minutes: `*/15 * * * *`

## Troubleshooting

If the cron job is not running as expected:

1. Check the "Actions" tab in your GitHub repository to see the workflow runs
2. Verify that the API key is correctly set up as a secret
3. Test the workflow manually using the "Run workflow" button in the Actions tab
4. Check that your API endpoint is accessible and responding correctly

## Manual Trigger

You can manually trigger the workflow at any time by:

1. Going to the "Actions" tab in your GitHub repository
2. Selecting the "SchoolConnect Ingestion Cron Job" workflow
3. Clicking "Run workflow" 
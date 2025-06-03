#!/usr/bin/env python
"""
Simple script to check if CRON_API_KEY is properly set in the environment.
"""

import os
from dotenv import load_dotenv
from src.core.config import get_settings

# Load environment variables
load_dotenv()

# Get the API key directly from environment
env_api_key = os.getenv("CRON_API_KEY")
print(f"CRON_API_KEY from environment: {env_api_key}")

# Get the API key from settings
settings = get_settings()
settings_api_key = settings.CRON_API_KEY
print(f"CRON_API_KEY from settings: {settings_api_key}")

# Check if they match
if env_api_key == settings_api_key:
    print("✅ API keys match!")
else:
    print("❌ API keys don't match!")
    
# Check if API key is set to a valid value
if not settings_api_key:
    print("❌ CRON_API_KEY is not set in settings!")
else:
    print(f"✅ CRON_API_KEY is set in settings: {settings_api_key}") 
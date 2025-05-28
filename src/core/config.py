"""
Configuration management for the SchoolConnect-AI unified backend.
"""

import os
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field
from functools import lru_cache

class Settings(BaseSettings):
    """Application settings loaded from environment variables with defaults."""
    
    # SchoolConnect settings
    SCHOOLCONNECT_USERNAME: str = Field("", env="SCHOOLCONNECT_USERNAME")
    SCHOOLCONNECT_PASSWORD: str = Field("", env="SCHOOLCONNECT_PASSWORD")
    
    # Airtable settings
    AIRTABLE_API_KEY: str = Field("", env="AIRTABLE_API_KEY")
    AIRTABLE_BASE_ID: str = Field("", env="AIRTABLE_BASE_ID")
    AIRTABLE_TABLE_NAME: str = Field("Announcements", env="AIRTABLE_TABLE_NAME")
    
    # OpenAI settings
    OPENAI_API_KEY: str = Field("", env="OPENAI_API_KEY")
    
    # Internal settings with defaults (not required as environment variables)
    DEBUG: bool = False
    PORT: int = 8000
    API_PREFIX: str = "/api"
    CORS_ORIGINS: List[str] = ["*"]
    SCHOOLCONNECT_GRAPHQL_URL: str = "https://connect.schoolstatus.com/graphql"
    OPENAI_MODEL: str = "gpt-4o"
    TEMP_FILE_DIR: str = "/tmp/schoolconnect_ai"
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Allow extra fields in environment variables

# Use lru_cache to ensure settings are loaded only once per process
@lru_cache()
def get_settings() -> Settings:
    """Get application settings."""
    return Settings()

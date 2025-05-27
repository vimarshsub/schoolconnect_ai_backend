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
    
    # General settings
    DEBUG: bool = Field(False, env="DEBUG")
    LOG_LEVEL: str = Field("INFO", env="LOG_LEVEL")
    PORT: int = Field(8000, env="PORT")
    
    # API settings
    API_PREFIX: str = Field("/api", env="API_PREFIX")
    CORS_ORIGINS: List[str] = Field(["*"], env="CORS_ORIGINS")
    
    # SchoolConnect settings
    SCHOOLCONNECT_USERNAME: str = Field("", env="SCHOOLCONNECT_USERNAME")
    SCHOOLCONNECT_PASSWORD: str = Field("", env="SCHOOLCONNECT_PASSWORD")
    SCHOOLCONNECT_GRAPHQL_URL: str = Field(
        "https://connect.schoolstatus.com/graphql", 
        env="SCHOOLCONNECT_GRAPHQL_URL"
    )
    
    # Airtable settings
    AIRTABLE_API_KEY: str = Field("", env="AIRTABLE_API_KEY")
    AIRTABLE_BASE_ID: str = Field("", env="AIRTABLE_BASE_ID")
    AIRTABLE_TABLE_NAME: str = Field("Announcements", env="AIRTABLE_TABLE_NAME")
    
    # OpenAI settings
    OPENAI_API_KEY: str = Field("", env="OPENAI_API_KEY")
    OPENAI_MODEL: str = Field("gpt-4o", env="OPENAI_MODEL")
    
    # Google Calendar settings
    GOOGLE_CALENDAR_CREDENTIALS: Optional[str] = Field(None, env="GOOGLE_CALENDAR_CREDENTIALS")
    
    # File storage settings
    TEMP_FILE_DIR: str = Field("/tmp/schoolconnect_ai", env="TEMP_FILE_DIR")
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Allow extra fields in environment variables

# Use lru_cache to ensure settings are loaded only once per process
@lru_cache()
def get_settings() -> Settings:
    """Get application settings."""
    return Settings()

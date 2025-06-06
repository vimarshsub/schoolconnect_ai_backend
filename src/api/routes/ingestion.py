"""
API routes for data ingestion operations.
"""

import os
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Request
from pydantic import BaseModel
from typing import Dict, Any, Optional

from src.api.routes.auth import get_current_user
from src.data_ingestion.tasks.fetch_announcements import FetchAnnouncementsTask
from src.core.config import get_settings

router = APIRouter()

class SyncRequest(BaseModel):
    """Request model for data synchronization."""
    username: Optional[str] = None
    password: Optional[str] = None
    max_pages: Optional[int] = 5

class SyncResponse(BaseModel):
    """Response model for data synchronization."""
    success: bool
    message: str
    details: Optional[Dict[str, Any]] = None

# Store the status of the last sync job
last_sync_status = {
    "in_progress": False,
    "success": None,
    "message": "No synchronization has been run yet",
    "details": None,
    "timestamp": None
}

# Helper function to check if API key is valid
async def get_current_user_or_api_key(request: Request):
    """
    Get current user from token or validate API key.
    Used for endpoints that support both authentication methods.
    
    Args:
        request: FastAPI request
        
    Returns:
        User object
        
    Raises:
        HTTPException: If authentication fails
    """
    # Check for API key in query parameters
    api_key = request.query_params.get("api_key")
    if api_key:
        # Validate API key
        settings = get_settings()
        if api_key == settings.CRON_API_KEY:
            # API key is valid, return a minimal user object
            return {"username": "api_key_user"}
    
    # If no valid API key, fall back to token authentication
    return await get_current_user(request)

@router.post("/sync", response_model=SyncResponse)
async def sync_data(
    request: Request,
    sync_request: SyncRequest,
    background_tasks: BackgroundTasks,
    current_user = Depends(get_current_user_or_api_key)
):
    """
    Manually trigger data synchronization from SchoolConnect to Airtable.
    
    If username and password are not provided in the request, the system will use
    the credentials from environment variables (SCHOOLCONNECT_USERNAME and SCHOOLCONNECT_PASSWORD).
    
    Authentication can be done either via:
    - JWT token in Authorization header
    - API key in query parameter (?api_key=YOUR_API_KEY)
    """
    if last_sync_status["in_progress"]:
        return SyncResponse(
            success=False,
            message="A synchronization job is already in progress",
            details={"status": "in_progress"}
        )
    
    # Get settings for credentials if not provided in request
    settings = get_settings()
    
    # Use credentials from request if provided, otherwise use from environment
    username = sync_request.username if sync_request.username else settings.SCHOOLCONNECT_USERNAME
    password = sync_request.password if sync_request.password else settings.SCHOOLCONNECT_PASSWORD
    
    # Validate credentials
    if not username or not password:
        return SyncResponse(
            success=False,
            message="SchoolConnect credentials not provided in request or environment variables",
            details={"status": "error", "error": "missing_credentials"}
        )
    
    # Start sync in background
    background_tasks.add_task(
        run_sync_task,
        username,
        password,
        sync_request.max_pages
    )
    
    return SyncResponse(
        success=True,
        message="Synchronization job started",
        details={"status": "started"}
    )

@router.get("/status", response_model=SyncResponse)
async def get_sync_status(current_user = Depends(get_current_user)):
    """
    Get the status of the last synchronization job.
    """
    if last_sync_status["in_progress"]:
        return SyncResponse(
            success=True,
            message="Synchronization job is in progress",
            details={"status": "in_progress", "timestamp": last_sync_status["timestamp"]}
        )
    elif last_sync_status["success"] is None:
        return SyncResponse(
            success=True,
            message="No synchronization has been run yet",
            details={"status": "none"}
        )
    else:
        return SyncResponse(
            success=last_sync_status["success"],
            message=last_sync_status["message"],
            details=last_sync_status["details"]
        )

class ConfigRequest(BaseModel):
    """Request model for updating configuration."""
    max_pages: Optional[int] = None
    schedule_enabled: Optional[bool] = None
    schedule_cron: Optional[str] = None

class ConfigResponse(BaseModel):
    """Response model for configuration."""
    max_pages: int
    schedule_enabled: bool
    schedule_cron: str

# Default configuration
config = {
    "max_pages": 5,
    "schedule_enabled": True,
    "schedule_cron": "0 0 * * *"  # Daily at midnight
}

@router.get("/config", response_model=ConfigResponse)
async def get_config(current_user = Depends(get_current_user)):
    """
    Get the current configuration for data ingestion.
    """
    return ConfigResponse(**config)

@router.put("/config", response_model=ConfigResponse)
async def update_config(
    request: ConfigRequest,
    current_user = Depends(get_current_user)
):
    """
    Update the configuration for data ingestion.
    """
    if request.max_pages is not None:
        config["max_pages"] = request.max_pages
    
    if request.schedule_enabled is not None:
        config["schedule_enabled"] = request.schedule_enabled
    
    if request.schedule_cron is not None:
        config["schedule_cron"] = request.schedule_cron
    
    return ConfigResponse(**config)

@router.post("/cron", response_model=SyncResponse)
async def cron_sync_data(
    background_tasks: BackgroundTasks,
    api_key: str = None
):
    """
    Special endpoint for scheduled cron jobs to trigger data synchronization.
    This endpoint uses environment variables for SchoolConnect credentials
    and requires an API key for authentication.
    
    Args:
        background_tasks: FastAPI background tasks
        api_key: API key for authentication (passed as query parameter)
        
    Returns:
        SyncResponse
    """
    # Get settings
    settings = get_settings()
    
    # Validate API key (compare with environment variable)
    if not api_key or api_key != settings.CRON_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key"
        )
    
    if last_sync_status["in_progress"]:
        return SyncResponse(
            success=False,
            message="A synchronization job is already in progress",
            details={"status": "in_progress"}
        )
    
    # Use credentials from environment variables
    username = settings.SCHOOLCONNECT_USERNAME
    password = settings.SCHOOLCONNECT_PASSWORD
    
    # Validate credentials
    if not username or not password:
        return SyncResponse(
            success=False,
            message="SchoolConnect credentials not configured in environment variables",
            details={"status": "error", "error": "missing_credentials"}
        )
    
    # Start sync in background
    background_tasks.add_task(
        run_sync_task,
        username,
        password,
        config["max_pages"]  # Use the configured max_pages
    )
    
    return SyncResponse(
        success=True,
        message="Cron-triggered synchronization job started",
        details={"status": "started"}
    )

async def run_sync_task(username: str, password: str, max_pages: int):
    """
    Run the synchronization task.
    """
    import datetime
    
    # Update status
    last_sync_status["in_progress"] = True
    last_sync_status["timestamp"] = datetime.datetime.now().isoformat()
    
    try:
        # Run the task
        task = FetchAnnouncementsTask()
        result = task.execute(username, password, max_pages)
        
        # Update status based on result
        last_sync_status["success"] = result.get("success", False)
        if result.get("success"):
            last_sync_status["message"] = "Synchronization completed successfully"
        else:
            last_sync_status["message"] = f"Synchronization failed: {result.get('error', 'Unknown error')}"
        
        last_sync_status["details"] = {
            "announcements_processed": result.get("announcements_processed", 0),
            "announcements_saved": result.get("announcements_saved", 0),
            "completed_at": datetime.datetime.now().isoformat()
        }
    except Exception as e:
        last_sync_status["success"] = False
        last_sync_status["message"] = f"Synchronization failed with an exception: {str(e)}"
        last_sync_status["details"] = {
            "error": str(e),
            "completed_at": datetime.datetime.now().isoformat()
        }
    finally:
        last_sync_status["in_progress"] = False

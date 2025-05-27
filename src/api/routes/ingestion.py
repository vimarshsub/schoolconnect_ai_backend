"""
API routes for data ingestion operations.
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, Any, Optional

from src.api.routes.auth import get_current_user
from src.data_ingestion.tasks.fetch_announcements import FetchAnnouncementsTask

router = APIRouter()

class SyncRequest(BaseModel):
    """Request model for data synchronization."""
    username: str
    password: str
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

@router.post("/sync", response_model=SyncResponse)
async def sync_data(
    request: SyncRequest,
    background_tasks: BackgroundTasks,
    current_user = Depends(get_current_user)
):
    """
    Manually trigger data synchronization from SchoolConnect to Airtable.
    """
    if last_sync_status["in_progress"]:
        return SyncResponse(
            success=False,
            message="A synchronization job is already in progress",
            details={"status": "in_progress"}
        )
    
    # Start sync in background
    background_tasks.add_task(
        run_sync_task,
        request.username,
        request.password,
        request.max_pages
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

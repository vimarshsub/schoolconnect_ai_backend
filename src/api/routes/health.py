"""
API routes for health check.
"""

from fastapi import APIRouter, Response, status
import psutil
import time

router = APIRouter()

@router.get("/health")
async def health_check():
    """
    Check the health of the backend service.
    """
    # Get system metrics
    cpu_percent = psutil.cpu_percent(interval=0.1)
    memory_info = psutil.virtual_memory()
    disk_info = psutil.disk_usage('/')
    
    # Check if metrics are within acceptable ranges
    healthy = (
        cpu_percent < 90 and
        memory_info.percent < 90 and
        disk_info.percent < 90
    )
    
    # Prepare response
    health_data = {
        "status": "healthy" if healthy else "unhealthy",
        "timestamp": time.time(),
        "metrics": {
            "cpu": {
                "percent": cpu_percent
            },
            "memory": {
                "total": memory_info.total,
                "available": memory_info.available,
                "percent": memory_info.percent
            },
            "disk": {
                "total": disk_info.total,
                "free": disk_info.free,
                "percent": disk_info.percent
            }
        }
    }
    
    # Set appropriate status code
    status_code = status.HTTP_200_OK if healthy else status.HTTP_503_SERVICE_UNAVAILABLE
    
    return health_data

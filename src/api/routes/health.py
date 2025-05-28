"""
API routes for health check.
"""

from fastapi import APIRouter, Response, status

router = APIRouter()

@router.get("/health")
async def health_check():
    """
    Simple health check endpoint that returns a 200 OK status.
    """
    return {"status": "healthy"}

"""
Error handling middleware.
"""

from fastapi import Request, Response
from fastapi.responses import JSONResponse
import logging
import traceback
import json

logger = logging.getLogger("schoolconnect_ai")

class ErrorHandlerMiddleware:
    """Middleware for handling errors."""
    
    def __init__(self, app):
        """Initialize the middleware."""
        self.app = app
    
    async def __call__(self, request: Request, call_next):
        """
        Process the request and handle errors.
        
        Args:
            request: FastAPI request
            call_next: Next middleware or route handler
            
        Returns:
            Response
        """
        try:
            return await call_next(request)
        except Exception as e:
            # Log the error
            logger.error(f"Unhandled exception: {str(e)}")
            logger.error(traceback.format_exc())
            
            # Return error response
            return JSONResponse(
                status_code=500,
                content={
                    "detail": "Internal server error",
                    "message": str(e)
                }
            )

"""
API package initialization.

Middleware configuration for the API.
"""

from fastapi import FastAPI
from src.api.middleware.auth import AuthMiddleware

def setup_middleware(app: FastAPI):
    """
    Configure middleware for the FastAPI application.
    
    Args:
        app: FastAPI application
    """
    # Add authentication middleware
    app.add_middleware(AuthMiddleware)
    
    return app

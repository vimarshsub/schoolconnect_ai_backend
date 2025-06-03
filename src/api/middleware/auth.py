"""
Middleware for authentication.
"""

from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from jwt.exceptions import PyJWTError
import logging
from typing import Callable

from src.core.security import JWT_SECRET_KEY, JWT_ALGORITHM

logger = logging.getLogger("schoolconnect_ai")

security = HTTPBearer()

async def verify_token(credentials: HTTPAuthorizationCredentials = security):
    """
    Verify JWT token.
    
    Args:
        credentials: HTTP Authorization credentials
        
    Returns:
        Decoded token payload
        
    Raises:
        HTTPException: If token is invalid
    """
    try:
        payload = jwt.decode(
            credentials.credentials, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM]
        )
        return payload
    except PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

class AuthMiddleware:
    """Middleware for authentication."""
    
    def __init__(self, app):
        """Initialize the middleware."""
        self.app = app
    
    async def __call__(self, scope, receive, send):
        """
        Process the request.
        
        Args:
            scope: ASGI scope
            receive: ASGI receive function
            send: ASGI send function
            
        Returns:
            ASGI response
        """
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
            
        # Create a request object from the scope for easier handling
        request = Request(scope)
            
        # Skip authentication for certain paths
        if request.url.path in ["/health", "/api/auth/login", "/api/auth/refresh"]:
            return await self.app(scope, receive, send)
            
        # Check for API key in query parameters for protected endpoints
        api_key = request.query_params.get("api_key")
        logger.debug(f"API key in request: {api_key}")
        
        # Allow API key authentication for ingestion and GraphQL endpoints
        if api_key and (request.url.path == "/api/ingestion/sync" or request.url.path == "/api/ingestion/cron" or "/graphql" in request.url.path):
            from src.core.config import get_settings
            settings = get_settings()
            logger.debug(f"Comparing API keys for {request.url.path}")
            if api_key == settings.CRON_API_KEY:
                # API key is valid, allow the request
                logger.debug(f"API key is valid, allowing request to {request.url.path}")
                return await self.app(scope, receive, send)
            else:
                logger.debug(f"API key is invalid for {request.url.path}")
        
        # Check for Authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            # Return 401 Unauthorized response
            return await self._unauthorized_response(send)
        
        # Verify token
        try:
            scheme, token = auth_header.split()
            if scheme.lower() != "bearer":
                return await self._unauthorized_response(send, "Invalid authentication scheme")
            
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
            # Store user in request state by modifying the scope
            scope["state"] = {"user": payload}
            
        except (ValueError, PyJWTError):
            return await self._unauthorized_response(send)
        
        return await self.app(scope, receive, send)
    
    async def _unauthorized_response(self, send: Callable, detail: str = "Unauthorized"):
        """
        Send a 401 Unauthorized response.
        
        Args:
            send: ASGI send function
            detail: Error detail message
            
        Returns:
            None
        """
        await send({
            "type": "http.response.start",
            "status": status.HTTP_401_UNAUTHORIZED,
            "headers": [
                (b"content-type", b"application/json"),
                (b"www-authenticate", b"Bearer"),
            ],
        })
        
        body = f'{{"detail": "{detail}"}}'.encode("utf-8")
        await send({
            "type": "http.response.body",
            "body": body,
        })
        
        return

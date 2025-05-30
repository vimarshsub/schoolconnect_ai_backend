"""
Middleware for authentication.
"""

from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from jwt.exceptions import PyJWTError

from src.core.security import JWT_SECRET_KEY, JWT_ALGORITHM

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
    
    async def __call__(self, request: Request, call_next):
        """
        Process the request.
        
        Args:
            request: FastAPI request
            call_next: Next middleware or route handler
            
        Returns:
            Response
        """
        # Skip authentication for certain paths
        if request.url.path in ["/health", "/api/auth/login", "/api/auth/refresh"]:
            return await call_next(request)
        
        # Check for Authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authorization header missing",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Verify token
        try:
            scheme, token = auth_header.split()
            if scheme.lower() != "bearer":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid authentication scheme",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
            request.state.user = payload
            
        except (ValueError, PyJWTError):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return await call_next(request)

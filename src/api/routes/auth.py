"""
API routes for authentication.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import Optional

from src.core.security import create_access_token, decode_access_token

router = APIRouter()

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

class Token(BaseModel):
    """Token response model."""
    access_token: str
    token_type: str

class TokenData(BaseModel):
    """Token data model."""
    username: Optional[str] = None

class User(BaseModel):
    """User model."""
    username: str
    disabled: Optional[bool] = None

@router.post("/login", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Authenticate user and return access token.
    
    This is a simplified implementation that accepts any username/password
    for demonstration purposes. In a real application, this would validate
    against a user database.
    """
    # For demonstration, accept any username/password
    user = {"username": form_data.username}
    
    access_token = create_access_token(data={"sub": user["username"]})
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/refresh", response_model=Token)
async def refresh_token(token: str = Depends(oauth2_scheme)):
    """
    Refresh an access token.
    """
    try:
        payload = decode_access_token(token)
        username = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Create a new token
        access_token = create_access_token(data={"sub": username})
        return {"access_token": access_token, "token_type": "bearer"}
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def get_current_user(token: str = Depends(oauth2_scheme)):
    """
    Get the current user from the token.
    """
    try:
        payload = decode_access_token(token)
        username = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        token_data = TokenData(username=username)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # In a real application, we would fetch the user from a database
    user = User(username=token_data.username)
    return user

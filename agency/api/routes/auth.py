from typing import Dict, List, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Security
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, Field

from ...utils.logging import get_logger
from ...utils.security import generate_jwt, verify_password, hash_password, create_api_key
from ..middleware.auth import get_current_user, admin_required

logger = get_logger(__name__)

# Request and response models
class TokenResponse(BaseModel):
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field("bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration time in seconds")

class ApiKeyResponse(BaseModel):
    api_key: str = Field(..., description="Generated API key")

def create_router(dependencies: Dict[str, Any]) -> APIRouter:
    """
    Create a router for authentication-related endpoints.
    
    Args:
        dependencies: Dictionary of dependencies
    
    Returns:
        FastAPI router
    """
    router = APIRouter()
    
    # In a real implementation, these would be stored in a database
    # For demonstration purposes, we'll use an in-memory dictionary
    users = {
        "admin": {
            "username": "admin",
            "password_hash": hash_password("admin"),  # NEVER use hardcoded passwords in production
            "role": "admin"
        }
    }
    
    @router.post(
        "/token",
        response_model=TokenResponse,
        summary="Get access token",
        description="Get a JWT access token for API access"
    )
    async def login(form_data: OAuth2PasswordRequestForm = Depends()):
        """Get a JWT access token for API access."""
        # Check if user exists
        user = users.get(form_data.username)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Check password
        if not verify_password(user["password_hash"], form_data.password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Generate token
        token_data = {
            "sub": user["username"],
            "user_id": user["username"],
            "role": user["role"]
        }
        
        # Default expiration is 24 hours (from Config.JWT_EXPIRATION)
        from ...config import Config
        token = generate_jwt(token_data)
        
        return {
            "access_token": token,
            "token_type": "bearer",
            "expires_in": Config.JWT_EXPIRATION
        }
    
    @router.post(
        "/api-key",
        response_model=ApiKeyResponse,
        summary="Generate API key",
        description="Generate a new API key (admin only)"
    )
    async def generate_api_key(current_user = Depends(admin_required)):
        """Generate a new API key (admin only)."""
        # Generate a new API key
        api_key = create_api_key()
        
        # In a real implementation, you would store the API key in a database
        # and associate it with the current user
        
        return {
            "api_key": api_key
        }
    
    @router.get(
        "/me",
        summary="Get current user",
        description="Get information about the currently authenticated user"
    )
    async def get_me(current_user = Depends(get_current_user)):
        """Get information about the currently authenticated user."""
        return current_user
    
    return router

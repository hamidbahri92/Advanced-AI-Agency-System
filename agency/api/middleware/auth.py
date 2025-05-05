from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader, OAuth2PasswordBearer
from starlette.requests import Request

from ...config import Config
from ...utils.security import verify_api_key, verify_jwt

# API key authentication
api_key_header = APIKeyHeader(name="x-api-key", auto_error=False)

# JWT authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token", auto_error=False)

async def authenticate_request(
    request: Request,
    api_key: str = Security(api_key_header),
    token: str = Depends(oauth2_scheme)
) -> None:
    """
    Authenticate a request using either API key or JWT.
    
    Args:
        request: HTTP request
        api_key: API key from header
        token: JWT token from Authorization header
    
    Raises:
        HTTPException: If authentication fails
    """
    # Try API key first
    if api_key:
        if api_key == Config.API_KEY:
            return
    
    # Try JWT next
    if token:
        payload = verify_jwt(token)
        if payload:
            # Store user info in request state
            request.state.user = payload.get("sub")
            request.state.user_id = payload.get("user_id")
            return
    
    # Authentication failed
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer"}
    )

def get_current_user(request: Request = None) -> dict:
    """
    Get the current authenticated user.
    
    Args:
        request: HTTP request
    
    Returns:
        User information
    
    Raises:
        HTTPException: If not authenticated
    """
    if not request or not hasattr(request.state, "user"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    return {
        "username": request.state.user,
        "user_id": request.state.user_id
    }

class RoleChecker:
    """Check if the current user has the required role."""
    
    def __init__(self, required_role: str):
        """
        Initialize the role checker.
        
        Args:
            required_role: Required role (e.g., 'admin', 'user')
        """
        self.required_role = required_role
    
    def __call__(self, request: Request = None) -> None:
        """
        Check if the user has the required role.
        
        Args:
            request: HTTP request
        
        Raises:
            HTTPException: If the user doesn't have the required role
        """
        if not request or not hasattr(request.state, "user"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated"
            )
        
        # In a real implementation, this would check the user's role
        # For now, we'll assume all authenticated users have all roles
        # You would typically retrieve the user's roles from a database
        user_role = "admin"  # Placeholder
        
        if user_role != self.required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{self.required_role}' required"
            )

# Convenience dependencies
admin_required = RoleChecker("admin")
user_required = RoleChecker("user")

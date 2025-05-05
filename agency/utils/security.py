import time
import jwt
from typing import Dict, Any, Optional
from starlette.requests import Request

from ..config import Config
from .logging import get_logger

logger = get_logger(__name__)

def verify_api_key(request: Request) -> bool:
    """
    Verify the API key in the request.
    
    Args:
        request: HTTP request
    
    Returns:
        True if the API key is valid, False otherwise
    """
    api_key = request.headers.get("x-api-key")
    if not api_key:
        return False
    
    return api_key == Config.API_KEY

def generate_jwt(payload: Dict[str, Any], expiration: Optional[int] = None) -> str:
    """
    Generate a JWT token.
    
    Args:
        payload: Data to include in the token
        expiration: Optional expiration time in seconds
    
    Returns:
        JWT token as a string
    """
    # Add expiration time
    if expiration is None:
        expiration = Config.JWT_EXPIRATION
        
    payload["exp"] = int(time.time()) + expiration
    
    # Generate the token
    token = jwt.encode(
        payload,
        Config.JWT_SECRET,
        algorithm=Config.JWT_ALGORITHM
    )
    
    return token

def verify_jwt(token: str) -> Optional[Dict[str, Any]]:
    """
    Verify a JWT token.
    
    Args:
        token: JWT token to verify
    
    Returns:
        Decoded payload if valid, None otherwise
    """
    try:
        payload = jwt.decode(
            token,
            Config.JWT_SECRET,
            algorithms=[Config.JWT_ALGORITHM]
        )
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning("JWT token expired")
        return None
    except jwt.InvalidTokenError:
        logger.warning("Invalid JWT token")
        return None

def create_api_key() -> str:
    """
    Create a new API key.
    
    Returns:
        Generated API key
    """
    import secrets
    
    # Generate a secure random token
    token = secrets.token_hex(32)
    
    return token

def hash_password(password: str) -> str:
    """
    Hash a password for storage.
    
    Args:
        password: Plain text password
    
    Returns:
        Hashed password
    """
    import hashlib
    import os
    
    # Generate a random salt
    salt = os.urandom(32)
    
    # Hash the password with the salt
    hash_obj = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt,
        100000
    )
    
    # Combine the salt and hash for storage
    return salt.hex() + ':' + hash_obj.hex()

def verify_password(stored_password: str, provided_password: str) -> bool:
    """
    Verify a password against a stored hash.
    
    Args:
        stored_password: Stored password hash
        provided_password: Plain text password to verify
    
    Returns:
        True if the password is correct, False otherwise
    """
    import hashlib
    
    # Split the stored password into salt and hash
    salt_hex, hash_hex = stored_password.split(':')
    
    # Convert the salt and hash from hex
    salt = bytes.fromhex(salt_hex)
    stored_hash = bytes.fromhex(hash_hex)
    
    # Hash the provided password with the same salt
    hash_obj = hashlib.pbkdf2_hmac(
        'sha256',
        provided_password.encode('utf-8'),
        salt,
        100000
    )
    
    # Compare the hashes
    return hash_obj == stored_hash

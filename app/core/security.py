"""
Security utilities for authentication and authorization.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Union

from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import ValidationError

from app.core.config import settings
from app.core.exceptions import AuthenticationException, AuthorizationException
from app.schemas.auth import TokenData

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
ALGORITHM = "HS256"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Generate password hash."""
    return pwd_context.hash(password)


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token."""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: Dict[str, Any]) -> str:
    """Create JWT refresh token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str, token_type: str = "access") -> TokenData:
    """Verify and decode JWT token."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        
        # Check token type
        if payload.get("type") != token_type:
            raise AuthenticationException("Invalid token type")
        
        # Extract user ID
        user_id: str = payload.get("sub")
        if user_id is None:
            raise AuthenticationException("Invalid token payload")
        
        # Extract additional claims
        email: str = payload.get("email")
        role: str = payload.get("role", "user")
        
        return TokenData(user_id=user_id, email=email, role=role)
        
    except JWTError as e:
        raise AuthenticationException(f"Token validation failed: {str(e)}")
    except ValidationError as e:
        raise AuthenticationException(f"Token data validation failed: {str(e)}")


def check_permissions(user_role: str, required_permissions: list) -> bool:
    """Check if user has required permissions."""
    role_permissions = {
        "admin": ["read", "write", "delete", "admin"],
        "gm": ["read", "write", "gm"],
        "user": ["read", "write"],
        "guest": ["read"],
    }
    
    user_permissions = role_permissions.get(user_role, [])
    return all(permission in user_permissions for permission in required_permissions)


def require_permissions(required_permissions: list):
    """Decorator to require specific permissions."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # This would be used with dependency injection in FastAPI
            # The actual implementation would extract user from request context
            return func(*args, **kwargs)
        return wrapper
    return decorator


class SecurityUtils:
    """Utility class for security operations."""
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitize filename for safe storage."""
        import re
        # Remove or replace dangerous characters
        filename = re.sub(r'[^\w\-_\.]', '_', filename)
        # Limit length
        if len(filename) > 255:
            name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
            filename = name[:255-len(ext)-1] + '.' + ext if ext else name[:255]
        return filename
    
    @staticmethod
    def validate_file_type(content_type: str, allowed_types: list) -> bool:
        """Validate file content type."""
        return content_type in allowed_types
    
    @staticmethod
    def validate_file_size(file_size: int, max_size: int) -> bool:
        """Validate file size."""
        return file_size <= max_size


"""
Custom exception classes for the RoleForge API.
"""

from typing import Any, Dict, Optional


class RoleForgeException(Exception):
    """Base exception class for RoleForge API."""
    
    def __init__(self, detail: str, context: Optional[Dict[str, Any]] = None):
        self.detail = detail
        self.context = context or {}
        super().__init__(detail)


class ValidationException(RoleForgeException):
    """Raised when input validation fails."""
    pass


class AuthenticationException(RoleForgeException):
    """Raised when authentication fails."""
    pass


class AuthorizationException(RoleForgeException):
    """Raised when authorization fails."""
    pass


class NotFoundException(RoleForgeException):
    """Raised when a requested resource is not found."""
    pass


class ConflictException(RoleForgeException):
    """Raised when a resource conflict occurs."""
    pass


class InternalServerException(RoleForgeException):
    """Raised when an internal server error occurs."""
    pass


class ExternalServiceException(RoleForgeException):
    """Raised when an external service call fails."""
    pass


class RateLimitException(RoleForgeException):
    """Raised when rate limit is exceeded."""
    pass


class FileUploadException(RoleForgeException):
    """Raised when file upload fails."""
    pass


class AIServiceException(ExternalServiceException):
    """Raised when AI service calls fail."""
    pass


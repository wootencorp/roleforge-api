"""
Authentication endpoints for user management.
"""

from datetime import timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    verify_password,
    verify_token,
    get_password_hash,
)
from app.core.exceptions import (
    AuthenticationException,
    ValidationException,
    ConflictException,
    NotFoundException,
)
from app.schemas.auth import (
    UserCreate,
    UserLogin,
    UserResponse,
    Token,
    TokenRefresh,
    PasswordChange,
    UserUpdate,
    TokenData,
)
from app.services.auth_service import AuthService
from app.services.user_service import UserService

router = APIRouter()
security = HTTPBearer()

# Dependency injection
def get_auth_service() -> AuthService:
    return AuthService()

def get_user_service() -> UserService:
    return UserService()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    user_service: UserService = Depends(get_user_service),
) -> UserResponse:
    """Get current authenticated user."""
    try:
        token_data = verify_token(credentials.credentials)
        user = await user_service.get_user_by_id(token_data.user_id)
        if not user:
            raise AuthenticationException("User not found")
        return user
    except AuthenticationException:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    auth_service: AuthService = Depends(get_auth_service),
) -> Any:
    """Register a new user."""
    try:
        # Check if user already exists
        existing_user = await auth_service.get_user_by_email(user_data.email)
        if existing_user:
            raise ConflictException("User with this email already exists")
        
        existing_username = await auth_service.get_user_by_username(user_data.username)
        if existing_username:
            raise ConflictException("Username already taken")
        
        # Create new user
        user = await auth_service.create_user(user_data)
        
        # Generate tokens
        access_token = create_access_token(
            data={"sub": user.id, "email": user.email, "role": user.role}
        )
        refresh_token = create_refresh_token(
            data={"sub": user.id, "email": user.email}
        )
        
        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )
        
    except ConflictException as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=e.detail)
    except ValidationException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.detail)


@router.post("/login", response_model=Token)
async def login(
    user_data: UserLogin,
    auth_service: AuthService = Depends(get_auth_service),
) -> Any:
    """Authenticate user and return tokens."""
    try:
        # Verify user credentials
        user = await auth_service.authenticate_user(user_data.email, user_data.password)
        if not user:
            raise AuthenticationException("Invalid email or password")
        
        # Generate tokens
        access_token = create_access_token(
            data={"sub": user.id, "email": user.email, "role": user.role}
        )
        refresh_token = create_refresh_token(
            data={"sub": user.id, "email": user.email}
        )
        
        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )
        
    except AuthenticationException as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=e.detail)


@router.post("/refresh", response_model=Token)
async def refresh_token(
    token_data: TokenRefresh,
    auth_service: AuthService = Depends(get_auth_service),
) -> Any:
    """Refresh access token using refresh token."""
    try:
        # Verify refresh token
        token_payload = verify_token(token_data.refresh_token, token_type="refresh")
        
        # Get user
        user = await auth_service.get_user_by_id(token_payload.user_id)
        if not user:
            raise AuthenticationException("User not found")
        
        # Generate new tokens
        access_token = create_access_token(
            data={"sub": user.id, "email": user.email, "role": user.role}
        )
        refresh_token = create_refresh_token(
            data={"sub": user.id, "email": user.email}
        )
        
        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )
        
    except AuthenticationException as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=e.detail)


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: UserResponse = Depends(get_current_user),
) -> Any:
    """Get current user profile."""
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_current_user_profile(
    user_update: UserUpdate,
    current_user: UserResponse = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
) -> Any:
    """Update current user profile."""
    try:
        # Check if username is already taken (if being updated)
        if user_update.username and user_update.username != current_user.username:
            existing_user = await user_service.get_user_by_username(user_update.username)
            if existing_user:
                raise ConflictException("Username already taken")
        
        updated_user = await user_service.update_user(current_user.id, user_update)
        return updated_user
        
    except ConflictException as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=e.detail)
    except ValidationException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.detail)


@router.post("/change-password", status_code=status.HTTP_200_OK)
async def change_password(
    password_data: PasswordChange,
    current_user: UserResponse = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service),
) -> Any:
    """Change user password."""
    try:
        # Verify current password
        user = await auth_service.get_user_by_id(current_user.id)
        if not verify_password(password_data.current_password, user.password_hash):
            raise AuthenticationException("Current password is incorrect")
        
        # Update password
        await auth_service.update_password(current_user.id, password_data.new_password)
        
        return {"message": "Password updated successfully"}
        
    except AuthenticationException as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=e.detail)


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(
    current_user: UserResponse = Depends(get_current_user),
) -> Any:
    """Logout user (client should discard tokens)."""
    # In a more sophisticated implementation, you might maintain a token blacklist
    return {"message": "Logged out successfully"}


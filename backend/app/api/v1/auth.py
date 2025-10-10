"""
Authentication API endpoints.
Handles user registration, login, token refresh, and logout.
"""
from datetime import datetime, timedelta
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from uuid import UUID
import secrets

from app.core.database import get_db
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token
)
from app.core.config import settings
from app.core.rate_limit import limiter
from app.models.user import User
from app.models.email_verification_token import EmailVerificationToken
from app.schemas.auth import (
    UserRegister,
    UserLogin,
    LoginResponse,
    RefreshTokenRequest,
    TokenResponse,
    UserResponse,
    MessageResponse,
    ErrorResponse
)
from app.api.dependencies import get_current_user, verify_refresh_token
from app.services.email import email_service


router = APIRouter()


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    responses={
        201: {"description": "User successfully registered"},
        400: {"model": ErrorResponse, "description": "Email already registered"},
        429: {"model": ErrorResponse, "description": "Rate limit exceeded"},
    }
)
@limiter.limit("5/hour")  # 5 registrations per hour per IP
async def register(
    request: Request,
    user_data: UserRegister,
    db: Session = Depends(get_db)
) -> Any:
    """
    Register a new user account.
    
    - **email**: Valid email address (unique)
    - **password**: Strong password (min 8 chars, uppercase, lowercase, digit)
    - **full_name**: Optional full name
    
    Returns the created user information (without password).
    A verification email will be sent to the provided email address.
    """
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    hashed_password = hash_password(user_data.password)
    
    new_user = User(
        email=user_data.email,
        password_hash=hashed_password,
        full_name=user_data.full_name,
        is_active=True,
        is_verified=False,  # User needs to verify email
        role="user"
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Create email verification token
    verification_token = secrets.token_urlsafe(32)
    expires_at = datetime.utcnow() + timedelta(hours=24)
    
    email_verification = EmailVerificationToken(
        user_id=new_user.id,
        token=verification_token,
        expires_at=expires_at,
        is_used=False
    )
    
    db.add(email_verification)
    db.commit()
    
    # Send verification email (async, don't wait for completion)
    await email_service.send_verification_email(
        to_email=new_user.email,
        token=verification_token,
        user_name=new_user.full_name
    )
    
    return new_user


@router.post(
    "/login",
    response_model=LoginResponse,
    summary="Login user",
    responses={
        200: {"description": "Successfully authenticated"},
        401: {"model": ErrorResponse, "description": "Invalid credentials"},
        403: {"model": ErrorResponse, "description": "Account inactive"},
        429: {"model": ErrorResponse, "description": "Rate limit exceeded"},
    }
)
@limiter.limit("5/minute")  # 5 login attempts per minute per IP
async def login(
    request: Request,
    login_data: UserLogin,
    db: Session = Depends(get_db)
) -> Any:
    """
    Authenticate user and return access and refresh tokens.
    
    - **email**: User email address
    - **password**: User password
    
    Returns:
    - User information
    - Access token (15 minutes expiry)
    - Refresh token (7 days expiry)
    """
    # Find user by email
    user = db.query(User).filter(User.email == login_data.email).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Verify password
    if not verify_password(login_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive. Please contact support."
        )
    
    # Update last login timestamp
    user.last_login_at = datetime.utcnow()
    db.commit()
    
    # Create tokens
    access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email}
    )
    refresh_token = create_refresh_token(
        data={"sub": str(user.id)}
    )
    
    return {
        "user": user,
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60  # Convert to seconds
    }


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh access token",
    responses={
        200: {"description": "Token successfully refreshed"},
        401: {"model": ErrorResponse, "description": "Invalid refresh token"},
        429: {"model": ErrorResponse, "description": "Rate limit exceeded"},
    }
)
@limiter.limit("10/minute")  # 10 refresh attempts per minute per IP
async def refresh_token(
    request: Request,
    token_data: RefreshTokenRequest,
    db: Session = Depends(get_db)
) -> Any:
    """
    Refresh an expired access token using a valid refresh token.
    
    - **refresh_token**: Valid JWT refresh token
    
    Returns new access and refresh tokens.
    """
    # Verify refresh token
    user_id = verify_refresh_token(token_data.refresh_token)
    
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    # Get user from database
    try:
        user_uuid = UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    user = db.query(User).filter(User.id == user_uuid).first()
    
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    # Create new tokens
    access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email}
    )
    new_refresh_token = create_refresh_token(
        data={"sub": str(user.id)}
    )
    
    return {
        "access_token": access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }


@router.post(
    "/logout",
    response_model=MessageResponse,
    summary="Logout user",
    responses={
        200: {"description": "Successfully logged out"},
    }
)
async def logout(
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Logout current user.
    
    Note: Since we're using stateless JWT tokens, the actual logout
    happens on the client side by removing the tokens from storage.
    This endpoint is provided for consistency and can be extended
    to implement token blacklisting if needed.
    """
    # TODO: Implement token blacklisting with Redis (optional enhancement)
    # For now, client-side logout by removing tokens is sufficient
    
    return {
        "message": "Successfully logged out",
        "detail": "Please remove tokens from client storage"
    }


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user info",
    responses={
        200: {"description": "Current user information"},
        401: {"model": ErrorResponse, "description": "Not authenticated"},
    }
)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get current authenticated user information.
    
    Requires a valid access token in the Authorization header.
    """
    return current_user


@router.get(
    "/verify-token",
    response_model=MessageResponse,
    summary="Verify if access token is valid",
    responses={
        200: {"description": "Token is valid"},
        401: {"model": ErrorResponse, "description": "Token is invalid"},
    }
)
async def verify_access_token(
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Verify if the provided access token is valid.
    
    Useful for checking token validity before making other API calls.
    """
    return {
        "message": "Token is valid",
        "detail": f"User: {current_user.email}"
    }
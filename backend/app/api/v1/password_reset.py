"""
Password reset API endpoints.
Handles password reset requests and confirmations.
"""
from datetime import datetime, timedelta
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
import secrets

from app.core.database import get_db
from app.core.security import hash_password
from app.core.rate_limit import limiter
from app.models.user import User
from app.models.password_reset_token import PasswordResetToken
from app.schemas.auth import (
    PasswordResetRequest,
    PasswordResetConfirm,
    MessageResponse,
    ErrorResponse
)
from app.services.email import email_service


router = APIRouter()


@router.post(
    "/request",
    response_model=MessageResponse,
    summary="Request password reset",
    responses={
        200: {"description": "Password reset email sent"},
        404: {"model": ErrorResponse, "description": "User not found"},
        429: {"model": ErrorResponse, "description": "Rate limit exceeded"},
    }
)
@limiter.limit("3/hour")  # 3 password reset requests per hour per IP
async def request_password_reset(
    request: Request,
    reset_request: PasswordResetRequest,
    db: Session = Depends(get_db)
) -> Any:
    """
    Request a password reset email.
    
    - **email**: User email address
    
    Sends an email with a password reset link (1 hour expiry).
    For security, always returns success even if email doesn't exist.
    """
    # Find user by email
    user = db.query(User).filter(User.email == reset_request.email).first()
    
    # For security, always return success message (don't reveal if email exists)
    if not user:
        return {
            "message": "If an account with that email exists, a password reset link has been sent.",
            "detail": "Please check your email inbox and spam folder."
        }
    
    # Check if user is active
    if not user.is_active:
        return {
            "message": "If an account with that email exists, a password reset link has been sent.",
            "detail": "Please check your email inbox and spam folder."
        }
    
    # Invalidate any existing password reset tokens for this user
    existing_tokens = db.query(PasswordResetToken).filter(
        PasswordResetToken.user_id == user.id,
        PasswordResetToken.is_used == False,
        PasswordResetToken.expires_at > datetime.utcnow()
    ).all()
    
    for token in existing_tokens:
        token.is_used = True
    
    # Generate new reset token
    reset_token = secrets.token_urlsafe(32)
    expires_at = datetime.utcnow() + timedelta(hours=1)
    
    # Create password reset token record
    password_reset = PasswordResetToken(
        user_id=user.id,
        token=reset_token,
        expires_at=expires_at,
        is_used=False
    )
    
    db.add(password_reset)
    db.commit()
    
    # Send password reset email
    email_sent = await email_service.send_password_reset_email(
        to_email=user.email,
        token=reset_token,
        user_name=user.full_name
    )
    
    if not email_sent:
        # Log error but don't expose to user
        # In production, you might want to use a proper logging/monitoring service
        pass
    
    return {
        "message": "If an account with that email exists, a password reset link has been sent.",
        "detail": "Please check your email inbox and spam folder. The link will expire in 1 hour."
    }


@router.post(
    "/confirm",
    response_model=MessageResponse,
    summary="Confirm password reset",
    responses={
        200: {"description": "Password reset successful"},
        400: {"model": ErrorResponse, "description": "Invalid or expired token"},
        429: {"model": ErrorResponse, "description": "Rate limit exceeded"},
    }
)
@limiter.limit("5/hour")  # 5 password reset confirmations per hour per IP
async def confirm_password_reset(
    request: Request,
    reset_confirm: PasswordResetConfirm,
    db: Session = Depends(get_db)
) -> Any:
    """
    Confirm password reset with token and set new password.
    
    - **token**: Password reset token from email
    - **new_password**: New password (min 8 chars, uppercase, lowercase, digit)
    
    Returns success message if password was reset.
    """
    # Find the password reset token
    password_reset = db.query(PasswordResetToken).filter(
        PasswordResetToken.token == reset_confirm.token,
        PasswordResetToken.is_used == False
    ).first()
    
    if not password_reset:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired password reset token"
        )
    
    # Check if token has expired
    if password_reset.expires_at < datetime.utcnow():
        password_reset.is_used = True
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password reset token has expired. Please request a new one."
        )
    
    # Get the user
    user = db.query(User).filter(User.id == password_reset.user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User not found"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    
    # Update user password
    user.password_hash = hash_password(reset_confirm.new_password)
    user.updated_at = datetime.utcnow()
    
    # Mark token as used
    password_reset.is_used = True
    password_reset.used_at = datetime.utcnow()
    
    db.commit()
    
    return {
        "message": "Password has been reset successfully",
        "detail": "You can now log in with your new password"
    }


@router.post(
    "/validate-token/{token}",
    response_model=MessageResponse,
    summary="Validate password reset token",
    responses={
        200: {"description": "Token is valid"},
        400: {"model": ErrorResponse, "description": "Invalid or expired token"},
    }
)
async def validate_reset_token(
    token: str,
    db: Session = Depends(get_db)
) -> Any:
    """
    Validate a password reset token without using it.
    
    Useful for checking token validity before showing the reset form.
    """
    password_reset = db.query(PasswordResetToken).filter(
        PasswordResetToken.token == token,
        PasswordResetToken.is_used == False
    ).first()
    
    if not password_reset:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid password reset token"
        )
    
    if password_reset.expires_at < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password reset token has expired"
        )
    
    return {
        "message": "Token is valid",
        "detail": "You can proceed with password reset"
    }
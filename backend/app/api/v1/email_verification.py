"""
Email verification API endpoints.
Handles email verification and resending verification emails.
"""
from datetime import datetime, timedelta
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
import secrets

from app.core.database import get_db
from app.core.rate_limit import limiter
from app.models.user import User
from app.models.email_verification_token import EmailVerificationToken
from app.schemas.auth import (
    EmailVerificationRequest,
    MessageResponse,
    ErrorResponse
)
from app.api.dependencies import get_current_user
from app.services.email import email_service


router = APIRouter()


@router.post(
    "/verify/{token}",
    response_model=MessageResponse,
    summary="Verify email with token",
    responses={
        200: {"description": "Email verified successfully"},
        400: {"model": ErrorResponse, "description": "Invalid or expired token"},
    }
)
async def verify_email(
    token: str,
    db: Session = Depends(get_db)
) -> Any:
    """
    Verify user email address with token from email.
    
    - **token**: Email verification token from email
    
    Returns success message if email was verified.
    """
    # Find the verification token
    verification_token = db.query(EmailVerificationToken).filter(
        EmailVerificationToken.token == token,
        EmailVerificationToken.is_used == False
    ).first()
    
    if not verification_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired email verification token"
        )
    
    # Check if token has expired
    if verification_token.expires_at < datetime.utcnow():
        verification_token.is_used = True
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email verification token has expired. Please request a new one."
        )
    
    # Get the user
    user = db.query(User).filter(User.id == verification_token.user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User not found"
        )
    
    # Check if already verified
    if user.is_verified:
        return {
            "message": "Email already verified",
            "detail": "Your email address has already been verified"
        }
    
    # Mark user as verified
    user.is_verified = True
    user.updated_at = datetime.utcnow()
    
    # Mark token as used
    verification_token.is_used = True
    verification_token.used_at = datetime.utcnow()
    
    db.commit()
    
    return {
        "message": "Email verified successfully",
        "detail": "Your account is now fully activated"
    }


@router.post(
    "/resend",
    response_model=MessageResponse,
    summary="Resend verification email",
    responses={
        200: {"description": "Verification email sent"},
        400: {"model": ErrorResponse, "description": "Email already verified or user not found"},
        429: {"model": ErrorResponse, "description": "Rate limit exceeded"},
    }
)
@limiter.limit("3/hour")  # 3 resend requests per hour per IP
async def resend_verification_email(
    request: Request,
    email_request: EmailVerificationRequest,
    db: Session = Depends(get_db)
) -> Any:
    """
    Resend email verification email.
    
    - **email**: User email address
    
    Sends a new verification email with a fresh token (24 hour expiry).
    """
    # Find user by email
    user = db.query(User).filter(User.email == email_request.email).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check if already verified
    if user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already verified"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    
    # Invalidate any existing verification tokens for this user
    existing_tokens = db.query(EmailVerificationToken).filter(
        EmailVerificationToken.user_id == user.id,
        EmailVerificationToken.is_used == False,
        EmailVerificationToken.expires_at > datetime.utcnow()
    ).all()
    
    for token in existing_tokens:
        token.is_used = True
    
    # Generate new verification token
    verification_token = secrets.token_urlsafe(32)
    expires_at = datetime.utcnow() + timedelta(hours=24)
    
    # Create verification token record
    email_verification = EmailVerificationToken(
        user_id=user.id,
        token=verification_token,
        expires_at=expires_at,
        is_used=False
    )
    
    db.add(email_verification)
    db.commit()
    
    # Send verification email
    email_sent = await email_service.send_verification_email(
        to_email=user.email,
        token=verification_token,
        user_name=user.full_name
    )
    
    if not email_sent:
        # Log error but don't expose to user
        pass
    
    return {
        "message": "Verification email sent",
        "detail": "Please check your email inbox and spam folder. The link will expire in 24 hours."
    }


@router.post(
    "/resend-authenticated",
    response_model=MessageResponse,
    summary="Resend verification email (authenticated)",
    responses={
        200: {"description": "Verification email sent"},
        400: {"model": ErrorResponse, "description": "Email already verified"},
        401: {"model": ErrorResponse, "description": "Not authenticated"},
        429: {"model": ErrorResponse, "description": "Rate limit exceeded"},
    }
)
@limiter.limit("3/hour")  # 3 resend requests per hour per IP
async def resend_verification_email_authenticated(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Resend email verification email for currently authenticated user.
    
    This endpoint is for users who are logged in but haven't verified their email yet.
    """
    # Check if already verified
    if current_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already verified"
        )
    
    # Invalidate any existing verification tokens for this user
    existing_tokens = db.query(EmailVerificationToken).filter(
        EmailVerificationToken.user_id == current_user.id,
        EmailVerificationToken.is_used == False,
        EmailVerificationToken.expires_at > datetime.utcnow()
    ).all()
    
    for token in existing_tokens:
        token.is_used = True
    
    # Generate new verification token
    verification_token = secrets.token_urlsafe(32)
    expires_at = datetime.utcnow() + timedelta(hours=24)
    
    # Create verification token record
    email_verification = EmailVerificationToken(
        user_id=current_user.id,
        token=verification_token,
        expires_at=expires_at,
        is_used=False
    )
    
    db.add(email_verification)
    db.commit()
    
    # Send verification email
    email_sent = await email_service.send_verification_email(
        to_email=current_user.email,
        token=verification_token,
        user_name=current_user.full_name
    )
    
    if not email_sent:
        # Log error but don't expose to user
        pass
    
    return {
        "message": "Verification email sent",
        "detail": "Please check your email inbox and spam folder. The link will expire in 24 hours."
    }


@router.get(
    "/validate-token/{token}",
    response_model=MessageResponse,
    summary="Validate email verification token",
    responses={
        200: {"description": "Token is valid"},
        400: {"model": ErrorResponse, "description": "Invalid or expired token"},
    }
)
async def validate_verification_token(
    token: str,
    db: Session = Depends(get_db)
) -> Any:
    """
    Validate an email verification token without using it.
    
    Useful for checking token validity before showing the verification confirmation.
    """
    verification_token = db.query(EmailVerificationToken).filter(
        EmailVerificationToken.token == token,
        EmailVerificationToken.is_used == False
    ).first()
    
    if not verification_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid email verification token"
        )
    
    if verification_token.expires_at < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email verification token has expired"
        )
    
    return {
        "message": "Token is valid",
        "detail": "You can proceed with email verification"
    }
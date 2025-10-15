"""
Contact form API endpoint.
"""
from fastapi import APIRouter, HTTPException, status, Request
from pydantic import BaseModel, EmailStr, Field
from app.core.rate_limit import limiter
from app.services.email import email_service

router = APIRouter(prefix="/contact", tags=["Contact"])


class ContactMessage(BaseModel):
    """Contact form submission schema."""
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    subject: str = Field(..., min_length=5, max_length=200)
    message: str = Field(..., min_length=20, max_length=2000)


@router.post("/send")
@limiter.limit("3/hour")  # Prevent spam
async def send_contact_message(
    request: Request,
    data: ContactMessage
):
    """
    Send a contact form message via email.
    Rate limited to 3 messages per hour per IP.
    """
    try:
        # Send email to support
        await email_service.send_contact_form_email(
            from_name=data.name,
            from_email=data.email,
            subject=data.subject,
            message=data.message
        )
        
        return {
            "message": "Message sent successfully",
            "detail": "We'll get back to you within 24 hours"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send message: {str(e)}"
        )
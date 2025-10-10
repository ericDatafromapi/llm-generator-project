"""
Email service for sending verification and password reset emails.
Uses SendGrid for email delivery.
"""
import logging
from typing import Optional
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content
import os

from app.core.config import settings


logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending emails via SendGrid."""
    
    def __init__(self):
        """Initialize SendGrid client."""
        self.api_key = settings.SENDGRID_API_KEY
        self.from_email = settings.FROM_EMAIL
        self.client = None
        
        if self.api_key and self.api_key != "":
            try:
                self.client = SendGridAPIClient(self.api_key)
            except Exception as e:
                logger.error(f"Failed to initialize SendGrid client: {e}")
    
    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None
    ) -> bool:
        """
        Send an email via SendGrid.
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML content of the email
            text_content: Plain text content (optional)
            
        Returns:
            True if email sent successfully, False otherwise
        """
        if not self.client:
            logger.warning(f"SendGrid not configured. Would send email to {to_email} with subject: {subject}")
            logger.debug(f"Email content: {html_content}")
            return True  # Return True in development/testing
        
        try:
            message = Mail(
                from_email=Email(self.from_email),
                to_emails=To(to_email),
                subject=subject,
                html_content=Content("text/html", html_content)
            )
            
            if text_content:
                message.content = [
                    Content("text/plain", text_content),
                    Content("text/html", html_content)
                ]
            
            response = self.client.send(message)
            
            if response.status_code in [200, 201, 202]:
                logger.info(f"Email sent successfully to {to_email}")
                return True
            else:
                logger.error(f"Failed to send email to {to_email}. Status: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending email to {to_email}: {e}")
            return False
    
    async def send_verification_email(self, to_email: str, token: str, user_name: Optional[str] = None) -> bool:
        """
        Send email verification email.
        
        Args:
            to_email: Recipient email address
            token: Verification token
            user_name: User's name (optional)
            
        Returns:
            True if email sent successfully, False otherwise
        """
        verification_url = f"{settings.FRONTEND_URL}/verify-email/{token}"
        
        name_greeting = f"Hi {user_name}," if user_name else "Hi there,"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
                <h1 style="color: white; margin: 0;">Welcome to LLMReady!</h1>
            </div>
            
            <div style="background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px;">
                <p style="font-size: 16px;">{name_greeting}</p>
                
                <p style="font-size: 16px;">Thank you for registering with LLMReady! To complete your registration and start optimizing your content for AI, please verify your email address.</p>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{verification_url}" 
                       style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                              color: white; 
                              padding: 15px 40px; 
                              text-decoration: none; 
                              border-radius: 5px; 
                              font-weight: bold;
                              display: inline-block;">
                        Verify Email Address
                    </a>
                </div>
                
                <p style="font-size: 14px; color: #666;">Or copy and paste this link into your browser:</p>
                <p style="font-size: 14px; word-break: break-all; background: #fff; padding: 10px; border-radius: 5px;">
                    {verification_url}
                </p>
                
                <p style="font-size: 14px; color: #666; margin-top: 30px;">
                    This verification link will expire in 24 hours for security reasons.
                </p>
                
                <p style="font-size: 14px; color: #666;">
                    If you didn't create an account with LLMReady, you can safely ignore this email.
                </p>
            </div>
            
            <div style="text-align: center; margin-top: 20px; color: #999; font-size: 12px;">
                <p>© 2025 LLMReady. All rights reserved.</p>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        {name_greeting}
        
        Thank you for registering with LLMReady! To complete your registration, please verify your email address by clicking the link below:
        
        {verification_url}
        
        This verification link will expire in 24 hours for security reasons.
        
        If you didn't create an account with LLMReady, you can safely ignore this email.
        
        Best regards,
        The LLMReady Team
        """
        
        return await self.send_email(
            to_email=to_email,
            subject="Verify your LLMReady account",
            html_content=html_content,
            text_content=text_content
        )
    
    async def send_password_reset_email(self, to_email: str, token: str, user_name: Optional[str] = None) -> bool:
        """
        Send password reset email.
        
        Args:
            to_email: Recipient email address
            token: Password reset token
            user_name: User's name (optional)
            
        Returns:
            True if email sent successfully, False otherwise
        """
        reset_url = f"{settings.FRONTEND_URL}/reset-password/{token}"
        
        name_greeting = f"Hi {user_name}," if user_name else "Hi there,"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
                <h1 style="color: white; margin: 0;">Password Reset Request</h1>
            </div>
            
            <div style="background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px;">
                <p style="font-size: 16px;">{name_greeting}</p>
                
                <p style="font-size: 16px;">We received a request to reset your password for your LLMReady account. Click the button below to create a new password:</p>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{reset_url}" 
                       style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                              color: white; 
                              padding: 15px 40px; 
                              text-decoration: none; 
                              border-radius: 5px; 
                              font-weight: bold;
                              display: inline-block;">
                        Reset Password
                    </a>
                </div>
                
                <p style="font-size: 14px; color: #666;">Or copy and paste this link into your browser:</p>
                <p style="font-size: 14px; word-break: break-all; background: #fff; padding: 10px; border-radius: 5px;">
                    {reset_url}
                </p>
                
                <p style="font-size: 14px; color: #666; margin-top: 30px;">
                    This password reset link will expire in 1 hour for security reasons.
                </p>
                
                <p style="font-size: 14px; color: #e74c3c; font-weight: bold;">
                    If you didn't request a password reset, please ignore this email or contact support if you're concerned about your account security.
                </p>
            </div>
            
            <div style="text-align: center; margin-top: 20px; color: #999; font-size: 12px;">
                <p>© 2025 LLMReady. All rights reserved.</p>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        {name_greeting}
        
        We received a request to reset your password for your LLMReady account. Click the link below to create a new password:
        
        {reset_url}
        
        This password reset link will expire in 1 hour for security reasons.
        
        If you didn't request a password reset, please ignore this email or contact support if you're concerned about your account security.
        
        Best regards,
        The LLMReady Team
        """
        
        return await self.send_email(
            to_email=to_email,
            subject="Reset your LLMReady password",
            html_content=html_content,
            text_content=text_content
        )
    
    async def send_generation_complete_email(self, to_email: str, generation_id: str, user_name: Optional[str] = None) -> bool:
        """
        Send notification when content generation is complete.
        
        Args:
            to_email: Recipient email address
            generation_id: ID of the completed generation
            user_name: User's name (optional)
            
        Returns:
            True if email sent successfully, False otherwise
        """
        download_url = f"{settings.FRONTEND_URL}/dashboard/generations/{generation_id}"
        
        name_greeting = f"Hi {user_name}," if user_name else "Hi there,"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
                <h1 style="color: white; margin: 0;">✅ Content Generation Complete!</h1>
            </div>
            
            <div style="background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px;">
                <p style="font-size: 16px;">{name_greeting}</p>
                
                <p style="font-size: 16px;">Great news! Your LLM-optimized content is ready for download.</p>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{download_url}" 
                       style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                              color: white; 
                              padding: 15px 40px; 
                              text-decoration: none; 
                              border-radius: 5px; 
                              font-weight: bold;
                              display: inline-block;">
                        Download Your Files
                    </a>
                </div>
                
                <p style="font-size: 14px; color: #666;">
                    Your files will be available for download for the next 7 days.
                </p>
            </div>
            
            <div style="text-align: center; margin-top: 20px; color: #999; font-size: 12px;">
                <p>© 2025 LLMReady. All rights reserved.</p>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        {name_greeting}
        
        Great news! Your LLM-optimized content is ready for download.
        
        Download your files here: {download_url}
        
        Your files will be available for download for the next 7 days.
        
        Best regards,
        The LLMReady Team
        """
        
        return await self.send_email(
            to_email=to_email,
            subject="Your LLMReady content is ready! 🎉",
            html_content=html_content,
            text_content=text_content
        )


# Global email service instance
email_service = EmailService()
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
            # Create message without html_content initially
            message = Mail(
                from_email=Email(self.from_email),
                to_emails=To(to_email),
                subject=subject
            )
            
            # Set content properly - either both text and html, or just html
            if text_content:
                message.content = [
                    Content("text/plain", text_content),
                    Content("text/html", html_content)
                ]
            else:
                message.content = Content("text/html", html_content)
            
            response = self.client.send(message)
            
            if response.status_code in [200, 201, 202]:
                logger.info(f"Email sent successfully to {to_email}")
                return True
            else:
                logger.error(f"Failed to send email to {to_email}. Status: {response.status_code}, Body: {response.body}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending email to {to_email}: {e}")
            # Log more detailed error information
            if hasattr(e, 'body'):
                logger.error(f"SendGrid error details: {e.body}")
            if hasattr(e, 'to_dict'):
                logger.error(f"SendGrid error dict: {e.to_dict}")
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


    async def send_generation_failed_email(self, to_email: str, user_name: Optional[str] = None, error_message: str = "") -> bool:
        """
        Send notification when content generation fails.
        
        Args:
            to_email: Recipient email address
            user_name: User's name (optional)
            error_message: Error message (optional)
            
        Returns:
            True if email sent successfully, False otherwise
        """
        dashboard_url = f"{settings.FRONTEND_URL}/dashboard"
        
        name_greeting = f"Hi {user_name}," if user_name else "Hi there,"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #e74c3c 0%, #c0392b 100%); padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
                <h1 style="color: white; margin: 0;">⚠️ Content Generation Failed</h1>
            </div>
            
            <div style="background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px;">
                <p style="font-size: 16px;">{name_greeting}</p>
                
                <p style="font-size: 16px;">Unfortunately, your content generation encountered an error and couldn't be completed.</p>
                
                {f'<p style="font-size: 14px; color: #666; background: #fff; padding: 10px; border-left: 3px solid #e74c3c; border-radius: 3px;"><strong>Error:</strong> {error_message}</p>' if error_message else ''}
                
                <p style="font-size: 14px; color: #666;">
                    Don't worry - this hasn't counted against your usage quota. You can try again from your dashboard.
                </p>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{dashboard_url}"
                       style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                              color: white;
                              padding: 15px 40px;
                              text-decoration: none;
                              border-radius: 5px;
                              font-weight: bold;
                              display: inline-block;">
                        Go to Dashboard
                    </a>
                </div>
                
                <p style="font-size: 14px; color: #666;">
                    If this problem persists, please contact our support team.
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
        
        Unfortunately, your content generation encountered an error and couldn't be completed.
        
        {f'Error: {error_message}' if error_message else ''}
        
        Don't worry - this hasn't counted against your usage quota. You can try again from your dashboard: {dashboard_url}
        
        If this problem persists, please contact our support team.
        
        Best regards,
        The LLMReady Team
        """
        
        return await self.send_email(
            to_email=to_email,
            subject="Generation failed - LLMReady",
            html_content=html_content,
            text_content=text_content
        )


# Global email service instance
email_service = EmailService()


# Synchronous wrapper functions for Celery tasks
def send_generation_complete_email(to_email: str, user_name: str, website_name: str, generation_id: str) -> bool:
    """
    Synchronous wrapper for sending generation complete email.
    Used by Celery tasks which don't support async.
    """
    import asyncio
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(
        email_service.send_generation_complete_email(to_email, generation_id, user_name)
    )


def send_generation_failed_email(to_email: str, user_name: str, error_message: str) -> bool:
    """
    Synchronous wrapper for sending generation failed email.
    Used by Celery tasks which don't support async.
    """
    import asyncio
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(
        email_service.send_generation_failed_email(to_email, user_name, error_message)
    )


def increment_generation_usage(db: any, user_id: any) -> None:
    """
    Helper function to increment generation usage.
    Used by Celery tasks.
    """
    from app.services.subscription import SubscriptionService
    service = SubscriptionService(db)
    service.increment_usage(user_id)


# Stripe-related email functions
async def send_payment_success_email_async(to_email: str, amount_paid: float, user_name: Optional[str] = None) -> bool:
    """Send payment success confirmation email."""
    name_greeting = f"Hi {user_name}," if user_name else "Hi there,"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="background: linear-gradient(135deg, #10b981 0%, #059669 100%); padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
            <h1 style="color: white; margin: 0;">✅ Payment Successful!</h1>
        </div>
        
        <div style="background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px;">
            <p style="font-size: 16px;">{name_greeting}</p>
            
            <p style="font-size: 16px;">Thank you for your payment! Your subscription is now active.</p>
            
            <div style="background: #fff; padding: 20px; border-radius: 5px; margin: 20px 0;">
                <p style="margin: 0; font-size: 14px; color: #666;">Amount Paid</p>
                <p style="margin: 5px 0 0 0; font-size: 24px; font-weight: bold; color: #10b981;">€{amount_paid:.2f}</p>
            </div>
            
            <p style="font-size: 14px; color: #666;">
                Your subscription will automatically renew at the end of your billing period.
            </p>
            
            <div style="text-align: center; margin: 30px 0;">
                <a href="{settings.FRONTEND_URL}/dashboard"
                   style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                          color: white;
                          padding: 15px 40px;
                          text-decoration: none;
                          border-radius: 5px;
                          font-weight: bold;
                          display: inline-block;">
                    Go to Dashboard
                </a>
            </div>
        </div>
        
        <div style="text-align: center; margin-top: 20px; color: #999; font-size: 12px;">
            <p>© 2025 LLMReady. All rights reserved.</p>
        </div>
    </body>
    </html>
    """
    
    text_content = f"""
    {name_greeting}
    
    Thank you for your payment! Your subscription is now active.
    
    Amount Paid: €{amount_paid:.2f}
    
    Your subscription will automatically renew at the end of your billing period.
    
    Dashboard: {settings.FRONTEND_URL}/dashboard
    
    Best regards,
    The LLMReady Team
    """
    
    return await email_service.send_email(
        to_email=to_email,
        subject="Payment successful - LLMReady",
        html_content=html_content,
        text_content=text_content
    )


async def send_payment_failed_email_async(to_email: str, user_name: Optional[str] = None) -> bool:
    """Send payment failure notification email."""
    name_greeting = f"Hi {user_name}," if user_name else "Hi there,"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%); padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
            <h1 style="color: white; margin: 0;">⚠️ Payment Failed</h1>
        </div>
        
        <div style="background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px;">
            <p style="font-size: 16px;">{name_greeting}</p>
            
            <p style="font-size: 16px;">We were unable to process your payment. This may be due to:</p>
            
            <ul style="font-size: 14px; color: #666;">
                <li>Insufficient funds</li>
                <li>Expired card</li>
                <li>Incorrect card details</li>
                <li>Bank decline</li>
            </ul>
            
            <p style="font-size: 14px; color: #666;">
                Your subscription will remain active for a grace period of 3 days. Please update your payment method to avoid service interruption.
            </p>
            
            <div style="text-align: center; margin: 30px 0;">
                <a href="{settings.FRONTEND_URL}/dashboard?action=update_payment"
                   style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                          color: white;
                          padding: 15px 40px;
                          text-decoration: none;
                          border-radius: 5px;
                          font-weight: bold;
                          display: inline-block;">
                    Update Payment Method
                </a>
            </div>
        </div>
        
        <div style="text-align: center; margin-top: 20px; color: #999; font-size: 12px;">
            <p>© 2025 LLMReady. All rights reserved.</p>
        </div>
    </body>
    </html>
    """
    
    text_content = f"""
    {name_greeting}
    
    We were unable to process your payment. This may be due to insufficient funds, an expired card, incorrect card details, or a bank decline.
    
    Your subscription will remain active for a grace period of 3 days. Please update your payment method to avoid service interruption.
    
    Update Payment Method: {settings.FRONTEND_URL}/dashboard?action=update_payment
    
    Best regards,
    The LLMReady Team
    """
    
    return await email_service.send_email(
        to_email=to_email,
        subject="Action required: Payment failed - LLMReady",
        html_content=html_content,
        text_content=text_content
    )


async def send_chargeback_email_async(to_email: str, user_name: Optional[str] = None) -> bool:
    """Send chargeback notification email."""
    name_greeting = f"Hi {user_name}," if user_name else "Hi there,"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="background: linear-gradient(135deg, #e74c3c 0%, #c0392b 100%); padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
            <h1 style="color: white; margin: 0;">⚠️ Chargeback Received</h1>
        </div>
        
        <div style="background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px;">
            <p style="font-size: 16px;">{name_greeting}</p>
            
            <p style="font-size: 16px;">We've received a chargeback for your payment. Your subscription has been canceled and your account has been downgraded to the free plan.</p>
            
            <p style="font-size: 14px; color: #666;">
                If you believe this was done in error, please contact our support team immediately.
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
    
    We've received a chargeback for your payment. Your subscription has been canceled and your account has been downgraded to the free plan.
    
    If you believe this was done in error, please contact our support team immediately.
    
    Best regards,
    The LLMReady Team
    """
    
    return await email_service.send_email(
        to_email=to_email,
        subject="Chargeback received - LLMReady",
        html_content=html_content,
        text_content=text_content
    )


async def send_refund_email_async(to_email: str, amount_refunded: float, user_name: Optional[str] = None) -> bool:
    """Send refund confirmation email."""
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
            <h1 style="color: white; margin: 0;">💰 Refund Processed</h1>
        </div>
        
        <div style="background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px;">
            <p style="font-size: 16px;">{name_greeting}</p>
            
            <p style="font-size: 16px;">A refund has been processed for your subscription.</p>
            
            <div style="background: #fff; padding: 20px; border-radius: 5px; margin: 20px 0;">
                <p style="margin: 0; font-size: 14px; color: #666;">Refund Amount</p>
                <p style="margin: 5px 0 0 0; font-size: 24px; font-weight: bold; color: #667eea;">€{amount_refunded:.2f}</p>
            </div>
            
            <p style="font-size: 14px; color: #666;">
                The refund should appear in your account within 5-10 business days, depending on your bank. Your subscription has been canceled and your account has been downgraded to the free plan.
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
    
    A refund has been processed for your subscription.
    
    Refund Amount: €{amount_refunded:.2f}
    
    The refund should appear in your account within 5-10 business days, depending on your bank. Your subscription has been canceled and your account has been downgraded to the free plan.
    
    Best regards,
    The LLMReady Team
    """
    
    return await email_service.send_email(
        to_email=to_email,
        subject="Refund processed - LLMReady",
        html_content=html_content,
        text_content=text_content
    )


async def send_payment_action_required_email_async(to_email: str, hosted_invoice_url: str, user_name: Optional[str] = None) -> bool:
    """Send payment action required email (3D Secure)."""
    name_greeting = f"Hi {user_name}," if user_name else "Hi there,"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%); padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
            <h1 style="color: white; margin: 0;">🔐 Authentication Required</h1>
        </div>
        
        <div style="background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px;">
            <p style="font-size: 16px;">{name_greeting}</p>
            
            <p style="font-size: 16px;">Your bank requires additional authentication to complete your payment (3D Secure).</p>
            
            <p style="font-size: 14px; color: #666;">
                Please complete the authentication process to activate your subscription.
            </p>
            
            <div style="text-align: center; margin: 30px 0;">
                <a href="{hosted_invoice_url}"
                   style="background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
                          color: white;
                          padding: 15px 40px;
                          text-decoration: none;
                          border-radius: 5px;
                          font-weight: bold;
                          display: inline-block;">
                    Complete Authentication
                </a>
            </div>
        </div>
        
        <div style="text-align: center; margin-top: 20px; color: #999; font-size: 12px;">
            <p>© 2025 LLMReady. All rights reserved.</p>
        </div>
    </body>
    </html>
    """
    
    text_content = f"""
    {name_greeting}
    
    Your bank requires additional authentication to complete your payment (3D Secure).
    
    Please complete the authentication process to activate your subscription: {hosted_invoice_url}
    
    Best regards,
    The LLMReady Team
    """
    
    return await email_service.send_email(
        to_email=to_email,
        subject="Authentication required for payment - LLMReady",
        html_content=html_content,
        text_content=text_content
    )


async def send_subscription_canceled_email_async(to_email: str, user_name: Optional[str] = None) -> bool:
    """Send subscription cancellation confirmation email."""
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
            <h1 style="color: white; margin: 0;">Subscription Canceled</h1>
        </div>
        
        <div style="background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px;">
            <p style="font-size: 16px;">{name_greeting}</p>
            
            <p style="font-size: 16px;">Your subscription has been canceled. Your account has been downgraded to the free plan.</p>
            
            <p style="font-size: 14px; color: #666;">
                We're sorry to see you go! You can resubscribe at any time from your dashboard.
            </p>
            
            <div style="text-align: center; margin: 30px 0;">
                <a href="{settings.FRONTEND_URL}/pricing"
                   style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                          color: white;
                          padding: 15px 40px;
                          text-decoration: none;
                          border-radius: 5px;
                          font-weight: bold;
                          display: inline-block;">
                    View Plans
                </a>
            </div>
        </div>
        
        <div style="text-align: center; margin-top: 20px; color: #999; font-size: 12px;">
            <p>© 2025 LLMReady. All rights reserved.</p>
        </div>
    </body>
    </html>
    """
    
    text_content = f"""
    {name_greeting}
    
    Your subscription has been canceled. Your account has been downgraded to the free plan.
    
    We're sorry to see you go! You can resubscribe at any time from your dashboard.
    
    View Plans: {settings.FRONTEND_URL}/pricing
    
    Best regards,
    The LLMReady Team
    """
    
    return await email_service.send_email(
        to_email=to_email,
        subject="Subscription canceled - LLMReady",
        html_content=html_content,
        text_content=text_content
    )


# Synchronous wrappers for Celery/webhook handlers
def send_payment_success_email(to_email: str, amount_paid: float, user_name: Optional[str] = None) -> bool:
    """Synchronous wrapper for payment success email."""
    import asyncio
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(
        send_payment_success_email_async(to_email, amount_paid, user_name)
    )


def send_payment_failed_email(to_email: str, user_name: Optional[str] = None) -> bool:
    """Synchronous wrapper for payment failed email."""
    import asyncio
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(
        send_payment_failed_email_async(to_email, user_name)
    )


def send_chargeback_email(to_email: str, user_name: Optional[str] = None) -> bool:
    """Synchronous wrapper for chargeback email."""
    import asyncio
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(
        send_chargeback_email_async(to_email, user_name)
    )


def send_refund_email(to_email: str, amount_refunded: float, user_name: Optional[str] = None) -> bool:
    """Synchronous wrapper for refund email."""
    import asyncio
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(
        send_refund_email_async(to_email, amount_refunded, user_name)
    )


def send_payment_action_required_email(to_email: str, hosted_invoice_url: str, user_name: Optional[str] = None) -> bool:
    """Synchronous wrapper for payment action required email."""
    import asyncio
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(
        send_payment_action_required_email_async(to_email, hosted_invoice_url, user_name)
    )


def send_subscription_canceled_email(to_email: str, user_name: Optional[str] = None) -> bool:
    """Synchronous wrapper for subscription canceled email."""
    import asyncio
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(
        send_subscription_canceled_email_async(to_email, user_name)
    )
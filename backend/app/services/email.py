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
    async def send_cooling_off_refund_email(
        self,
        to_email: str,
        user_name: str,
        refund_amount: float,
        usage_charge: float,
        generations_used: int
    ) -> bool:
        """
        Send email confirmation for EU cooling-off period refund.
        
        Args:
            to_email: Recipient email
            user_name: User's name
            refund_amount: Amount being refunded
            usage_charge: Amount charged for usage
            generations_used: Number of generations created
        
        Returns:
            True if email sent successfully
        """
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
                <h1 style="color: white; margin: 0;">💰 14-Day Refund Processed</h1>
            </div>
            
            <div style="background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px;">
                <p style="font-size: 16px;">{name_greeting}</p>
                
                <p style="font-size: 16px;">We've processed your subscription cancellation within the 14-day cooling-off period as per EU regulations.</p>
                
                <div style="background: #fff; padding: 20px; border-radius: 8px; margin: 20px 0; border: 1px solid #e5e7eb;">
                    <h3 style="margin-top: 0; color: #667eea;">Refund Breakdown</h3>
                    <table style="width: 100%; border-collapse: collapse;">
                        <tr style="border-bottom: 1px solid #e5e7eb;">
                            <td style="padding: 12px 0; color: #666;">Generations Created:</td>
                            <td style="padding: 12px 0; text-align: right; font-weight: bold;">
                                {generations_used}
                            </td>
                        </tr>
                        <tr style="border-bottom: 1px solid #e5e7eb;">
                            <td style="padding: 12px 0; color: #666;">Usage Charge:</td>
                            <td style="padding: 12px 0; text-align: right; font-weight: bold; color: #e74c3c;">
                                -€{usage_charge:.2f}
                            </td>
                        </tr>
                        <tr>
                            <td style="padding: 16px 0 0 0; font-size: 18px; font-weight: bold;">Refund Amount:</td>
                            <td style="padding: 16px 0 0 0; text-align: right; font-weight: bold; font-size: 20px; color: #10b981;">
                                €{refund_amount:.2f}
                            </td>
                        </tr>
                    </table>
                </div>
                
                <div style="background: #eff6ff; padding: 15px; border-radius: 5px; border-left: 4px solid #3b82f6; margin: 20px 0;">
                    <p style="margin: 0; font-size: 14px; color: #1e40af;">
                        <strong>Refund Timeline:</strong> 5-10 business days to your original payment method
                    </p>
                </div>
                
                <p style="font-size: 14px; color: #666;">
                    Your account has been downgraded to the <strong>Free plan</strong>. You can still:
                </p>
                <ul style="font-size: 14px; color: #666;">
                    <li>Create 1 website</li>
                    <li>Generate 1 llms.txt file per month</li>
                    <li>Access all your existing data</li>
                </ul>
                
                <p style="font-size: 14px; color: #666;">
                    We'd love to hear why you're leaving. Your feedback helps us improve!
                </p>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{settings.FRONTEND_URL}/dashboard"
                       style="background: #f3f4f6;
                              color: #667eea;
                              padding: 12px 30px;
                              text-decoration: none;
                              border-radius: 5px;
                              font-weight: bold;
                              display: inline-block;
                              border: 2px solid #667eea;">
                        Go to Dashboard
                    </a>
                </div>
                
                <p style="font-size: 12px; color: #999; margin-top: 30px; padding-top: 20px; border-top: 1px solid #e5e7eb;">
                    <strong>EU Consumer Rights:</strong> This refund was processed under EU Consumer Rights Directive (2011/83/EU) - 14-day cooling-off period.
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
        
        We've processed your subscription cancellation within the 14-day cooling-off period as per EU regulations.
        
        REFUND BREAKDOWN:
        ------------------
        Generations Created: {generations_used}
        Usage Charge: -€{usage_charge:.2f}
        Refund Amount: €{refund_amount:.2f}
        
        Refund Timeline: 5-10 business days to your original payment method
        
        Your account has been downgraded to the Free plan. You can still:
        - Create 1 website
        - Generate 1 llms.txt file per month
        - Access all your existing data
        
        We'd love to hear why you're leaving. Your feedback helps us improve!
        
        Dashboard: {settings.FRONTEND_URL}/dashboard
        
        EU Consumer Rights: This refund was processed under EU Consumer Rights Directive (2011/83/EU) - 14-day cooling-off period.
        
        Best regards,
        The LLMReady Team
        """
        
        return await self.send_email(
            to_email=to_email,
            subject="Refund Processed - 14-Day Cooling-Off Period",
            html_content=html_content,
            text_content=text_content
        )

    async def send_contact_form_email(
        self,
        from_name: str,
        from_email: str,
        subject: str,
        message: str
    ) -> bool:
        """
        Send contact form submission to support email.
        
        Args:
            from_name: Name of person submitting form
            from_email: Email of person submitting form
            subject: Subject line from form
            message: Message content from form
            
        Returns:
            True if email sent successfully, False otherwise
        """
        # Send to support email (FROM_EMAIL or a dedicated support email)
        support_email = self.from_email  # Or settings.SUPPORT_EMAIL if you add one
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
                <h1 style="color: white; margin: 0;">📧 New Contact Form Submission</h1>
            </div>
            
            <div style="background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px;">
                <div style="background: #fff; padding: 20px; border-radius: 5px; margin-bottom: 20px;">
                    <p style="margin: 0; font-size: 14px; color: #666;">From</p>
                    <p style="margin: 5px 0 0 0; font-size: 16px; font-weight: bold;">{from_name}</p>
                    <p style="margin: 5px 0 0 0; font-size: 14px; color: #667eea;">{from_email}</p>
                </div>
                
                <div style="background: #fff; padding: 20px; border-radius: 5px; margin-bottom: 20px;">
                    <p style="margin: 0; font-size: 14px; color: #666;">Subject</p>
                    <p style="margin: 5px 0 0 0; font-size: 16px; font-weight: bold;">{subject}</p>
                </div>
                
                <div style="background: #fff; padding: 20px; border-radius: 5px;">
                    <p style="margin: 0; font-size: 14px; color: #666;">Message</p>
                    <p style="margin: 10px 0 0 0; font-size: 14px; white-space: pre-wrap;">{message}</p>
                </div>
                
                <p style="font-size: 12px; color: #999; margin-top: 20px; text-align: center;">
                    Reply to this person at: {from_email}
                </p>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        New Contact Form Submission
        
        From: {from_name}
        Email: {from_email}
        Subject: {subject}
        
        Message:
        {message}
        
        ---
        Reply to: {from_email}
        """
        
        return await self.send_email(
            to_email=support_email,
            subject=f"Contact Form: {subject}",
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



async def send_subscription_payment_email_async(
    to_email: str,
    user_name: Optional[str],
    plan_name: str,
    amount_paid: float,
    billing_interval: str,
    next_billing_date: str,
    features: list
) -> bool:
    """
    Send detailed payment confirmation with subscription info.
    
    Args:
        to_email: Recipient email
        user_name: User's name
        plan_name: Plan name (Starter, Standard, Pro)
        amount_paid: Amount charged
        billing_interval: monthly or yearly
        next_billing_date: Date of next renewal
        features: List of plan features
    """
    name_greeting = f"Hi {user_name}," if user_name else "Hi there,"
    
    features_html = "".join([
        f'<li style="padding: 5px 0;">{feature}</li>'
        for feature in features
    ])
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="background: linear-gradient(135deg, #10b981 0%, #059669 100%); padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
            <h1 style="color: white; margin: 0;">🎉 Payment Successful!</h1>
        </div>
        
        <div style="background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px;">
            <p style="font-size: 16px;">{name_greeting}</p>
            
            <p style="font-size: 16px;">Thank you for your payment! Your <strong>{plan_name}</strong> subscription is now active.</p>
            
            <!-- Payment Summary -->
            <div style="background: #fff; padding: 25px; border-radius: 8px; margin: 25px 0; border: 2px solid #10b981;">
                <h3 style="margin-top: 0; color: #667eea; font-size: 18px;">Payment Summary</h3>
                <table style="width: 100%; border-collapse: collapse;">
                    <tr style="border-bottom: 1px solid #e5e7eb;">
                        <td style="padding: 12px 0; color: #666;">Plan:</td>
                        <td style="padding: 12px 0; text-align: right; font-weight: bold;">{plan_name} ({billing_interval.title()})</td>
                    </tr>
                    <tr style="border-bottom: 1px solid #e5e7eb;">
                        <td style="padding: 12px 0; color: #666;">Amount Paid:</td>
                        <td style="padding: 12px 0; text-align: right; font-weight: bold; color: #10b981;">€{amount_paid:.2f}</td>
                    </tr>
                    <tr>
                        <td style="padding: 12px 0; color: #666;">Next Billing:</td>
                        <td style="padding: 12px 0; text-align: right; font-weight: bold;">{next_billing_date}</td>
                    </tr>
                </table>
            </div>
            
            <!-- Plan Features -->
            <div style="background: #fff; padding: 20px; border-radius: 8px; margin: 20px 0;">
                <h3 style="margin-top: 0; color: #667eea; font-size: 16px;">Your {plan_name} Plan Includes:</h3>
                <ul style="font-size: 14px; color: #666; margin: 0; padding-left: 20px;">
                    {features_html}
                </ul>
            </div>
            
            <div style="background: #eff6ff; padding: 15px; border-radius: 5px; border-left: 4px solid #3b82f6; margin: 20px 0;">
                <p style="margin: 0; font-size: 14px; color: #1e40af;">
                    <strong>📧 Invoice:</strong> A detailed invoice has been sent to your email and is available in your Stripe customer portal.
                </p>
            </div>
            
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
            
            <p style="font-size: 12px; color: #999; text-align: center; margin-top: 20px;">
                Questions? Contact us at {settings.FROM_EMAIL}
            </p>
        </div>
        
        <div style="text-align: center; margin-top: 20px; color: #999; font-size: 12px;">
            <p>© 2025 LLMReady. All rights reserved.</p>
        </div>
    </body>
    </html>
    """
    
    features_text = "\n".join([f"  • {feature}" for feature in features])
    
    text_content = f"""
    {name_greeting}
    
    Thank you for your payment! Your {plan_name} subscription is now active.
    
    PAYMENT SUMMARY
    ---------------
    Plan: {plan_name} ({billing_interval.title()})
    Amount Paid: €{amount_paid:.2f}
    Next Billing: {next_billing_date}
    
    YOUR {plan_name.upper()} PLAN INCLUDES:
    {features_text}
    
    📧 Invoice: A detailed invoice has been sent to your email and is available in your Stripe customer portal.
    
    Dashboard: {settings.FRONTEND_URL}/dashboard
    
    Questions? Contact us at {settings.FROM_EMAIL}
    
    Best regards,
    The LLMReady Team
    """
    
    return await email_service.send_email(
        to_email=to_email,
        subject=f"Payment Confirmed - {plan_name} Plan Active! 🎉",
        html_content=html_content,
        text_content=text_content
    )


def send_subscription_payment_email(
    to_email: str,
    user_name: Optional[str],
    plan_name: str,
    amount_paid: float,
    billing_interval: str,
    next_billing_date: str,
    features: list
) -> bool:
    """Synchronous wrapper for subscription payment email."""
    import asyncio
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(
        send_subscription_payment_email_async(
            to_email, user_name, plan_name, amount_paid,
            billing_interval, next_billing_date, features
        )
    )

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
"""
Security middleware for adding security headers to all responses.
Implements security best practices including HSTS, CSP, and anti-clickjacking.
"""
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add security headers to all responses.
    
    Headers added:
    - Strict-Transport-Security: Forces HTTPS for 1 year
    - X-Content-Type-Options: Prevents MIME type sniffing
    - X-Frame-Options: Prevents clickjacking
    - X-XSS-Protection: Enables XSS filter
    - Content-Security-Policy: Restricts resource loading
    - Referrer-Policy: Controls referrer information
    """
    
    async def dispatch(self, request: Request, call_next):
        """Add security headers to response."""
        response: Response = await call_next(request)
        
        # Strict-Transport-Security (HSTS)
        # Tells browsers to only use HTTPS for this domain for 1 year
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        # X-Content-Type-Options
        # Prevents browsers from MIME-sniffing a response away from declared content-type
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # X-Frame-Options
        # Prevents site from being embedded in iframe (clickjacking protection)
        response.headers["X-Frame-Options"] = "DENY"
        
        # X-XSS-Protection
        # Enables XSS filter built into most browsers
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # Content-Security-Policy
        # Restricts sources of content that can be loaded
        # This is a basic policy - adjust based on your needs
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:; "
            "connect-src 'self'; "
            "frame-ancestors 'none';"
        )
        
        # Referrer-Policy
        # Controls how much referrer information is sent
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Permissions-Policy (formerly Feature-Policy)
        # Controls which browser features can be used
        response.headers["Permissions-Policy"] = (
            "geolocation=(), "
            "microphone=(), "
            "camera=(), "
            "payment=(), "
            "usb=(), "
            "magnetometer=(), "
            "gyroscope=(), "
            "accelerometer=()"
        )
        
        return response
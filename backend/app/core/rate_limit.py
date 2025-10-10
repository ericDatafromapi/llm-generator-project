"""
Rate limiting configuration using SlowAPI.
Protects authentication endpoints from brute force attacks.
"""
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request, Response
from fastapi.responses import JSONResponse


# Initialize rate limiter
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["60/minute"],  # Default: 60 requests per minute
    storage_uri="memory://",  # Use in-memory storage for MVP (can switch to Redis later)
)


def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> Response:
    """
    Custom handler for rate limit exceeded errors.
    
    Args:
        request: The FastAPI request object
        exc: The RateLimitExceeded exception
        
    Returns:
        JSON response with 429 status code
    """
    return JSONResponse(
        status_code=429,
        content={
            "detail": "Rate limit exceeded. Please try again later.",
            "error_code": "RATE_LIMIT_EXCEEDED",
            "retry_after": str(exc.detail).split("Retry after ")[1] if "Retry after" in str(exc.detail) else "60 seconds"
        }
    )
"""
FastAPI main application.
Entry point for the LLMReady backend API.
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
import logging
import sentry_sdk

from app.core.config import settings
from app.core.database import engine, Base
from app.core.rate_limit import limiter, rate_limit_exceeded_handler
from app.core.logging_config import configure_monitoring
from app.core.security_middleware import SecurityHeadersMiddleware
from app.api.v1 import auth, password_reset, email_verification, subscriptions, webhooks, generations, websites, contact, refunds

# Initialize monitoring and logging BEFORE creating the app
configure_monitoring()

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="LLMReady - Professional AI Content Optimization Platform",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add Security Headers Middleware
app.add_middleware(SecurityHeadersMiddleware)

# Add rate limiter state to app
app.state.limiter = limiter

# Add rate limit exceeded exception handler
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)


# Global exception handler for Sentry
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler that captures all unhandled exceptions
    and sends them to Sentry before returning an error response.
    """
    # Capture exception in Sentry
    if settings.SENTRY_DSN:
        sentry_sdk.capture_exception(exc)
    
    # Log the error
    logger.error(
        f"Unhandled exception: {exc}",
        exc_info=True,
        extra={
            "path": request.url.path,
            "method": request.method,
            "client_host": request.client.host if request.client else None,
        }
    )
    
    # Return appropriate error response
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "error": str(exc) if settings.DEBUG else "An unexpected error occurred"
        }
    )


@app.on_event("startup")
async def startup_event():
    """Run on application startup."""
    logger.info(f"Starting {settings.PROJECT_NAME}")
    logger.info(f"Debug mode: {settings.DEBUG}")
    logger.info(f"Database: {settings.DATABASE_URL.split('@')[1] if '@' in settings.DATABASE_URL else 'configured'}")
    
    # Note: In production, we use Alembic migrations instead of create_all
    # Base.metadata.create_all(bind=engine)


@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown."""
    logger.info(f"Shutting down {settings.PROJECT_NAME}")


@app.get("/", tags=["Root"])
@limiter.limit(f"{settings.RATE_LIMIT_HEALTH_PER_MINUTE}/minute")
async def root(request: Request):
    """Root endpoint. Rate limited."""
    return {
        "message": "LLMReady API",
        "version": "1.0.0",
        "status": "operational",
        "docs": "/api/docs"
    }


@app.get("/health", tags=["Health"])
@limiter.limit(f"{settings.RATE_LIMIT_HEALTH_PER_MINUTE}/minute")
async def health_check(request: Request):
    """
    Health check endpoint.
    Returns 200 if the service is healthy.
    Rate limited to prevent abuse.
    """
    try:
        # Test database connection
        from sqlalchemy import text
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        
        return JSONResponse(
            status_code=200,
            content={
                "status": "healthy",
                "database": "connected",
                "service": settings.PROJECT_NAME
            }
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "database": "disconnected",
                "error": str(e)
            }
        )

@app.get("/test-sentry", tags=["Testing"])
async def test_sentry():
    """
    Test endpoint to verify Sentry error tracking.
    This endpoint intentionally throws an error to test monitoring.
    """
    logger.info("Test Sentry endpoint called - about to throw an error")
    raise ValueError("🔥 This is a TEST error to verify Sentry is working! If you see this in Sentry, everything is configured correctly.")



# API v1 routes - Authentication
app.include_router(
    auth.router,
    prefix=f"{settings.API_V1_PREFIX}/auth",
    tags=["Authentication"]
)

app.include_router(
    password_reset.router,
    prefix=f"{settings.API_V1_PREFIX}/auth/password-reset",
    tags=["Password Reset"]
)

app.include_router(
    email_verification.router,
    prefix=f"{settings.API_V1_PREFIX}/auth/email-verification",
    tags=["Email Verification"]
)

# API v1 routes - Subscriptions & Payments
app.include_router(
    subscriptions.router,
    prefix=settings.API_V1_PREFIX
)

# Webhook routes (no auth required)
app.include_router(
    webhooks.router,
    prefix=settings.API_V1_PREFIX
)

# API v1 routes - Generations
app.include_router(
    generations.router,
    prefix=settings.API_V1_PREFIX
)

# API v1 routes - Websites
app.include_router(
    websites.router,
    prefix=settings.API_V1_PREFIX
)

# API v1 routes - Contact (public)
app.include_router(
    contact.router,
    prefix=settings.API_V1_PREFIX
)

# API v1 routes - Refunds (EU cooling-off period)
app.include_router(
    refunds.router,
    prefix=settings.API_V1_PREFIX
)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
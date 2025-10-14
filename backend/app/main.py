"""
FastAPI main application.
Entry point for the LLMReady backend API.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
import logging

from app.core.config import settings
from app.core.database import engine, Base
from app.core.rate_limit import limiter, rate_limit_exceeded_handler
from app.api.v1 import auth, password_reset, email_verification, subscriptions, webhooks, generations

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
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

# Add rate limiter state to app
app.state.limiter = limiter

# Add rate limit exceeded exception handler
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)


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
async def root():
    """Root endpoint."""
    return {
        "message": "LLMReady API",
        "version": "1.0.0",
        "status": "operational",
        "docs": "/api/docs"
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint.
    Returns 200 if the service is healthy.
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
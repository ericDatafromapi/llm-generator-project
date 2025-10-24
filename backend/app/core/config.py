"""
Application configuration using Pydantic Settings.
Reads from environment variables and .env file.
"""
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="allow"  # Allow extra fields like ENVIRONMENT for different environments
    )
    
    # Project Info
    PROJECT_NAME: str = "LLMReady"
    API_V1_PREFIX: str = "/api/v1"
    DEBUG: bool = True
    ENVIRONMENT: str = "development"  # development, test, production
    
    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/llmready_dev"
    DATABASE_ECHO: bool = False
    
    # Redis & Celery
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production-min-32-chars"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # CORS - stored as comma-separated string in .env
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:8501,http://localhost:8000"
    
    # Frontend URL for email links
    FRONTEND_URL: str = "http://localhost:3000"
    
    def get_cors_origins(self) -> List[str]:
        """Get CORS origins as list."""
        if isinstance(self.ALLOWED_ORIGINS, str):
            return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]
        return []
    
    # Stripe (for Week 4-5)
    STRIPE_SECRET_KEY: str = "sk_test_your_key_here"
    STRIPE_PUBLISHABLE_KEY: str = "pk_test_your_key_here"
    STRIPE_WEBHOOK_SECRET: str = "whsec_your_webhook_secret_here"
    
    # Subscription Plans Configuration
    # These should match your Stripe Dashboard product/price IDs
    STRIPE_PRICE_FREE: str = ""  # Free plan (no Stripe product needed)
    
    # Starter Plan (NEW)
    STRIPE_PRICE_STARTER_MONTHLY: str = ""  # Replace with actual price ID
    STRIPE_PRICE_STARTER_YEARLY: str = ""   # Replace with actual price ID
    
    # Standard Plan
    STRIPE_PRICE_STANDARD: str = ""  # Legacy - kept for backward compatibility
    STRIPE_PRICE_STANDARD_MONTHLY: str = ""  # Replace with actual price ID
    STRIPE_PRICE_STANDARD_YEARLY: str = ""   # Replace with actual price ID
    
    # Pro Plan
    STRIPE_PRICE_PRO: str = ""  # Legacy - kept for backward compatibility
    STRIPE_PRICE_PRO_MONTHLY: str = ""  # Replace with actual price ID
    STRIPE_PRICE_PRO_YEARLY: str = ""   # Replace with actual price ID
    
    # Email (for Week 3)
    SENDGRID_API_KEY: str = ""
    FROM_EMAIL: str = "noreply@yourdomain.com"
    
    # File Storage
    FILE_STORAGE_PATH: str = "./storage/files"  # Use local directory instead of /var
    MAX_FILE_SIZE_MB: int = 500
    
    # Generation Settings
    GENERATION_TIMEOUT: int = 3600  # 1 hour in seconds
    GENERATION_MAX_RETRIES: int = 2
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    # Authentication rate limits - STRICT defaults for production security
    # Override in .env for stress testing: RATE_LIMIT_REGISTER_PER_HOUR=100
    RATE_LIMIT_REGISTER_PER_HOUR: int = 5    # Registrations per hour per IP (PRODUCTION DEFAULT)
    RATE_LIMIT_LOGIN_PER_MINUTE: int = 5     # Login attempts per minute per IP (PRODUCTION DEFAULT)
    RATE_LIMIT_HEALTH_PER_MINUTE: int = 100  # Health checks per minute (PRODUCTION DEFAULT)
    
    # Monitoring & Logging
    SENTRY_DSN: str = ""  # Sentry DSN for error tracking
    SENTRY_TRACES_SAMPLE_RATE: float = 0.1  # 10% of transactions
    SENTRY_PROFILES_SAMPLE_RATE: float = 0.1  # 10% of transactions
    LOG_LEVEL: str = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL


# Global settings instance
settings = Settings()
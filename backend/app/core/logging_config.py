"""
Centralized logging and monitoring configuration.
Integrates Sentry for error tracking and structured JSON logging.
"""
import logging
import sys
from typing import Any, Dict
from pythonjsonlogger import jsonlogger

import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.redis import RedisIntegration
from sentry_sdk.integrations.logging import LoggingIntegration

from app.core.config import settings


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter with additional context."""
    
    def add_fields(
        self,
        log_record: Dict[str, Any],
        record: logging.LogRecord,
        message_dict: Dict[str, Any]
    ) -> None:
        """Add custom fields to log records."""
        super().add_fields(log_record, record, message_dict)
        
        # Add environment and service info
        log_record['environment'] = settings.ENVIRONMENT
        log_record['service'] = settings.PROJECT_NAME
        
        # Add log level
        log_record['level'] = record.levelname
        
        # Add module and function info
        log_record['module'] = record.module
        log_record['function'] = record.funcName
        
        # Add line number
        log_record['line'] = record.lineno


def setup_logging() -> None:
    """
    Configure application-wide logging with JSON formatting.
    Sets up structured logging for production environments.
    """
    # Determine log level
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    
    # Create root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Remove existing handlers
    root_logger.handlers = []
    
    # Console handler with JSON formatting in production
    console_handler = logging.StreamHandler(sys.stdout)
    
    if settings.ENVIRONMENT == "production":
        # Use JSON formatting in production
        json_formatter = CustomJsonFormatter(
            '%(timestamp)s %(level)s %(name)s %(message)s'
        )
        console_handler.setFormatter(json_formatter)
    else:
        # Use standard formatting in development
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(formatter)
    
    console_handler.setLevel(log_level)
    root_logger.addHandler(console_handler)
    
    # Configure third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    
    logger = logging.getLogger(__name__)
    logger.info(
        f"Logging configured - Environment: {settings.ENVIRONMENT}, "
        f"Level: {settings.LOG_LEVEL}"
    )


def setup_sentry() -> None:
    """
    Initialize Sentry SDK for error tracking and performance monitoring.
    Only enabled if SENTRY_DSN is configured.
    """
    if not settings.SENTRY_DSN or settings.SENTRY_DSN == "":
        logger = logging.getLogger(__name__)
        logger.info("Sentry disabled - No DSN configured")
        return
    
    # Configure Sentry integrations
    integrations = [
        FastApiIntegration(transaction_style="endpoint"),
        SqlalchemyIntegration(),
        CeleryIntegration(monitor_beat_tasks=True),
        RedisIntegration(),
        LoggingIntegration(
            level=logging.INFO,  # Capture info and above as breadcrumbs
            event_level=logging.ERROR  # Send errors and above as events
        ),
    ]
    
    # Initialize Sentry
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        environment=settings.ENVIRONMENT,
        traces_sample_rate=settings.SENTRY_TRACES_SAMPLE_RATE,
        profiles_sample_rate=settings.SENTRY_PROFILES_SAMPLE_RATE,
        integrations=integrations,
        
        # Performance monitoring
        enable_tracing=True,
        
        # Release tracking (optional - set via environment variable)
        # release="llmready@1.0.0",
        
        # Additional options
        debug=settings.DEBUG,
        attach_stacktrace=True,
        send_default_pii=False,  # Don't send PII by default
        
        # Filter out health check requests
        before_send_transaction=lambda event, hint: (
            None if event.get("transaction") == "/health" else event
        ),
    )
    
    logger = logging.getLogger(__name__)
    logger.info(
        f"Sentry initialized - Environment: {settings.ENVIRONMENT}, "
        f"Traces sample rate: {settings.SENTRY_TRACES_SAMPLE_RATE}"
    )


def configure_monitoring() -> None:
    """
    Configure all monitoring and logging components.
    Call this function once at application startup.
    """
    setup_logging()
    setup_sentry()
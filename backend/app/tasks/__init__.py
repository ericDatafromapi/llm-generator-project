"""
Celery tasks package.
Contains background tasks for generation and scheduled operations.
"""
# Import tasks to ensure they are registered with Celery
from app.tasks.generation import generate_llm_content
from app.tasks.scheduled import (
    reset_monthly_quotas,
    cleanup_old_generations,
    sync_stripe_subscriptions
)

__all__ = [
    'generate_llm_content',
    'reset_monthly_quotas',
    'cleanup_old_generations',
    'sync_stripe_subscriptions'
]
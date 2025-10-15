"""
Celery application configuration for background task processing.
Handles file generation tasks and scheduled jobs (quota resets).
"""
from celery import Celery
from celery.schedules import crontab
from app.core.config import settings

# Create Celery app instance
celery_app = Celery(
    'llmready',
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=['app.tasks.generation', 'app.tasks.scheduled']
)

# Celery Configuration
celery_app.conf.update(
    # Serialization
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    
    # Timezone
    timezone='UTC',
    enable_utc=True,
    
    # Task execution
    task_track_started=True,
    task_time_limit=3600,  # 1 hour hard limit
    task_soft_time_limit=3300,  # 55 minutes soft limit
    
    # Results
    result_expires=86400,  # 24 hours
    result_extended=True,
    
    # Error handling
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    
    # Beat schedule for periodic tasks
    beat_schedule={
        'reset-monthly-quotas': {
            'task': 'app.tasks.scheduled.reset_monthly_quotas',
            'schedule': crontab(hour=0, minute=0, day_of_month=1),  # 1st of each month at midnight UTC
        },
        'cleanup-old-generations': {
            'task': 'app.tasks.scheduled.cleanup_old_generations',
            'schedule': crontab(hour=2, minute=0),  # Daily at 2 AM UTC
        },
        'sync-stripe-subscriptions': {
            'task': 'app.tasks.scheduled.sync_stripe_subscriptions',
            'schedule': crontab(minute='0'),  # Every hour at :00
        },
    },
)

# Task routes (optional - for multiple queues)
celery_app.conf.task_routes = {
    'app.tasks.generation.*': {'queue': 'generation'},
    'app.tasks.scheduled.*': {'queue': 'scheduled'},
}
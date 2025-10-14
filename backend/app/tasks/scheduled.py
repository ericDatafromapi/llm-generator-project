"""
Scheduled Celery tasks for periodic operations.
Handles monthly quota resets, cleanup operations, and Stripe subscription syncing.
"""
import logging
import stripe
from datetime import datetime, timedelta

from app.core.celery_app import celery_app
from app.core.database import SessionLocal
from app.core.config import settings
from app.models.subscription import Subscription
from app.models.generation import Generation

# Configure Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY

logger = logging.getLogger(__name__)


@celery_app.task
def reset_monthly_quotas():
    """
    Reset generation usage counters for all subscriptions.
    Runs on the 1st of each month at midnight UTC.
    """
    db = SessionLocal()
    
    try:
        logger.info("Starting monthly quota reset")
        
        # Reset all subscription usage counters
        updated = db.query(Subscription).update({
            Subscription.generations_used: 0
        })
        
        db.commit()
        
        logger.info(f"Reset quotas for {updated} subscriptions")
        return {"reset_count": updated, "timestamp": datetime.utcnow().isoformat()}
        
    except Exception as e:
        logger.exception(f"Failed to reset monthly quotas: {str(e)}")
        db.rollback()
        raise
        
    finally:
        db.close()


@celery_app.task
def cleanup_old_generations():
    """
    Clean up old failed or completed generation files.
    Runs daily at 2 AM UTC.
    Removes files older than 30 days for failed generations
    and older than 90 days for completed generations.
    """
    db = SessionLocal()
    
    try:
        logger.info("Starting cleanup of old generations")
        
        # Calculate cutoff dates
        failed_cutoff = datetime.utcnow() - timedelta(days=30)
        completed_cutoff = datetime.utcnow() - timedelta(days=90)
        
        # Find old failed generations
        old_failed = db.query(Generation).filter(
            Generation.status == 'failed',
            Generation.created_at < failed_cutoff
        ).all()
        
        # Find old completed generations
        old_completed = db.query(Generation).filter(
            Generation.status == 'completed',
            Generation.created_at < completed_cutoff
        ).all()
        
        cleanup_count = 0
        
        # Delete old failed generation records
        for gen in old_failed:
            try:
                db.delete(gen)
                cleanup_count += 1
            except Exception as e:
                logger.error(f"Failed to delete generation {gen.id}: {e}")
        
        # For completed generations, just delete the files but keep records
        # (users may want to see their history)
        import os
        for gen in old_completed:
            if gen.file_path and os.path.exists(gen.file_path):
                try:
                    os.remove(gen.file_path)
                    gen.file_path = None
                    gen.file_size = None
                    logger.info(f"Deleted file for generation {gen.id}")
                    cleanup_count += 1
                except Exception as e:
                    logger.error(f"Failed to delete file {gen.file_path}: {e}")
        
        db.commit()
        
        logger.info(f"Cleaned up {cleanup_count} items")
        return {
            "cleanup_count": cleanup_count,
            "failed_count": len(old_failed),
            "completed_count": len(old_completed),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.exception(f"Failed to cleanup old generations: {str(e)}")
        db.rollback()
        raise
        
    finally:
        db.close()


@celery_app.task
def sync_stripe_subscriptions():
    """
    Backup sync task - runs hourly to catch missed webhooks.
    Syncs subscription status from Stripe for any subscriptions
    that have a Stripe subscription ID but aren't in 'active' status.
    
    This provides resilience against:
    - Missed webhooks due to network issues
    - Stripe outages
    - Webhook endpoint downtime
    """
    db = SessionLocal()
    
    try:
        logger.info("Starting Stripe subscription sync")
        
        # Find subscriptions with pending Stripe IDs
        # Look for subscriptions that have a stripe_subscription_id but aren't active/trialing
        pending_subscriptions = db.query(Subscription).filter(
            Subscription.stripe_subscription_id != None,
            Subscription.status.notin_(['active', 'trialing', 'canceled'])
        ).all()
        
        sync_count = 0
        error_count = 0
        
        for sub in pending_subscriptions:
            try:
                # Fetch current status from Stripe
                stripe_sub = stripe.Subscription.retrieve(sub.stripe_subscription_id)
                
                # Check if status differs
                if stripe_sub.status != sub.status:
                    old_status = sub.status
                    sub.status = stripe_sub.status
                    
                    # Update period dates if changed
                    if stripe_sub.current_period_start:
                        sub.current_period_start = datetime.fromtimestamp(stripe_sub.current_period_start)
                    if stripe_sub.current_period_end:
                        sub.current_period_end = datetime.fromtimestamp(stripe_sub.current_period_end)
                    
                    sub.cancel_at_period_end = stripe_sub.cancel_at_period_end
                    sub.updated_at = datetime.utcnow()
                    
                    logger.info(
                        f"Synced subscription {sub.id} from Stripe: "
                        f"{old_status} -> {stripe_sub.status}"
                    )
                    sync_count += 1
            
            except stripe.error.StripeError as e:
                logger.error(f"Stripe error syncing subscription {sub.id}: {e}")
                error_count += 1
            except Exception as e:
                logger.error(f"Failed to sync subscription {sub.id}: {e}")
                error_count += 1
        
        db.commit()
        
        result = {
            "synced_count": sync_count,
            "error_count": error_count,
            "total_checked": len(pending_subscriptions),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        logger.info(
            f"Stripe sync complete: {sync_count} synced, "
            f"{error_count} errors, {len(pending_subscriptions)} checked"
        )
        
        return result
        
    except Exception as e:
        logger.exception(f"Failed to sync Stripe subscriptions: {str(e)}")
        db.rollback()
        raise
        
    finally:
        db.close()
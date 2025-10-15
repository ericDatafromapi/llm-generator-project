"""
Stripe webhook handler for processing subscription events.
Production-ready with persistent idempotency, proper error handling, and comprehensive event coverage.
"""
import stripe
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from uuid import UUID
from fastapi import APIRouter, Request, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.core.config import settings
from app.core.database import get_db
from app.models.user import User
from app.models.subscription import Subscription
from app.models.stripe_event import StripeEvent
from app.core.subscription_plans import get_plan_limits
from app.services.subscription import SubscriptionService
from app.services.email import (
    send_payment_success_email,
    send_payment_failed_email,
    send_chargeback_email,
    send_refund_email,
    send_payment_action_required_email,
    send_subscription_canceled_email
)

# Configure Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY

router = APIRouter(prefix="/webhooks", tags=["webhooks"])
logger = logging.getLogger(__name__)

# Grace period for past_due subscriptions (days)
GRACE_PERIOD_DAYS = 3


def is_event_processed(db: Session, event_id: str) -> bool:
    """Check if event has already been processed."""
    return db.query(StripeEvent).filter(StripeEvent.id == event_id).first() is not None


def should_process_event(db: Session, event_id: str, event_type: str, event_created: int) -> bool:
    """
    Check if this event should be processed based on timestamp ordering.
    Prevents processing old events after newer ones have been processed.
    """
    # Check if already processed
    if is_event_processed(db, event_id):
        logger.info(f"Event {event_id} already processed, skipping")
        return False
    
    # Check if a newer event of the same type was already processed
    # This handles out-of-order webhook delivery
    newer_event = db.query(StripeEvent).filter(
        StripeEvent.type == event_type,
        StripeEvent.created > event_created
    ).first()
    
    if newer_event:
        logger.warning(f"Skipping old event {event_id} ({event_type}), newer event already processed")
        # Still mark as processed to prevent future attempts
        mark_event_processed(db, event_id, event_type, event_created)
        return False
    
    return True


def mark_event_processed(db: Session, event_id: str, event_type: str, event_created: int) -> None:
    """Mark event as successfully processed."""
    try:
        event = StripeEvent(
            id=event_id,
            type=event_type,
            created=event_created,
            status="processed"
        )
        db.add(event)
        db.commit()
        logger.info(f"Marked event {event_id} as processed")
    except Exception as e:
        logger.error(f"Failed to mark event as processed: {e}")
        db.rollback()


def mark_event_failed(db: Session, event_id: str, event_type: str, event_created: int, error_message: str) -> None:
    """Mark event as failed with error message."""
    try:
        event = StripeEvent(
            id=event_id,
            type=event_type,
            created=event_created,
            status="failed",
            error_message=error_message
        )
        db.add(event)
        db.commit()
        logger.error(f"Marked event {event_id} as failed: {error_message}")
    except Exception as e:
        logger.error(f"Failed to mark event as failed: {e}")
        db.rollback()


def get_user_by_stripe_customer_id(db: Session, customer_id: str) -> Optional[User]:
    """Get user by Stripe customer ID."""
    user = db.query(User).join(Subscription).filter(
        Subscription.stripe_customer_id == customer_id
    ).first()
    return user


def handle_checkout_session_completed(
    event_data: Dict[str, Any],
    db: Session
) -> None:
    """
    Handle successful checkout session completion.
    Creates or updates subscription record.
    """
    session = event_data
    customer_id = session.get("customer")
    subscription_id = session.get("subscription")
    metadata = session.get("metadata", {})
    
    user_id_str = metadata.get("user_id")
    plan_type = metadata.get("plan_type")
    
    logger.info(f"Checkout data: customer={customer_id}, subscription={subscription_id}, user={user_id_str}, plan={plan_type}")
    
    if not all([customer_id, subscription_id, user_id_str, plan_type]):
        logger.error(f"Missing required data in checkout session: {session}")
        return
    
    # Convert user_id string to UUID
    try:
        user_id = UUID(user_id_str)
        logger.info(f"Converted user_id to UUID: {user_id}")
    except (ValueError, TypeError) as e:
        logger.error(f"Invalid user_id format: {user_id_str}, error: {e}")
        return
    
    # Get user
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        logger.error(f"User {user_id} not found in database")
        return
    
    logger.info(f"Found user: {user.email}")
    
    # Get subscription details from Stripe
    logger.info(f"Retrieving Stripe subscription: {subscription_id}")
    stripe_subscription = stripe.Subscription.retrieve(subscription_id)
    
    # Extract subscription data safely
    sub_data = stripe_subscription.to_dict() if hasattr(stripe_subscription, 'to_dict') else dict(stripe_subscription)
    logger.info(f"Stripe subscription data: status={sub_data.get('status')}, period_start={sub_data.get('current_period_start')}")
    
    # Get or create subscription record
    subscription = db.query(Subscription).filter(Subscription.user_id == user_id).first()
    
    if not subscription:
        # Create new subscription
        limits = get_plan_limits(plan_type)
        subscription = Subscription(
            user_id=user_id,
            plan_type=plan_type,
            stripe_customer_id=customer_id,
            stripe_subscription_id=subscription_id,
            status=sub_data.get('status', 'active'),
            current_period_start=datetime.fromtimestamp(sub_data.get('current_period_start', 0)) if sub_data.get('current_period_start') else None,
            current_period_end=datetime.fromtimestamp(sub_data.get('current_period_end', 0)) if sub_data.get('current_period_end') else None,
            cancel_at_period_end=sub_data.get('cancel_at_period_end', False),
            generations_limit=limits["generations_limit"],
            generations_used=0,
            websites_limit=limits["max_websites"]
        )
        db.add(subscription)
    else:
        # Update existing subscription
        limits = get_plan_limits(plan_type)
        subscription.plan_type = plan_type
        subscription.stripe_customer_id = customer_id
        subscription.stripe_subscription_id = subscription_id
        subscription.status = sub_data.get('status', subscription.status)
        if sub_data.get('current_period_start'):
            subscription.current_period_start = datetime.fromtimestamp(sub_data['current_period_start'])
        if sub_data.get('current_period_end'):
            subscription.current_period_end = datetime.fromtimestamp(sub_data['current_period_end'])
        subscription.cancel_at_period_end = sub_data.get('cancel_at_period_end', subscription.cancel_at_period_end)
        subscription.generations_limit = limits["generations_limit"]
        subscription.websites_limit = limits["max_websites"]
        subscription.updated_at = datetime.utcnow()
    
    db.commit()
    logger.info(f"✅ SUCCESS: Subscription created/updated for user {user_id} ({user.email}), plan {plan_type}, DB ID: {subscription.id}")


def handle_subscription_updated(
    event_data: Dict[str, Any],
    db: Session
) -> None:
    """Handle subscription update/created events with quota overflow protection."""
    subscription_data = event_data
    subscription_id = subscription_data.get("id")
    customer_id = subscription_data.get("customer")
    
    logger.info(f"Processing subscription event: sub={subscription_id}, customer={customer_id}")
    
    if not subscription_id:
        logger.error("Missing subscription ID in update event")
        return
    
    # Get subscription record
    subscription = db.query(Subscription).filter(
        Subscription.stripe_subscription_id == subscription_id
    ).first()
    
    # If subscription doesn't exist yet, try to find by customer_id
    if not subscription and customer_id:
        subscription = db.query(Subscription).filter(
            Subscription.stripe_customer_id == customer_id
        ).first()
        
        if subscription:
            subscription.stripe_subscription_id = subscription_id
            logger.info(f"Linked subscription {subscription_id} to existing customer {customer_id}")
        else:
            # Create subscription from customer metadata
            try:
                stripe_customer = stripe.Customer.retrieve(customer_id)
                customer_metadata = stripe_customer.to_dict() if hasattr(stripe_customer, 'to_dict') else dict(stripe_customer)
                user_id_str = customer_metadata.get('metadata', {}).get('user_id')
                
                if not user_id_str:
                    logger.error(f"No user_id in customer {customer_id} metadata")
                    return
                
                user_id = UUID(user_id_str)
                logger.info(f"Creating subscription from customer metadata: user={user_id}")
                
                # Get plan type from subscription items
                items = subscription_data.get('items', {}).get('data', [])
                plan_type = 'free'
                if items:
                    price_id = items[0].get('price', {}).get('id')
                    if price_id == settings.STRIPE_PRICE_STANDARD:
                        plan_type = 'standard'
                    elif price_id == settings.STRIPE_PRICE_PRO:
                        plan_type = 'pro'
                
                limits = get_plan_limits(plan_type)
                subscription = Subscription(
                    user_id=user_id,
                    plan_type=plan_type,
                    stripe_customer_id=customer_id,
                    stripe_subscription_id=subscription_id,
                    status=subscription_data.get('status', 'active'),
                    current_period_start=datetime.fromtimestamp(subscription_data['current_period_start']) if subscription_data.get('current_period_start') else None,
                    current_period_end=datetime.fromtimestamp(subscription_data['current_period_end']) if subscription_data.get('current_period_end') else None,
                    cancel_at_period_end=subscription_data.get('cancel_at_period_end', False),
                    generations_limit=limits["generations_limit"],
                    generations_used=0,
                    websites_limit=limits["max_websites"]
                )
                db.add(subscription)
                db.commit()
                logger.info(f"✅ Created subscription from subscription.created event: user={user_id}, plan={plan_type}")
                return
                
            except Exception as e:
                logger.error(f"Error creating subscription from customer metadata: {e}", exc_info=True)
                return
    
    if not subscription:
        logger.warning(f"Subscription {subscription_id} not found and could not be created")
        return
    
    # Update subscription details
    old_plan = subscription.plan_type
    subscription.status = subscription_data.get("status", subscription.status)
    
    if subscription_data.get("current_period_start"):
        subscription.current_period_start = datetime.fromtimestamp(
            subscription_data.get("current_period_start")
        )
    if subscription_data.get("current_period_end"):
        subscription.current_period_end = datetime.fromtimestamp(
            subscription_data.get("current_period_end")
        )
    
    subscription.cancel_at_period_end = subscription_data.get(
        "cancel_at_period_end",
        subscription.cancel_at_period_end
    )
    subscription.updated_at = datetime.utcnow()
    
    # If plan changed, update limits with quota overflow handling
    items = subscription_data.get("items", {}).get("data", [])
    if items:
        price_id = items[0].get("price", {}).get("id")
        
        # Map price ID to plan type
        if price_id == settings.STRIPE_PRICE_STANDARD:
            new_plan = "standard"
        elif price_id == settings.STRIPE_PRICE_PRO:
            new_plan = "pro"
        else:
            new_plan = subscription.plan_type
        
        if new_plan != old_plan:
            old_limit = subscription.generations_limit
            limits = get_plan_limits(new_plan)
            subscription.plan_type = new_plan
            subscription.generations_limit = limits["generations_limit"]
            subscription.websites_limit = limits["max_websites"]
            
            # Handle quota overflow on downgrade
            if subscription.generations_used > limits["generations_limit"]:
                logger.warning(
                    f"User {subscription.user_id} downgraded from {old_plan} to {new_plan} "
                    f"with quota overage: {subscription.generations_used}/{limits['generations_limit']}"
                )
                # Set to limit (soft cap) - user can't generate until next billing cycle
                subscription.generations_used = limits["generations_limit"]
            
            logger.info(f"Plan changed from {old_plan} to {new_plan} for subscription {subscription_id}")
    
    db.commit()
    logger.info(f"Subscription {subscription_id} updated")


def handle_subscription_deleted(
    event_data: Dict[str, Any],
    db: Session
) -> None:
    """Handle subscription cancellation/deletion."""
    subscription_data = event_data
    subscription_id = subscription_data.get("id")
    
    if not subscription_id:
        logger.error("Missing subscription ID in delete event")
        return
    
    subscription = db.query(Subscription).filter(
        Subscription.stripe_subscription_id == subscription_id
    ).first()
    
    if not subscription:
        logger.warning(f"Subscription {subscription_id} not found in database")
        return
    
    # Get user for email notification
    user = db.query(User).filter(User.id == subscription.user_id).first()
    
    # Downgrade to free plan
    subscription.plan_type = "free"
    subscription.status = "canceled"
    subscription.stripe_subscription_id = None
    limits = get_plan_limits("free")
    subscription.generations_limit = limits["generations_limit"]
    subscription.websites_limit = limits["max_websites"]
    subscription.cancel_at_period_end = False
    subscription.updated_at = datetime.utcnow()
    
    db.commit()
    logger.info(f"Subscription {subscription_id} canceled, user downgraded to free")
    
    # Send cancellation email
    if user:
        try:
            send_subscription_canceled_email(user.email, user.full_name)
        except Exception as e:
            logger.error(f"Failed to send cancellation email: {e}")


def handle_payment_failed(
    event_data: Dict[str, Any],
    db: Session
) -> None:
    """Handle failed payment events."""
    invoice_data = event_data
    customer_id = invoice_data.get("customer")
    subscription_id = invoice_data.get("subscription")
    
    if not subscription_id:
        logger.error("Missing subscription ID in payment failed event")
        return
    
    subscription = db.query(Subscription).filter(
        Subscription.stripe_subscription_id == subscription_id
    ).first()
    
    if not subscription:
        logger.warning(f"Subscription {subscription_id} not found in database")
        return
    
    # Update status to indicate payment issue
    subscription.status = "past_due"
    subscription.updated_at = datetime.utcnow()
    
    db.commit()
    logger.warning(f"Payment failed for subscription {subscription_id}")
    
    # Send email notification
    user = db.query(User).filter(User.id == subscription.user_id).first()
    if user:
        try:
            send_payment_failed_email(user.email, user.full_name)
        except Exception as e:
            logger.error(f"Failed to send payment failed email: {e}")


def handle_payment_succeeded(event_data: Dict[str, Any], db: Session) -> None:
    """Handle successful payment events."""
    invoice_data = event_data
    subscription_id = invoice_data.get("subscription")
    amount_paid = invoice_data.get("amount_paid", 0) / 100  # Convert from cents
    
    if subscription_id:
        subscription = db.query(Subscription).filter(
            Subscription.stripe_subscription_id == subscription_id
        ).first()
        
        if subscription:
            # Ensure status is active
            subscription.status = "active"
            subscription.updated_at = datetime.utcnow()
            db.commit()
            
            # Send success email
            user = db.query(User).filter(User.id == subscription.user_id).first()
            if user:
                try:
                    send_payment_success_email(user.email, amount_paid, user.full_name)
                except Exception as e:
                    logger.error(f"Failed to send payment success email: {e}")
    
    logger.info(f"Payment succeeded for subscription {subscription_id}: €{amount_paid}")


def handle_charge_disputed(event_data: Dict[str, Any], db: Session) -> None:
    """Handle disputed charges (chargebacks)."""
    charge_data = event_data
    customer_id = charge_data.get("customer")
    amount = charge_data.get("amount", 0) / 100
    
    logger.warning(f"⚠️ CHARGEBACK: Customer {customer_id} disputed €{amount}")
    
    # Find subscription
    subscription = db.query(Subscription).filter(
        Subscription.stripe_customer_id == customer_id
    ).first()
    
    if subscription:
        # Immediately revoke access
        subscription.status = "canceled"
        subscription.plan_type = "free"
        limits = get_plan_limits("free")
        subscription.generations_limit = limits["generations_limit"]
        subscription.websites_limit = limits["max_websites"]
        db.commit()
        
        # Notify user
        user = db.query(User).filter(User.id == subscription.user_id).first()
        if user:
            try:
                send_chargeback_email(user.email, user.full_name)
            except Exception as e:
                logger.error(f"Failed to send chargeback email: {e}")


def handle_charge_refunded(event_data: Dict[str, Any], db: Session) -> None:
    """Handle refund events."""
    charge_data = event_data
    customer_id = charge_data.get("customer")
    amount_refunded = charge_data.get("amount_refunded", 0) / 100
    
    logger.info(f"Refund processed: Customer {customer_id}, €{amount_refunded}")
    
    # Find subscription
    subscription = db.query(Subscription).filter(
        Subscription.stripe_customer_id == customer_id
    ).first()
    
    if subscription and subscription.status == "active":
        # Downgrade to free (full refund)
        if charge_data.get("refunded"):  # Full refund
            subscription.plan_type = "free"
            subscription.status = "canceled"
            limits = get_plan_limits("free")
            subscription.generations_limit = limits["generations_limit"]
            subscription.websites_limit = limits["max_websites"]
            db.commit()
            
            # Notify user
            user = db.query(User).filter(User.id == subscription.user_id).first()
            if user:
                try:
                    send_refund_email(user.email, amount_refunded, user.full_name)
                except Exception as e:
                    logger.error(f"Failed to send refund email: {e}")


def handle_payment_action_required(event_data: Dict[str, Any], db: Session) -> None:
    """Handle payments requiring additional authentication (3D Secure)."""
    invoice_data = event_data
    customer_id = invoice_data.get("customer")
    hosted_invoice_url = invoice_data.get("hosted_invoice_url")
    
    # Get user
    subscription = db.query(Subscription).filter(
        Subscription.stripe_customer_id == customer_id
    ).first()
    
    if subscription:
        user = db.query(User).filter(User.id == subscription.user_id).first()
        if user and hosted_invoice_url:
            try:
                send_payment_action_required_email(user.email, hosted_invoice_url, user.full_name)
            except Exception as e:
                logger.error(f"Failed to send payment action required email: {e}")


def handle_customer_deleted(event_data: Dict[str, Any], db: Session) -> None:
    """Handle customer deletion in Stripe."""
    customer_id = event_data.get("id")
    
    subscription = db.query(Subscription).filter(
        Subscription.stripe_customer_id == customer_id
    ).first()
    
    if subscription:
        # Downgrade to free
        subscription.plan_type = "free"
        subscription.status = "canceled"
        subscription.stripe_customer_id = None
        subscription.stripe_subscription_id = None
        limits = get_plan_limits("free")
        subscription.generations_limit = limits["generations_limit"]
        subscription.websites_limit = limits["max_websites"]
        db.commit()
        
        logger.warning(f"Customer {customer_id} deleted, downgraded to free")


@router.post("/stripe")
async def stripe_webhook(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Handle Stripe webhook events with production-ready features:
    - Persistent idempotency using database
    - Proper error handling (returns 200 to prevent retries)
    - Event ordering to handle out-of-order delivery
    - Comprehensive event coverage
    """
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    
    if not sig_header:
        raise HTTPException(status_code=400, detail="Missing stripe-signature header")
    
    try:
        # Verify webhook signature
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        logger.error(f"Invalid payload: {e}")
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError as e:
        logger.error(f"Invalid signature: {e}")
        raise HTTPException(status_code=400, detail="Invalid signature")
    
    event_id = event.get("id")
    event_type = event["type"]
    event_data = event["data"]["object"]
    event_created = event.get("created", 0)
    
    logger.info(f"Received webhook event: {event_type} (ID: {event_id})")
    
    # Check if should process (idempotency + ordering)
    if not should_process_event(db, event_id, event_type, event_created):
        return {"status": "already_processed"}
    
    # Process event
    try:
        if event_type == "checkout.session.completed":
            handle_checkout_session_completed(event_data, db)
        
        elif event_type == "customer.subscription.created":
            handle_subscription_updated(event_data, db)
        
        elif event_type == "customer.subscription.updated":
            handle_subscription_updated(event_data, db)
        
        elif event_type == "customer.subscription.deleted":
            handle_subscription_deleted(event_data, db)
        
        elif event_type == "invoice.payment_failed":
            handle_payment_failed(event_data, db)
        
        elif event_type == "invoice.payment_succeeded":
            handle_payment_succeeded(event_data, db)
        
        elif event_type == "invoice.payment_action_required":
            handle_payment_action_required(event_data, db)
        
        elif event_type == "charge.dispute.created":
            handle_charge_disputed(event_data, db)
        
        elif event_type == "charge.refunded":
            handle_charge_refunded(event_data, db)
        
        elif event_type == "customer.deleted":
            handle_customer_deleted(event_data, db)
        
        else:
            logger.info(f"Unhandled event type: {event_type}")
        
        # Mark event as processed
        mark_event_processed(db, event_id, event_type, event_created)
        
        # Return 200 to acknowledge receipt
        return {"status": "success", "event_type": event_type}
    
    except Exception as e:
        logger.error(f"Error processing webhook event {event_type}: {e}", exc_info=True)
        # Log to stripe_events table with error
        mark_event_failed(db, event_id, event_type, event_created, str(e))
        # Return 200 to prevent Stripe retries (we've logged the error)
        return {"status": "error", "message": str(e), "event_type": event_type}
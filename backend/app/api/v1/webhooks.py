"""
Stripe webhook handler for processing subscription events.
"""
import stripe
import logging
from datetime import datetime
from typing import Dict, Any
from uuid import UUID
from fastapi import APIRouter, Request, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.core.config import settings
from app.core.database import get_db
from app.models.user import User
from app.models.subscription import Subscription
from app.core.subscription_plans import get_plan_limits
from app.services.subscription import SubscriptionService

# Configure Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY

router = APIRouter(prefix="/webhooks", tags=["webhooks"])
logger = logging.getLogger(__name__)

# Store processed webhook event IDs to prevent duplicate processing
processed_events = set()


def get_user_by_stripe_customer_id(db: Session, customer_id: str) -> User:
    """Get user by Stripe customer ID."""
    user = db.query(User).join(Subscription).filter(
        Subscription.stripe_customer_id == customer_id
    ).first()
    if not user:
        raise ValueError(f"No user found for Stripe customer {customer_id}")
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
            websites_limit=limits["max_websites"]  # Note: model uses websites_limit
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
        subscription.websites_limit = limits["max_websites"]  # Note: model uses websites_limit
        subscription.updated_at = datetime.utcnow()
    
    db.commit()
    logger.info(f"✅ SUCCESS: Subscription created/updated for user {user_id} ({user.email}), plan {plan_type}, DB ID: {subscription.id}")


def handle_subscription_updated(
    event_data: Dict[str, Any],
    db: Session
) -> None:
    """Handle subscription update/created events."""
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
    
    # If subscription doesn't exist yet (from subscription.created event),
    # try to find by customer_id
    if not subscription and customer_id:
        subscription = db.query(Subscription).filter(
            Subscription.stripe_customer_id == customer_id
        ).first()
        
        if subscription:
            # Link the subscription ID
            subscription.stripe_subscription_id = subscription_id
            logger.info(f"Linked subscription {subscription_id} to existing customer {customer_id}")
        else:
            # Subscription record doesn't exist yet - get user from customer metadata
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
                
                # Create new subscription
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
    
    # If plan changed, update limits
    items = subscription_data.get("items", {}).get("data", [])
    if items:
        # Get price ID from first item
        price_id = items[0].get("price", {}).get("id")
        
        # Map price ID to plan type
        if price_id == settings.STRIPE_PRICE_STANDARD:
            new_plan = "standard"
        elif price_id == settings.STRIPE_PRICE_PRO:
            new_plan = "pro"
        else:
            new_plan = subscription.plan_type
        
        if new_plan != subscription.plan_type:
            subscription.plan_type = new_plan
            limits = get_plan_limits(new_plan)
            subscription.generations_limit = limits["generations_limit"]
            subscription.websites_limit = limits["max_websites"]  # Note: model uses websites_limit
            logger.info(f"Plan changed to {new_plan} for subscription {subscription_id}")
    
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
    
    # Get subscription record
    subscription = db.query(Subscription).filter(
        Subscription.stripe_subscription_id == subscription_id
    ).first()
    
    if not subscription:
        logger.warning(f"Subscription {subscription_id} not found in database")
        return
    
    # Downgrade to free plan
    subscription.plan_type = "free"
    subscription.status = "canceled"
    subscription.stripe_subscription_id = None
    limits = get_plan_limits("free")
    subscription.generations_limit = limits["generations_limit"]
    subscription.websites_limit = limits["max_websites"]  # Note: model uses websites_limit
    subscription.cancel_at_period_end = False
    subscription.updated_at = datetime.utcnow()
    
    db.commit()
    logger.info(f"Subscription {subscription_id} canceled, user downgraded to free")


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
    
    # Get subscription record
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
    
    # TODO: Send email notification to user about failed payment


@router.post("/stripe")
async def stripe_webhook(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Handle Stripe webhook events.
    
    This endpoint receives events from Stripe about subscription lifecycle:
    - checkout.session.completed: New subscription created
    - customer.subscription.updated: Subscription changed (plan, status)
    - customer.subscription.deleted: Subscription canceled
    - invoice.payment_failed: Payment failed
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
    
    # Check for duplicate events (idempotency)
    event_id = event.get("id")
    if event_id in processed_events:
        logger.info(f"Event {event_id} already processed, skipping")
        return {"status": "already_processed"}
    
    # Process event
    event_type = event["type"]
    event_data = event["data"]["object"]
    
    logger.info(f"Processing webhook event: {event_type} (ID: {event_id})")
    
    try:
        if event_type == "checkout.session.completed":
            handle_checkout_session_completed(event_data, db)
        
        elif event_type == "customer.subscription.created":
            # Handle subscription.created the same way as subscription.updated
            handle_subscription_updated(event_data, db)
        
        elif event_type == "customer.subscription.updated":
            handle_subscription_updated(event_data, db)
        
        elif event_type == "customer.subscription.deleted":
            handle_subscription_deleted(event_data, db)
        
        elif event_type == "invoice.payment_failed":
            handle_payment_failed(event_data, db)
        
        else:
            logger.info(f"Unhandled event type: {event_type}")
        
        # Mark event as processed
        processed_events.add(event_id)
        
        # Cleanup old event IDs (keep last 1000)
        if len(processed_events) > 1000:
            processed_events.clear()
        
        return {"status": "success", "event_type": event_type}
    
    except Exception as e:
        logger.error(f"Error processing webhook event {event_type}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error processing webhook: {str(e)}"
        )
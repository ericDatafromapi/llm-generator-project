"""
Subscription service for managing Stripe subscriptions and quotas.
"""
import stripe
import logging
from typing import Optional
from datetime import datetime
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import select, func

logger = logging.getLogger(__name__)

from app.core.config import settings
from app.core.subscription_plans import PlanType, PLAN_FEATURES, get_plan_limits, get_plan_info
from app.models.user import User
from app.models.subscription import Subscription
from app.schemas.subscription import (
    CheckoutSessionResponse,
    CustomerPortalResponse,
    SubscriptionInfo,
    UsageStats,
    PlanInfo
)

# Configure Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY


class SubscriptionService:
    """Service for managing subscriptions and Stripe integration."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_checkout_session(
        self,
        user: User,
        plan_type: str,
        billing_interval: str = 'monthly',
        success_url: Optional[str] = None,
        cancel_url: Optional[str] = None
    ) -> CheckoutSessionResponse:
        """
        Create a Stripe checkout session or modify existing subscription.
        
        IMPORTANT: If user has an active paid subscription, this will MODIFY it
        with proration instead of creating a new subscription.
        
        Args:
            user: User subscribing
            plan_type: Plan to subscribe to (starter, standard, or pro)
            billing_interval: Billing interval (monthly or yearly)
            success_url: Custom success URL (optional)
            cancel_url: Custom cancel URL (optional)
            
        Returns:
            CheckoutSessionResponse with checkout URL or redirect URL
        """
        # Validate plan type
        if plan_type not in [PlanType.STARTER, PlanType.STANDARD, PlanType.PRO]:
            raise ValueError(f"Invalid plan type: {plan_type}. Must be 'starter', 'standard', or 'pro'")
        
        # Validate billing interval
        if billing_interval not in ['monthly', 'yearly']:
            billing_interval = 'monthly'
        
        # Get user's subscription
        subscription = self.get_user_subscription(user.id)
        
        # If user has an active PAID subscription, modify it instead of creating new one
        if subscription and subscription.stripe_subscription_id and subscription.plan_type != 'free':
            logger.info(f"User {user.id} has existing subscription {subscription.stripe_subscription_id}, modifying instead of creating new")
            
            # Get new price ID
            price_id_map = {
                ('starter', 'monthly'): settings.STRIPE_PRICE_STARTER_MONTHLY,
                ('starter', 'yearly'): settings.STRIPE_PRICE_STARTER_YEARLY,
                ('standard', 'monthly'): settings.STRIPE_PRICE_STANDARD_MONTHLY,
                ('standard', 'yearly'): settings.STRIPE_PRICE_STANDARD_YEARLY,
                ('pro', 'monthly'): settings.STRIPE_PRICE_PRO_MONTHLY,
                ('pro', 'yearly'): settings.STRIPE_PRICE_PRO_YEARLY,
            }
            
            new_price_id = price_id_map.get((plan_type, billing_interval))
            if not new_price_id:
                raise ValueError(f"No Stripe price ID configured for {plan_type} ({billing_interval})")
            
            # Retrieve current subscription from Stripe
            stripe_subscription = stripe.Subscription.retrieve(subscription.stripe_subscription_id)
            
            # Convert to dict for consistent access
            stripe_sub_dict = dict(stripe_subscription)
            
            # Get current subscription item ID
            items_data = stripe_sub_dict.get('items', {}).get('data', [])
            if not items_data:
                raise ValueError("No subscription items found")
            
            subscription_item_id = items_data[0]['id']
            
            # Modify subscription with proration and immediate billing
            updated_subscription = stripe.Subscription.modify(
                subscription.stripe_subscription_id,
                items=[{
                    'id': subscription_item_id,
                    'price': new_price_id,
                }],
                proration_behavior='create_prorations',  # Automatic proration
                billing_cycle_anchor='now',  # Reset billing cycle to now (charge immediately)
                proration_date=int(datetime.utcnow().timestamp())  # Calculate proration from now
            )
            
            logger.info(f"✅ Modified subscription {subscription.stripe_subscription_id} to {plan_type} with proration")
            
            # Update local subscription record immediately (don't wait for webhook)
            limits = get_plan_limits(plan_type)
            subscription.plan_type = plan_type
            subscription.generations_limit = limits["generations_limit"]
            subscription.websites_limit = limits["max_websites"]
            subscription.updated_at = datetime.utcnow()
            self.db.commit()
            
            logger.info(f"✅ Updated local subscription record to {plan_type}")
            
            # Return success URL directly (no checkout needed)
            if not success_url:
                success_url = f"{settings.FRONTEND_URL}/dashboard/subscription?upgraded=true"
            
            return CheckoutSessionResponse(
                checkout_url=success_url,
                session_id=subscription.stripe_subscription_id
            )
        
        # User has no paid subscription - create checkout session for new subscription
        if subscription and subscription.stripe_customer_id:
            customer_id = subscription.stripe_customer_id
        else:
            # Create new Stripe customer
            customer = stripe.Customer.create(
                email=user.email,
                name=user.full_name,
                metadata={
                    "user_id": str(user.id),
                    "plan_type": plan_type.value if hasattr(plan_type, 'value') else plan_type
                }
            )
            customer_id = customer.id
            
            # Update subscription with customer ID
            if subscription:
                subscription.stripe_customer_id = customer_id
                self.db.commit()
        
        # Get price ID based on plan and billing interval
        price_id_map = {
            ('starter', 'monthly'): settings.STRIPE_PRICE_STARTER_MONTHLY,
            ('starter', 'yearly'): settings.STRIPE_PRICE_STARTER_YEARLY,
            ('standard', 'monthly'): settings.STRIPE_PRICE_STANDARD_MONTHLY,
            ('standard', 'yearly'): settings.STRIPE_PRICE_STANDARD_YEARLY,
            ('pro', 'monthly'): settings.STRIPE_PRICE_PRO_MONTHLY,
            ('pro', 'yearly'): settings.STRIPE_PRICE_PRO_YEARLY,
        }
        
        price_id = price_id_map.get((plan_type, billing_interval))
        if not price_id:
            raise ValueError(f"No Stripe price ID configured for {plan_type} ({billing_interval})")
        
        # Set default URLs if not provided
        if not success_url:
            success_url = f"{settings.FRONTEND_URL}/dashboard?success=true&session_id={{CHECKOUT_SESSION_ID}}"
        if not cancel_url:
            cancel_url = f"{settings.FRONTEND_URL}/pricing?canceled=true"
        
        # Create checkout session with Terms of Service consent
        session = stripe.checkout.Session.create(
            customer=customer_id,
            payment_method_types=['card'],
            line_items=[{
                'price': price_id,
                'quantity': 1,
            }],
            mode='subscription',
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={
                "user_id": str(user.id),
                "plan_type": plan_type.value if hasattr(plan_type, 'value') else plan_type,
                "billing_interval": billing_interval
            },
            allow_promotion_codes=True,
            billing_address_collection='required',
            # ⭐ Require Terms of Service acceptance (EU compliance)
            consent_collection={
                'terms_of_service': 'required',
            },
        )
        
        return CheckoutSessionResponse(
            checkout_url=session.url,
            session_id=session.id
        )
    
    def create_customer_portal_session(
        self,
        user: User,
        return_url: Optional[str] = None
    ) -> CustomerPortalResponse:
        """
        Create a Stripe customer portal session.
        
        Args:
            user: User requesting portal access
            return_url: URL to return to after portal session
            
        Returns:
            CustomerPortalResponse with portal URL
        """
        subscription = self.get_user_subscription(user.id)
        
        if not subscription or not subscription.stripe_customer_id:
            raise ValueError("No Stripe customer found for this user")
        
        if not return_url:
            return_url = f"{settings.FRONTEND_URL}/dashboard"
        
        # Create portal session
        session = stripe.billing_portal.Session.create(
            customer=subscription.stripe_customer_id,
            return_url=return_url
        )
        
        return CustomerPortalResponse(portal_url=session.url)
    
    def get_user_subscription(self, user_id: UUID) -> Optional[Subscription]:
        """Get user's subscription."""
        return self.db.query(Subscription).filter(Subscription.user_id == user_id).first()
    
    def get_subscription_info(self, user: User) -> SubscriptionInfo:
        """
        Get detailed subscription information for a user.
        
        Args:
            user: User to get subscription info for
            
        Returns:
            SubscriptionInfo with all details
        """
        subscription = self.get_user_subscription(user.id)
        
        if not subscription:
            raise ValueError("No subscription found for user")
        
        # Get plan info
        plan_info = get_plan_info(subscription.plan_type)
        
        # Calculate remaining generations
        remaining = max(0, subscription.generations_limit - subscription.generations_used)
        
        # Calculate usage percentage
        usage_pct = (
            (subscription.generations_used / subscription.generations_limit * 100)
            if subscription.generations_limit > 0
            else 0
        )
        
        return SubscriptionInfo(
            id=subscription.id,
            user_id=subscription.user_id,
            plan_type=subscription.plan_type,
            stripe_customer_id=subscription.stripe_customer_id,
            stripe_subscription_id=subscription.stripe_subscription_id,
            status=subscription.status,
            current_period_start=subscription.current_period_start,
            current_period_end=subscription.current_period_end,
            cancel_at_period_end=subscription.cancel_at_period_end,
            generations_used=subscription.generations_used,
            generations_limit=subscription.generations_limit,
            max_websites=subscription.websites_limit,
            created_at=subscription.created_at,
            updated_at=subscription.updated_at,
            remaining_generations=remaining,
            usage_percentage=round(usage_pct, 2),
            plan_info=PlanInfo(**plan_info)
        )
    
    def get_usage_stats(self, user: User) -> UsageStats:
        """
        Get usage statistics for a user.
        
        Args:
            user: User to get stats for
            
        Returns:
            UsageStats with current usage information
        """
        subscription = self.get_user_subscription(user.id)
        
        if not subscription:
            raise ValueError("No subscription found for user")
        
        # Count websites
        from app.models.website import Website
        website_count = self.db.query(func.count(Website.id)).filter(Website.user_id == user.id).scalar()
        
        # Calculate remaining generations
        remaining = max(0, subscription.generations_limit - subscription.generations_used)
        
        # Calculate usage percentage
        usage_pct = (
            (subscription.generations_used / subscription.generations_limit * 100)
            if subscription.generations_limit > 0
            else 0
        )
        
        return UsageStats(
            current_plan=subscription.plan_type,
            generations_used=subscription.generations_used,
            generations_limit=subscription.generations_limit,
            remaining_generations=remaining,
            usage_percentage=round(usage_pct, 2),
            websites_count=website_count or 0,
            max_websites=subscription.websites_limit,
            period_start=subscription.current_period_start,
            period_end=subscription.current_period_end
        )
    
    def check_generation_quota(self, user_id: UUID) -> bool:
        """
        Check if user has available generation quota with grace period support.
        
        Args:
            user_id: User ID to check
            
        Returns:
            True if user can generate, False otherwise
        """
        subscription = self.get_user_subscription(user_id)
        
        if not subscription:
            return False
        
        # Allowed statuses
        ALLOWED_STATUSES = ["active", "trialing"]
        GRACE_PERIOD_DAYS = 3
        
        # Check status
        if subscription.status in ALLOWED_STATUSES:
            return subscription.generations_used < subscription.generations_limit
        
        # Grace period for past_due
        if subscription.status == "past_due":
            if subscription.updated_at:
                days_past_due = (datetime.utcnow() - subscription.updated_at).days
                if days_past_due <= GRACE_PERIOD_DAYS:
                    logger.info(f"User {user_id} in grace period: {days_past_due}/{GRACE_PERIOD_DAYS} days")
                    return subscription.generations_used < subscription.generations_limit
                else:
                    logger.warning(f"User {user_id} exceeded grace period: {days_past_due} days past due")
        
        return False
    
    def increment_usage(self, user_id: UUID) -> None:
        """
        Increment generation usage for a user.
        
        Args:
            user_id: User ID to increment usage for
        """
        subscription = self.get_user_subscription(user_id)
        
        if not subscription:
            raise ValueError("No subscription found for user")
        
        subscription.generations_used += 1
        subscription.updated_at = datetime.utcnow()
        self.db.commit()
    
    def check_website_limit(self, user_id: UUID) -> bool:
        """
        Check if user can create more websites.
        
        Args:
            user_id: User ID to check
            
        Returns:
            True if user can create more websites
        """
        subscription = self.get_user_subscription(user_id)
        
        if not subscription:
            return False
        
        # Count current websites
        from app.models.website import Website
        website_count = self.db.query(func.count(Website.id)).filter(Website.user_id == user_id).scalar()
        
        return (website_count or 0) < subscription.websites_limit
    
    def reset_monthly_usage(self, user_id: UUID) -> None:
        """
        Reset monthly usage for a user.
        Called by Celery beat on 1st of each month.
        
        Args:
            user_id: User ID to reset usage for
        """
        subscription = self.get_user_subscription(user_id)
        
        if subscription:
            subscription.generations_used = 0
            subscription.updated_at = datetime.utcnow()
            self.db.commit()
    
    def update_subscription_from_stripe(
        self,
        stripe_subscription_id: str,
        status: str,
        current_period_start: datetime,
        current_period_end: datetime,
        cancel_at_period_end: bool,
        plan_type: Optional[str] = None
    ) -> None:
        """
        Update subscription from Stripe webhook data.
        
        Args:
            stripe_subscription_id: Stripe subscription ID
            status: Subscription status
            current_period_start: Period start date
            current_period_end: Period end date
            cancel_at_period_end: Whether subscription cancels at period end
            plan_type: New plan type (if changed)
        """
        subscription = self.db.query(Subscription).filter(
            Subscription.stripe_subscription_id == stripe_subscription_id
        ).first()
        
        if not subscription:
            return
        
        subscription.status = status
        subscription.current_period_start = current_period_start
        subscription.current_period_end = current_period_end
        subscription.cancel_at_period_end = cancel_at_period_end
        subscription.updated_at = datetime.utcnow()
        
        # Update plan type if changed
        if plan_type and plan_type != subscription.plan_type:
            subscription.plan_type = plan_type
            limits = get_plan_limits(plan_type)
            subscription.generations_limit = limits["generations_limit"]
            subscription.websites_limit = limits["max_websites"]
        
        self.db.commit()
    
    def upgrade_subscription(self, user: User, new_plan_type: str) -> dict:
        """
        Upgrade subscription with proration.
        
        Args:
            user: User upgrading subscription
            new_plan_type: New plan type (standard or pro)
            
        Returns:
            Dict with upgrade status and proration info
        """
        subscription = self.get_user_subscription(user.id)
        
        if not subscription or not subscription.stripe_subscription_id:
            raise ValueError("No active subscription found")
        
        # Get new price ID
        new_price_id = (
            settings.STRIPE_PRICE_STANDARD if new_plan_type == "standard"
            else settings.STRIPE_PRICE_PRO
        )
        
        # Retrieve current subscription from Stripe
        stripe_subscription = stripe.Subscription.retrieve(subscription.stripe_subscription_id)
        
        # Convert to dict for consistent access
        stripe_sub_dict = dict(stripe_subscription)
        
        # Get current subscription item ID
        items_data = stripe_sub_dict.get('items', {}).get('data', [])
        if not items_data:
            raise ValueError("No subscription items found")
        
        subscription_item_id = items_data[0]['id']
        
        # Update Stripe subscription with proration
        updated_subscription = stripe.Subscription.modify(
            subscription.stripe_subscription_id,
            items=[{
                'id': subscription_item_id,
                'price': new_price_id,
            }],
            proration_behavior='create_prorations',  # Enable proration
        )
        
        logger.info(f"Subscription upgraded with proration: {subscription.stripe_subscription_id}")
        
        return {
            "status": "upgraded",
            "proration": "applied",
            "new_plan": new_plan_type
        }
    
    def cancel_user_subscription_on_deletion(self, user_id: UUID) -> None:
        """
        Cancel Stripe subscription when user account is deleted.
        This prevents continued billing after account deletion.
        
        Args:
            user_id: User ID being deleted
        """
        subscription = self.get_user_subscription(user_id)
        
        if not subscription:
            logger.info(f"No subscription found for user {user_id} during deletion")
            return
        
        if subscription.stripe_subscription_id:
            try:
                # Cancel subscription in Stripe immediately
                stripe.Subscription.delete(subscription.stripe_subscription_id)
                logger.info(f"Canceled Stripe subscription {subscription.stripe_subscription_id} for deleted user {user_id}")
            except stripe.error.StripeError as e:
                logger.error(f"Failed to cancel Stripe subscription during user deletion: {e}")
                # Don't raise - allow user deletion to proceed
            except Exception as e:
                logger.error(f"Unexpected error canceling subscription during user deletion: {e}")
        
        # Update local subscription record
        subscription.status = "canceled"
        subscription.plan_type = "free"
        subscription.stripe_subscription_id = None
        subscription.updated_at = datetime.utcnow()
        self.db.commit()
        
        logger.info(f"Local subscription canceled for deleted user {user_id}")
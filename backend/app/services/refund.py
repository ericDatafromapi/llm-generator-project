"""
EU 14-Day Cooling-Off Period Refund Service.

Implements EU Consumer Rights Directive (2011/83/EU) compliant refund logic
with usage-based charges to prevent abuse while staying legal.
"""
import stripe
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from decimal import Decimal
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.subscription import Subscription
from app.models.user import User
from app.models.generation import Generation

logger = logging.getLogger(__name__)

# Configure Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY

# EU Cooling-off period (days)
EU_COOLING_OFF_DAYS = 14

# Pricing per generation (calculated from plan limits)
PRICE_PER_GENERATION = {
    'starter_monthly': 19 / 3,      # €19/month ÷ 3 generations = €6.33 per gen
    'starter_yearly': 171 / 36,     # €171/year ÷ 36 generations = €4.75 per gen
    'standard_monthly': 39 / 10,    # €39/month ÷ 10 generations = €3.90 per gen
    'standard_yearly': 351 / 120,   # €351/year ÷ 120 generations = €2.93 per gen
    'pro_monthly': 79 / 25,         # €79/month ÷ 25 generations = €3.16 per gen
    'pro_yearly': 711 / 300,        # €711/year ÷ 300 generations = €2.37 per gen
}

# Minimum charge if service was used (prevents €0.10 charges)
MINIMUM_USAGE_CHARGE = 10.00  # €10 minimum if service used

# Maximum generations allowed for cooling-off refund
MAX_GENERATIONS_FOR_REFUND = 10  # Reasonable testing limit


class RefundService:
    """Service for handling EU-compliant refunds with usage charges."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def is_within_cooling_off_period(self, subscription: Subscription) -> bool:
        """
        Check if subscription is within EU 14-day cooling-off period.
        
        Args:
            subscription: Subscription to check
            
        Returns:
            True if within 14 days of subscription start
        """
        if not subscription.created_at:
            return False
        
        days_since_start = (datetime.utcnow() - subscription.created_at).days
        return days_since_start <= EU_COOLING_OFF_DAYS
    
    def calculate_usage_charge(
        self,
        subscription: Subscription,
        generations_used: int
    ) -> Dict[str, Any]:
        """
        Calculate usage charge for cooling-off period cancellation.
        
        Args:
            subscription: User's subscription
            generations_used: Number of generations created
            
        Returns:
            Dict with calculation breakdown
        """
        plan_type = subscription.plan_type
        
        # Determine billing interval from Stripe
        billing_interval = 'monthly'  # Default
        if subscription.stripe_subscription_id:
            try:
                stripe_sub = stripe.Subscription.retrieve(subscription.stripe_subscription_id)
                if stripe_sub.items.data:
                    interval = stripe_sub.items.data[0].price.recurring.interval
                    billing_interval = 'yearly' if interval == 'year' else 'monthly'
            except Exception as e:
                logger.error(f"Error retrieving billing interval: {e}")
        
        # Get price per generation
        price_key = f"{plan_type}_{billing_interval}"
        price_per_gen = Decimal(str(PRICE_PER_GENERATION.get(price_key, 5.00)))
        
        # Calculate raw usage charge
        raw_usage_charge = price_per_gen * Decimal(str(generations_used))
        
        # Apply minimum charge if service was used
        if generations_used > 0:
            usage_charge = max(Decimal(str(MINIMUM_USAGE_CHARGE)), raw_usage_charge)
        else:
            usage_charge = Decimal('0')
        
        # Check if excessive usage (abuse prevention)
        is_excessive = generations_used > MAX_GENERATIONS_FOR_REFUND
        
        return {
            'generations_used': generations_used,
            'price_per_generation': float(price_per_gen),
            'raw_usage_charge': float(raw_usage_charge),
            'usage_charge': float(usage_charge),
            'minimum_applied': generations_used > 0 and usage_charge == Decimal(str(MINIMUM_USAGE_CHARGE)),
            'is_excessive_usage': is_excessive,
            'billing_interval': billing_interval
        }
    
    def calculate_refund_amount(
        self,
        subscription: Subscription,
        stripe_subscription_id: str
    ) -> Dict[str, Any]:
        """
        Calculate refund amount for cooling-off period cancellation.
        
        Args:
            subscription: User's subscription
            stripe_subscription_id: Stripe subscription ID
            
        Returns:
            Dict with refund calculation details
        """
        # Check if within cooling-off period
        if not self.is_within_cooling_off_period(subscription):
            return {
                'eligible': False,
                'reason': 'outside_cooling_off_period',
                'days_since_start': (datetime.utcnow() - subscription.created_at).days,
                'message': f'Cooling-off period ended. Standard cancellation policy applies.'
            }
        
        # Get total amount paid
        try:
            stripe_sub = stripe.Subscription.retrieve(stripe_subscription_id)
            latest_invoice_id = stripe_sub.latest_invoice
            
            if not latest_invoice_id:
                raise ValueError("No invoice found for subscription")
            
            invoice = stripe.Invoice.retrieve(latest_invoice_id)
            total_paid = Decimal(str(invoice.amount_paid / 100))  # Convert cents to euros
            
        except Exception as e:
            logger.error(f"Error retrieving invoice: {e}")
            raise ValueError(f"Could not retrieve payment information: {e}")
        
        # Count completed generations during subscription
        generations_count = self.db.query(Generation).filter(
            Generation.user_id == subscription.user_id,
            Generation.created_at >= subscription.created_at,
            Generation.status == 'completed'
        ).count()
        
        # Calculate usage charge
        usage_calc = self.calculate_usage_charge(subscription, generations_count)
        usage_charge = Decimal(str(usage_calc['usage_charge']))
        
        # Calculate refund amount
        refund_amount = total_paid - usage_charge
        
        # Ensure refund is not negative
        refund_amount = max(Decimal('0'), refund_amount)
        
        return {
            'eligible': True,
            'total_paid': float(total_paid),
            'generations_used': generations_count,
            'usage_charge': float(usage_charge),
            'refund_amount': float(refund_amount),
            'days_since_start': (datetime.utcnow() - subscription.created_at).days,
            'is_excessive_usage': usage_calc['is_excessive_usage'],
            'calculation_details': usage_calc,
            'message': self._generate_refund_message(
                float(total_paid),
                generations_count,
                float(usage_charge),
                float(refund_amount),
                usage_calc['is_excessive_usage']
            )
        }
    
    def _generate_refund_message(
        self,
        total_paid: float,
        generations: int,
        usage_charge: float,
        refund_amount: float,
        is_excessive: bool
    ) -> str:
        """Generate user-friendly refund message."""
        if generations == 0:
            return f"Full refund of €{total_paid:.2f} (no service usage)."
        
        if is_excessive:
            return (
                f"Refund of €{refund_amount:.2f} from €{total_paid:.2f} paid. "
                f"Usage charge of €{usage_charge:.2f} for {generations} generations "
                f"(exceeds reasonable testing limit of {MAX_GENERATIONS_FOR_REFUND})."
            )
        
        return (
            f"Refund of €{refund_amount:.2f} from €{total_paid:.2f} paid. "
            f"Usage charge of €{usage_charge:.2f} for {generations} generation(s) created."
        )
    
    def process_cooling_off_refund(
        self,
        subscription: Subscription,
        user: User,
        reason: str = "EU 14-day cooling-off period"
    ) -> Dict[str, Any]:
        """
        Process a cooling-off period refund with usage charges.
        
        Args:
            subscription: User's subscription
            user: User requesting refund
            reason: Refund reason
            
        Returns:
            Dict with refund details
        """
        if not subscription.stripe_subscription_id:
            raise ValueError("No Stripe subscription found")
        
        # Calculate refund amount
        refund_calc = self.calculate_refund_amount(subscription, subscription.stripe_subscription_id)
        
        if not refund_calc['eligible']:
            raise ValueError(refund_calc['message'])
        
        refund_amount = refund_calc['refund_amount']
        
        # If refund amount is 0 or negative, just cancel without refund
        if refund_amount <= 0:
            logger.info(f"No refund due for user {user.id}: usage charge exceeds payment")
            # Still cancel the subscription
            self._cancel_subscription_immediately(subscription)
            
            return {
                'refunded': False,
                'refund_amount': 0,
                'usage_charge': refund_calc['usage_charge'],
                'message': 'Subscription canceled. No refund due to service usage.'
            }
        
        # Get the charge to refund
        try:
            stripe_sub = stripe.Subscription.retrieve(subscription.stripe_subscription_id)
            invoice = stripe.Invoice.retrieve(stripe_sub.latest_invoice)
            charge_id = invoice.charge
            
            if not charge_id:
                raise ValueError("No charge found on invoice")
            
            # Issue partial refund
            refund = stripe.Refund.create(
                charge=charge_id,
                amount=int(refund_amount * 100),  # Convert to cents
                reason='requested_by_customer',
                metadata={
                    'cooling_off_period': 'true',
                    'user_id': str(user.id),
                    'generations_used': refund_calc['generations_used'],
                    'usage_charge': refund_calc['usage_charge'],
                    'days_since_start': refund_calc['days_since_start']
                }
            )
            
            logger.info(
                f"✅ Cooling-off refund processed: User {user.id}, "
                f"€{refund_amount:.2f} refunded, "
                f"€{refund_calc['usage_charge']:.2f} usage charge"
            )
            
            # Cancel subscription
            self._cancel_subscription_immediately(subscription)
            
            return {
                'refunded': True,
                'refund_id': refund.id,
                'refund_amount': refund_amount,
                'usage_charge': refund_calc['usage_charge'],
                'generations_used': refund_calc['generations_used'],
                'message': refund_calc['message']
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe refund error: {e}")
            raise ValueError(f"Refund failed: {str(e)}")
    
    def _cancel_subscription_immediately(self, subscription: Subscription) -> None:
        """Cancel subscription immediately and downgrade to free."""
        try:
            # Cancel in Stripe
            if subscription.stripe_subscription_id:
                stripe.Subscription.delete(subscription.stripe_subscription_id)
            
            # Update local database
            from app.core.subscription_plans import get_plan_limits
            subscription.plan_type = 'free'
            subscription.status = 'canceled'
            subscription.stripe_subscription_id = None
            limits = get_plan_limits('free')
            subscription.generations_limit = limits['generations_limit']
            subscription.websites_limit = limits['max_websites']
            subscription.cancel_at_period_end = False
            subscription.updated_at = datetime.utcnow()
            
            self.db.commit()
            logger.info(f"Subscription canceled and downgraded to free")
            
        except Exception as e:
            logger.error(f"Error canceling subscription: {e}")
            raise
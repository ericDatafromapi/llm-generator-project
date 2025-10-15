"""
Refund API endpoints for EU 14-day cooling-off period compliance.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.api.dependencies import get_current_active_user
from app.models.user import User
from app.services.refund import RefundService
from app.services.subscription import SubscriptionService
from app.services.email import email_service

router = APIRouter(prefix="/refunds", tags=["Refunds"])


class CancellationRequest(BaseModel):
    """Request to cancel subscription with cooling-off check."""
    reason: str = "Customer request"
    acknowledge_usage_charge: bool = False


class RefundCalculationResponse(BaseModel):
    """Response showing refund calculation preview."""
    within_cooling_off: bool
    days_since_start: int
    eligible_for_refund: bool
    total_paid: float
    generations_used: int
    usage_charge: float
    refund_amount: float
    is_excessive_usage: bool
    message: str


class CancellationResponse(BaseModel):
    """Response after cancellation."""
    canceled: bool
    refunded: bool
    refund_amount: float
    usage_charge: float
    generations_used: int
    message: str
    refund_id: str = None


@router.get("/calculate", response_model=RefundCalculationResponse)
async def calculate_cooling_off_refund(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Calculate potential refund for cooling-off period cancellation.
    
    Shows user preview of what they'll be charged/refunded before canceling.
    EU-compliant: Must show calculation transparently.
    """
    subscription_service = SubscriptionService(db)
    refund_service = RefundService(db)
    
    subscription = subscription_service.get_user_subscription(current_user.id)
    
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No subscription found"
        )
    
    if subscription.plan_type == 'free':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You are on the free plan. Nothing to cancel."
        )
    
    # Check if within cooling-off period
    within_cooling_off = refund_service.is_within_cooling_off_period(subscription)
    days_since_start = (datetime.utcnow() - subscription.created_at).days if subscription.created_at else 0
    
    if not within_cooling_off:
        return RefundCalculationResponse(
            within_cooling_off=False,
            days_since_start=days_since_start,
            eligible_for_refund=False,
            total_paid=0,
            generations_used=0,
            usage_charge=0,
            refund_amount=0,
            is_excessive_usage=False,
            message=f"Outside 14-day cooling-off period ({days_since_start} days). Use 'Cancel at period end' instead."
        )
    
    # Calculate refund
    try:
        refund_calc = refund_service.calculate_refund_amount(
            subscription,
            subscription.stripe_subscription_id
        )
        
        return RefundCalculationResponse(
            within_cooling_off=True,
            days_since_start=days_since_start,
            eligible_for_refund=refund_calc['eligible'],
            total_paid=refund_calc.get('total_paid', 0),
            generations_used=refund_calc.get('generations_used', 0),
            usage_charge=refund_calc.get('usage_charge', 0),
            refund_amount=refund_calc.get('refund_amount', 0),
            is_excessive_usage=refund_calc.get('is_excessive_usage', False),
            message=refund_calc.get('message', '')
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/cancel-subscription", response_model=CancellationResponse)
async def cancel_subscription_with_cooling_off(
    request: CancellationRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Cancel subscription with EU 14-day cooling-off period handling.
    
    Behavior:
    - Within 14 days: Partial refund (total paid - usage charges)
    - After 14 days: Use Customer Portal for standard cancellation
    
    EU Compliance: User must acknowledge usage charges before cancellation.
    """
    subscription_service = SubscriptionService(db)
    refund_service = RefundService(db)
    
    subscription = subscription_service.get_user_subscription(current_user.id)
    
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No subscription found"
        )
    
    if subscription.plan_type == 'free':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You are on the free plan. Nothing to cancel."
        )
    
    # Check if within cooling-off period
    within_cooling_off = refund_service.is_within_cooling_off_period(subscription)
    
    if not within_cooling_off:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Outside 14-day cooling-off period. Please use the Customer Portal to cancel at period end."
        )
    
    # User must acknowledge usage charges
    if not request.acknowledge_usage_charge:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You must acknowledge that usage charges will be deducted from your refund."
        )
    
    # Process refund
    try:
        result = refund_service.process_cooling_off_refund(
            subscription,
            current_user,
            request.reason
        )
        
        # Send refund confirmation email
        await email_service.send_cooling_off_refund_email(
            to_email=current_user.email,
            user_name=current_user.full_name,
            refund_amount=result['refund_amount'],
            usage_charge=result['usage_charge'],
            generations_used=result['generations_used']
        )
        
        return CancellationResponse(
            canceled=True,
            refunded=result['refunded'],
            refund_amount=result['refund_amount'],
            usage_charge=result['usage_charge'],
            generations_used=result['generations_used'],
            message=result['message'],
            refund_id=result.get('refund_id')
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error processing cooling-off refund: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process refund: {str(e)}"
        )


from datetime import datetime
import logging
logger = logging.getLogger(__name__)
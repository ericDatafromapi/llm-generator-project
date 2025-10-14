"""
Subscription management API endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.rate_limit import limiter
from app.api.dependencies import get_current_active_user
from app.models.user import User
from app.services.subscription import SubscriptionService
from app.schemas.subscription import (
    CheckoutSessionCreate,
    CheckoutSessionResponse,
    CustomerPortalResponse,
    SubscriptionInfo,
    UsageStats,
    PlanInfo
)
from app.core.subscription_plans import PLAN_FEATURES, PlanType

router = APIRouter(prefix="/subscriptions", tags=["Subscriptions"])


@router.get("/plans", response_model=dict)
async def get_available_plans():
    """
    Get all available subscription plans and their features.
    Public endpoint - no authentication required.
    """
    return {
        "plans": {
            plan_type: {
                **plan_data,
                "plan_type": plan_type
            }
            for plan_type, plan_data in PLAN_FEATURES.items()
        }
    }


@router.post("/checkout", response_model=CheckoutSessionResponse)
@limiter.limit("5/minute")  # Prevent double-click and abuse
async def create_checkout_session(
    request: Request,
    data: CheckoutSessionCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Create a Stripe checkout session for subscription purchase.
    
    Rate limited to 5 requests per minute to prevent:
    - Double-click duplicate charges
    - Abuse and spam
    
    The user will be redirected to Stripe to complete payment.
    After successful payment, Stripe will redirect to the success_url.
    """
    try:
        service = SubscriptionService(db)
        return service.create_checkout_session(
            user=current_user,
            plan_type=data.plan_type,
            success_url=data.success_url,
            cancel_url=data.cancel_url
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create checkout session: {str(e)}"
        )


@router.get("/current", response_model=SubscriptionInfo)
async def get_current_subscription(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get current user's subscription information including:
    - Plan type and status
    - Usage statistics
    - Billing period
    - Remaining quota
    """
    try:
        service = SubscriptionService(db)
        return service.get_subscription_info(current_user)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get subscription info: {str(e)}"
        )


@router.get("/usage", response_model=UsageStats)
async def get_usage_statistics(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get current usage statistics for the user:
    - Generations used vs limit
    - Websites count vs limit
    - Current billing period
    """
    try:
        service = SubscriptionService(db)
        return service.get_usage_stats(current_user)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get usage stats: {str(e)}"
        )


@router.post("/portal", response_model=CustomerPortalResponse)
async def create_customer_portal_session(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Create a Stripe Customer Portal session.
    
    The customer portal allows users to:
    - Update payment methods
    - View invoices
    - Update billing information
    - Cancel subscription
    """
    try:
        service = SubscriptionService(db)
        return service.create_customer_portal_session(current_user)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create portal session: {str(e)}"
        )


@router.get("/quota/check")
async def check_generation_quota(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Check if user has available generation quota.
    Returns boolean indicating whether user can create a new generation.
    """
    try:
        service = SubscriptionService(db)
        can_generate = service.check_generation_quota(current_user.id)
        
        if not can_generate:
            subscription_info = service.get_subscription_info(current_user)
            return {
                "can_generate": False,
                "reason": "quota_exceeded",
                "generations_used": subscription_info.generations_used,
                "generations_limit": subscription_info.generations_limit,
                "message": "You have reached your generation limit for this billing period"
            }
        
        return {
            "can_generate": True,
            "message": "Quota available"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check quota: {str(e)}"
        )


@router.get("/website-limit/check")
async def check_website_limit(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Check if user can create more websites.
    Returns boolean indicating whether user can add a new website.
    """
    try:
        service = SubscriptionService(db)
        can_create = service.check_website_limit(current_user.id)
        
        if not can_create:
            usage_stats = service.get_usage_stats(current_user)
            return {
                "can_create": False,
                "reason": "limit_reached",
                "websites_count": usage_stats.websites_count,
                "max_websites": usage_stats.max_websites,
                "message": f"You have reached your website limit ({usage_stats.max_websites} websites)"
            }
        
        return {
            "can_create": True,
            "message": "Can create more websites"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check website limit: {str(e)}"
        )
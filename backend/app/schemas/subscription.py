"""
Subscription-related schemas for request/response models.
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field, field_validator
from app.core.subscription_plans import PlanType


class SubscriptionBase(BaseModel):
    """Base subscription schema."""
    pass


class CheckoutSessionCreate(BaseModel):
    """Schema for creating a Stripe checkout session."""
    plan_type: PlanType = Field(..., description="Plan to subscribe to (standard or pro)")
    success_url: Optional[str] = Field(
        None,
        description="Optional custom success URL",
        json_schema_extra={"example": None}  # Hide from Swagger UI
    )
    cancel_url: Optional[str] = Field(
        None,
        description="Optional custom cancel URL",
        json_schema_extra={"example": None}  # Hide from Swagger UI
    )
    
    @field_validator('success_url', 'cancel_url', mode='before')
    @classmethod
    def validate_url(cls, v):
        """Validate URL or convert invalid values to None."""
        if v is None or v == '' or v == 'string':
            return None
        # Check if it starts with http:// or https://
        if not (v.startswith('http://') or v.startswith('https://')):
            return None
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "plan_type": "standard"
            }
        }


class CheckoutSessionResponse(BaseModel):
    """Response after creating checkout session."""
    checkout_url: str = Field(..., description="Stripe checkout session URL")
    session_id: str = Field(..., description="Stripe session ID")


class CustomerPortalResponse(BaseModel):
    """Response for customer portal link."""
    portal_url: str = Field(..., description="Stripe customer portal URL")


class PlanInfo(BaseModel):
    """Information about a subscription plan."""
    name: str
    price: int
    currency: str
    interval: str
    generations_limit: int
    max_websites: int
    max_pages_per_website: int
    features: List[str]


class SubscriptionInfo(BaseModel):
    """Current subscription information."""
    id: UUID
    user_id: UUID
    plan_type: str
    stripe_customer_id: Optional[str]
    stripe_subscription_id: Optional[str]
    status: str
    current_period_start: Optional[datetime]
    current_period_end: Optional[datetime]
    cancel_at_period_end: bool
    generations_used: int
    generations_limit: int
    max_websites: int
    created_at: datetime
    updated_at: datetime
    
    # Additional computed fields
    remaining_generations: int
    usage_percentage: float
    plan_info: PlanInfo
    
    class Config:
        from_attributes = True


class UsageStats(BaseModel):
    """User usage statistics."""
    current_plan: str
    generations_used: int
    generations_limit: int
    remaining_generations: int
    usage_percentage: float
    websites_count: int
    max_websites: int
    period_start: Optional[datetime]
    period_end: Optional[datetime]


class SubscriptionUpdate(BaseModel):
    """Schema for internal subscription updates (from webhooks)."""
    stripe_subscription_id: Optional[str] = None
    stripe_customer_id: Optional[str] = None
    status: Optional[str] = None
    current_period_start: Optional[datetime] = None
    current_period_end: Optional[datetime] = None
    cancel_at_period_end: Optional[bool] = None
    plan_type: Optional[str] = None


class WebhookEvent(BaseModel):
    """Stripe webhook event data."""
    type: str
    data: Dict[str, Any]
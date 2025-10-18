"""
Subscription plans configuration.
Defines the four tiers: Free, Starter, Standard, and Pro with monthly and yearly billing.
"""
from typing import Dict, Any
from enum import Enum


class PlanType(str, Enum):
    """Subscription plan types."""
    FREE = "free"
    STARTER = "starter"
    STANDARD = "standard"
    PRO = "pro"


class BillingInterval(str, Enum):
    """Billing intervals."""
    MONTHLY = "monthly"
    YEARLY = "yearly"


# Plan Features and Limits
PLAN_FEATURES: Dict[str, Dict[str, Any]] = {
    PlanType.FREE: {
        "name": "Free",
        "price_monthly": 0,
        "price_yearly": 0,
        "currency": "eur",
        "generations_limit": 1,
        "max_websites": 1,
        "max_pages_per_website": 100,
        "features": [
            "1 generation per month",
            "1 website",
            "Up to 100 pages",
            "Basic support",
            "llms.txt files"
        ]
    },
    PlanType.STARTER: {
        "name": "Starter",
        "price_monthly": 19,
        "price_yearly": 171,  # €14.25/month with 25% discount
        "currency": "eur",
        "generations_limit": 3,
        "max_websites": 2,
        "max_pages_per_website": 200,
        "features": [
            "3 generations per month",
            "2 websites",
            "Up to 200 pages",
            "Priority support",
            "llms.txt files",
            "Email notifications"
        ]
    },
    PlanType.STANDARD: {
        "name": "Standard",
        "price_monthly": 39,
        "price_yearly": 351,  # €29.25/month with 25% discount
        "currency": "eur",
        "generations_limit": 10,
        "max_websites": 5,
        "max_pages_per_website": 500,
        "features": [
            "10 generations per month",
            "5 websites",
            "Up to 500 pages per site",
            "Priority support",
            "llms.txt + full content",
            "Automatic updates"
        ]
    },
    PlanType.PRO: {
        "name": "Pro",
        "price_monthly": 79,
        "price_yearly": 711,  # €59.25/month with 25% discount
        "currency": "eur",
        "generations_limit": 25,
        "max_websites": 999,  # "unlimited"
        "max_pages_per_website": 1000,
        "features": [
            "25 generations per month",
            "Unlimited websites",
            "Up to 1000 pages per site",
            "Premium support",
            "llms.txt + full content",
            "Automatic updates",
            "API access"
        ]
    }
}


def get_plan_limits(plan_type: str) -> Dict[str, int]:
    """Get limits for a specific plan."""
    if plan_type not in PLAN_FEATURES:
        plan_type = PlanType.FREE
    
    plan = PLAN_FEATURES[plan_type]
    return {
        "generations_limit": plan["generations_limit"],
        "max_websites": plan["max_websites"],
        "max_pages_per_website": plan["max_pages_per_website"]
    }


def get_plan_info(plan_type: str) -> Dict[str, Any]:
    """Get full information about a plan."""
    if plan_type not in PLAN_FEATURES:
        plan_type = PlanType.FREE
    
    return PLAN_FEATURES[plan_type]


def is_upgrade(current_plan: str, new_plan: str) -> bool:
    """Check if new plan is an upgrade from current."""
    plan_order = [PlanType.FREE, PlanType.STARTER, PlanType.STANDARD, PlanType.PRO]
    try:
        current_idx = plan_order.index(current_plan)
        new_idx = plan_order.index(new_plan)
        return new_idx > current_idx
    except ValueError:
        return False


def get_yearly_discount_percent() -> int:
    """Get the yearly billing discount percentage."""
    return 25  # 25% discount for yearly billing
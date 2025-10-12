"""
Subscription plans configuration.
Defines the three tiers: Free, Standard, and Pro.
"""
from typing import Dict, Any
from enum import Enum


class PlanType(str, Enum):
    """Subscription plan types."""
    FREE = "free"
    STANDARD = "standard"
    PRO = "pro"


# Plan Features and Limits
PLAN_FEATURES: Dict[str, Dict[str, Any]] = {
    PlanType.FREE: {
        "name": "Free",
        "price": 0,
        "currency": "eur",
        "interval": "month",
        "generations_limit": 1,
        "max_websites": 1,
        "max_pages_per_website": 100,
        "features": [
            "1 generation per month",
            "1 website",
            "Up to 100 pages",
            "Basic support"
        ]
    },
    PlanType.STANDARD: {
        "name": "Standard",
        "price": 29,
        "currency": "eur",
        "interval": "month",
        "generations_limit": 10,
        "max_websites": 5,
        "max_pages_per_website": 500,
        "features": [
            "10 generations per month",
            "5 websites",
            "Up to 500 pages per site",
            "Priority support",
            "Email notifications"
        ]
    },
    PlanType.PRO: {
        "name": "Pro",
        "price": 59,
        "currency": "eur",
        "interval": "month",
        "generations_limit": 25,
        "max_websites": 999,  # "unlimited"
        "max_pages_per_website": 1000,
        "features": [
            "25 generations per month",
            "Unlimited websites",
            "Up to 1000 pages per site",
            "Premium support",
            "Advanced analytics",
            "API access",
            "Custom configurations"
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
    plan_order = [PlanType.FREE, PlanType.STANDARD, PlanType.PRO]
    try:
        current_idx = plan_order.index(current_plan)
        new_idx = plan_order.index(new_plan)
        return new_idx > current_idx
    except ValueError:
        return False
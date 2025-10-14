"""
Website API endpoints for managing user websites.
Includes CRUD operations, statistics, and plan-based limits.
"""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, desc, and_
from sqlalchemy.orm import Session
import math
from datetime import datetime, timedelta

from app.core.database import get_db
from app.api.dependencies import get_current_active_user
from app.models.user import User
from app.models.website import Website
from app.models.generation import Generation
from app.models.subscription import Subscription
from app.services.subscription import SubscriptionService
from app.core.subscription_plans import get_plan_limits
from app.schemas.website import (
    WebsiteCreate,
    WebsiteUpdate,
    WebsiteResponse,
    WebsiteListResponse,
    WebsiteStats,
    UserStats
)

router = APIRouter(prefix="/websites", tags=["websites"])


@router.post("", response_model=WebsiteResponse, status_code=201)
def create_website(
    data: WebsiteCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Create a new website configuration.
    
    Enforces plan-based website limits:
    - Free: 1 website
    - Standard: 5 websites
    - Pro: unlimited (999)
    """
    # Get user's subscription
    subscription_service = SubscriptionService(db)
    subscription = subscription_service.get_user_subscription(current_user.id)
    
    if not subscription:
        raise HTTPException(status_code=404, detail="No subscription found")
    
    # Get plan limits
    limits = get_plan_limits(subscription.plan_type)
    max_websites = limits['max_websites']
    
    # Count current websites
    website_count = db.query(func.count(Website.id)).filter(
        Website.user_id == current_user.id
    ).scalar()
    
    if website_count >= max_websites:
        raise HTTPException(
            status_code=403,
            detail=f"Website limit reached. Your {subscription.plan_type} plan allows {max_websites} website{'s' if max_websites != 1 else ''}. Please upgrade your plan to add more websites."
        )
    
    # Check for duplicate URL
    existing = db.query(Website).filter(
        Website.user_id == current_user.id,
        Website.url == data.url
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"You already have a website with URL: {data.url}"
        )
    
    # Enforce max_pages based on plan
    max_pages_limit = limits['max_pages_per_website']
    if data.max_pages > max_pages_limit:
        data.max_pages = max_pages_limit
    
    # Create website
    website = Website(
        user_id=current_user.id,
        url=data.url,
        name=data.name,
        description=data.description,
        include_patterns=data.include_patterns,
        exclude_patterns=data.exclude_patterns,
        max_pages=data.max_pages,
        use_playwright=1 if data.use_playwright else 0,
        timeout=data.timeout,
        is_active=1 if data.is_active else 0
    )
    
    db.add(website)
    
    # Update subscription website count
    subscription.websites_count = website_count + 1
    
    db.commit()
    db.refresh(website)
    
    return website


@router.get("", response_model=WebsiteListResponse)
def list_websites(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get paginated list of user's websites.
    """
    # Build query
    query = db.query(Website).filter(Website.user_id == current_user.id)
    
    # Apply filters
    if is_active is not None:
        query = query.filter(Website.is_active == (1 if is_active else 0))
    
    # Get total count
    total = query.count()
    
    # Calculate pagination
    total_pages = math.ceil(total / per_page) if total > 0 else 1
    
    if page > total_pages and total > 0:
        raise HTTPException(status_code=404, detail="Page not found")
    
    # Get paginated results
    offset = (page - 1) * per_page
    websites = query.order_by(desc(Website.created_at)).offset(offset).limit(per_page).all()
    
    return WebsiteListResponse(
        items=[WebsiteResponse.model_validate(w) for w in websites],
        total=total,
        page=page,
        per_page=per_page,
        pages=total_pages
    )


@router.get("/{website_id}", response_model=WebsiteResponse)
def get_website(
    website_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific website by ID.
    """
    website = db.query(Website).filter(
        Website.id == website_id,
        Website.user_id == current_user.id
    ).first()
    
    if not website:
        raise HTTPException(status_code=404, detail="Website not found")
    
    return website


@router.put("/{website_id}", response_model=WebsiteResponse)
def update_website(
    website_id: UUID,
    data: WebsiteUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update a website configuration.
    """
    website = db.query(Website).filter(
        Website.id == website_id,
        Website.user_id == current_user.id
    ).first()
    
    if not website:
        raise HTTPException(status_code=404, detail="Website not found")
    
    # Get plan limits for max_pages validation
    subscription_service = SubscriptionService(db)
    subscription = subscription_service.get_user_subscription(current_user.id)
    limits = get_plan_limits(subscription.plan_type)
    
    # Update fields if provided
    update_data = data.model_dump(exclude_unset=True)
    
    # Enforce max_pages limit if being updated
    if 'max_pages' in update_data:
        max_pages_limit = limits['max_pages_per_website']
        if update_data['max_pages'] > max_pages_limit:
            update_data['max_pages'] = max_pages_limit
    
    # Handle boolean conversion for use_playwright and is_active
    if 'use_playwright' in update_data:
        update_data['use_playwright'] = 1 if update_data['use_playwright'] else 0
    
    if 'is_active' in update_data:
        update_data['is_active'] = 1 if update_data['is_active'] else 0
    
    # Check for duplicate URL if URL is being changed
    if 'url' in update_data and update_data['url'] != website.url:
        existing = db.query(Website).filter(
            Website.user_id == current_user.id,
            Website.url == update_data['url'],
            Website.id != website_id
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=409,
                detail=f"You already have a website with URL: {update_data['url']}"
            )
    
    # Apply updates
    for key, value in update_data.items():
        setattr(website, key, value)
    
    website.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(website)
    
    return website


@router.delete("/{website_id}")
def delete_website(
    website_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Delete a website and all associated generations.
    """
    website = db.query(Website).filter(
        Website.id == website_id,
        Website.user_id == current_user.id
    ).first()
    
    if not website:
        raise HTTPException(status_code=404, detail="Website not found")
    
    # Check if there are any pending/processing generations
    active_generations = db.query(Generation).filter(
        Generation.website_id == website_id,
        Generation.status.in_(['pending', 'processing'])
    ).first()
    
    if active_generations:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete website with generations in progress. Please wait for them to complete."
        )
    
    # Delete associated generation files
    generations = db.query(Generation).filter(Generation.website_id == website_id).all()
    
    for generation in generations:
        if generation.file_path:
            try:
                import os
                if os.path.exists(generation.file_path):
                    os.remove(generation.file_path)
            except Exception as e:
                # Log but continue
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Failed to delete file {generation.file_path}: {e}")
    
    # Delete website (cascade will delete generations)
    db.delete(website)
    
    # Update subscription website count
    subscription = db.query(Subscription).filter(
        Subscription.user_id == current_user.id
    ).first()
    
    if subscription:
        subscription.websites_count = max(0, subscription.websites_count - 1)
    
    db.commit()
    
    return {"message": "Website deleted successfully"}


@router.get("/{website_id}/stats", response_model=WebsiteStats)
def get_website_stats(
    website_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get statistics for a specific website.
    """
    website = db.query(Website).filter(
        Website.id == website_id,
        Website.user_id == current_user.id
    ).first()
    
    if not website:
        raise HTTPException(status_code=404, detail="Website not found")
    
    # Get generation statistics
    total_generations = db.query(func.count(Generation.id)).filter(
        Generation.website_id == website_id
    ).scalar() or 0
    
    successful_generations = db.query(func.count(Generation.id)).filter(
        Generation.website_id == website_id,
        Generation.status == 'completed'
    ).scalar() or 0
    
    failed_generations = db.query(func.count(Generation.id)).filter(
        Generation.website_id == website_id,
        Generation.status == 'failed'
    ).scalar() or 0
    
    # Get last generation date
    last_generation = db.query(Generation.completed_at).filter(
        Generation.website_id == website_id,
        Generation.status == 'completed'
    ).order_by(desc(Generation.completed_at)).first()
    
    last_generation_at = last_generation[0] if last_generation else None
    
    # Calculate success rate
    success_rate = (successful_generations / total_generations * 100) if total_generations > 0 else 0.0
    
    return WebsiteStats(
        website_id=website.id,
        website_name=website.name or website.url,
        website_url=website.url,
        total_generations=total_generations,
        successful_generations=successful_generations,
        failed_generations=failed_generations,
        last_generation_at=last_generation_at,
        success_rate=round(success_rate, 2)
    )


@router.get("/stats/user", response_model=UserStats)
def get_user_stats(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get overall statistics for the current user.
    """
    # Get subscription info
    subscription_service = SubscriptionService(db)
    subscription = subscription_service.get_user_subscription(current_user.id)
    
    if not subscription:
        raise HTTPException(status_code=404, detail="No subscription found")
    
    # Website counts
    total_websites = db.query(func.count(Website.id)).filter(
        Website.user_id == current_user.id
    ).scalar() or 0
    
    active_websites = db.query(func.count(Website.id)).filter(
        Website.user_id == current_user.id,
        Website.is_active == 1
    ).scalar() or 0
    
    # Generation counts
    total_generations = db.query(func.count(Generation.id)).filter(
        Generation.user_id == current_user.id
    ).scalar() or 0
    
    successful_generations = db.query(func.count(Generation.id)).filter(
        Generation.user_id == current_user.id,
        Generation.status == 'completed'
    ).scalar() or 0
    
    failed_generations = db.query(func.count(Generation.id)).filter(
        Generation.user_id == current_user.id,
        Generation.status == 'failed'
    ).scalar() or 0
    
    # Generations this month (based on current period)
    if subscription.current_period_start:
        generations_this_month = db.query(func.count(Generation.id)).filter(
            Generation.user_id == current_user.id,
            Generation.created_at >= subscription.current_period_start
        ).scalar() or 0
    else:
        # Fallback to calendar month if no period start
        start_of_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        generations_this_month = db.query(func.count(Generation.id)).filter(
            Generation.user_id == current_user.id,
            Generation.created_at >= start_of_month
        ).scalar() or 0
    
    # Remaining generations
    generations_remaining = max(0, subscription.generations_limit - subscription.generations_used)
    
    # Success rate
    success_rate = (successful_generations / total_generations * 100) if total_generations > 0 else 0.0
    
    return UserStats(
        total_websites=total_websites,
        active_websites=active_websites,
        total_generations=total_generations,
        successful_generations=successful_generations,
        failed_generations=failed_generations,
        generations_this_month=generations_this_month,
        generations_remaining=generations_remaining,
        success_rate=round(success_rate, 2)
    )
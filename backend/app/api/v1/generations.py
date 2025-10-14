"""
Generation API endpoints for starting, tracking, and downloading content generations.
"""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy import select, func, desc
from sqlalchemy.orm import Session
import os
import math

from app.core.database import get_db
from app.api.dependencies import get_current_active_user
from app.models.user import User
from app.models.generation import Generation
from app.models.website import Website
from app.services.subscription import SubscriptionService
from app.schemas.generation import (
    GenerationCreate,
    GenerationResponse,
    GenerationListResponse,
    GenerationStartResponse,
    GenerationStatusResponse,
    QuotaCheckResponse
)
from app.tasks.generation import generate_llm_content

router = APIRouter(prefix="/generations", tags=["generations"])


@router.post("/start", response_model=GenerationStartResponse)
def start_generation(
    data: GenerationCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Start a new content generation for a website.
    
    Checks quota before starting and queues the generation task.
    """
    # Check if website exists and belongs to user
    website = db.query(Website).filter(
        Website.id == data.website_id,
        Website.user_id == current_user.id
    ).first()
    
    if not website:
        raise HTTPException(status_code=404, detail="Website not found")
    
    # Check if website is active
    if not website.is_active_bool:
        raise HTTPException(status_code=400, detail="Website is not active")
    
    # Check generation quota
    subscription_service = SubscriptionService(db)
    if not subscription_service.check_generation_quota(current_user.id):
        subscription = subscription_service.get_user_subscription(current_user.id)
        raise HTTPException(
            status_code=403,
            detail=f"Generation limit reached. You have used {subscription.generations_used}/{subscription.generations_limit} generations this month."
        )
    
    # Check if there's already a pending/processing generation for this website
    existing = db.query(Generation).filter(
        Generation.website_id == data.website_id,
        Generation.status.in_(['pending', 'processing'])
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"A generation is already in progress for this website (ID: {existing.id})"
        )
    
    # Create generation record
    generation = Generation(
        user_id=current_user.id,
        website_id=data.website_id,
        status='pending',
        progress_percentage=0,
        pages_crawled=0
    )
    
    db.add(generation)
    db.commit()
    db.refresh(generation)
    
    # Queue Celery task
    task = generate_llm_content.delay(str(generation.id))
    
    # Update with Celery task ID
    generation.celery_task_id = task.id
    db.commit()
    
    return GenerationStartResponse(
        generation_id=generation.id,
        status='pending',
        message='Generation started successfully. You will receive an email when it completes.'
    )


@router.get("/quota/check", response_model=QuotaCheckResponse)
def check_generation_quota(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Check if user has available generation quota.
    """
    subscription_service = SubscriptionService(db)
    subscription = subscription_service.get_user_subscription(current_user.id)
    
    if not subscription:
        raise HTTPException(status_code=404, detail="No subscription found")
    
    can_generate = subscription_service.check_generation_quota(current_user.id)
    remaining = max(0, subscription.generations_limit - subscription.generations_used)
    
    message = (
        f"You have {remaining} generation{'s' if remaining != 1 else ''} remaining this month."
        if can_generate
        else f"Generation limit reached. You have used all {subscription.generations_limit} generations this month."
    )
    
    return QuotaCheckResponse(
        can_generate=can_generate,
        generations_used=subscription.generations_used,
        generations_limit=subscription.generations_limit,
        remaining_generations=remaining,
        message=message
    )


@router.get("/history", response_model=GenerationListResponse)
def get_generation_history(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    website_id: Optional[UUID] = Query(None, description="Filter by website ID"),
    status: Optional[str] = Query(None, description="Filter by status"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get paginated list of user's generations with optional filters.
    """
    # Build query
    query = db.query(Generation).filter(Generation.user_id == current_user.id)
    
    # Apply filters
    if website_id:
        query = query.filter(Generation.website_id == website_id)
    
    if status:
        if status not in ['pending', 'processing', 'completed', 'failed']:
            raise HTTPException(status_code=400, detail="Invalid status filter")
        query = query.filter(Generation.status == status)
    
    # Get total count
    total = query.count()
    
    # Calculate pagination
    total_pages = math.ceil(total / per_page) if total > 0 else 1
    
    if page > total_pages and total > 0:
        raise HTTPException(status_code=404, detail="Page not found")
    
    # Get paginated results
    offset = (page - 1) * per_page
    generations = query.order_by(desc(Generation.created_at)).offset(offset).limit(per_page).all()
    
    return GenerationListResponse(
        items=[GenerationResponse.model_validate(g) for g in generations],
        total=total,
        page=page,
        per_page=per_page,
        pages=total_pages
    )


@router.get("/{generation_id}", response_model=GenerationStatusResponse)
def get_generation_status(
    generation_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get the status of a specific generation.
    """
    generation = db.query(Generation).filter(
        Generation.id == generation_id,
        Generation.user_id == current_user.id
    ).first()
    
    if not generation:
        raise HTTPException(status_code=404, detail="Generation not found")
    
    can_download = (
        generation.status == 'completed' and
        generation.file_path is not None and
        os.path.exists(generation.file_path)
    )
    
    return GenerationStatusResponse(
        id=generation.id,
        status=generation.status,
        progress_percentage=generation.progress_percentage,
        pages_crawled=generation.pages_crawled,
        total_pages=generation.total_pages,
        error_message=generation.error_message,
        created_at=generation.created_at,
        started_at=generation.started_at,
        completed_at=generation.completed_at,
        duration_seconds=float(generation.duration_seconds) if generation.duration_seconds else None,
        can_download=can_download
    )


@router.get("/{generation_id}/download")
def download_generation(
    generation_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Download the generated content file.
    """
    generation = db.query(Generation).filter(
        Generation.id == generation_id,
        Generation.user_id == current_user.id
    ).first()
    
    if not generation:
        raise HTTPException(status_code=404, detail="Generation not found")
    
    if generation.status != 'completed':
        raise HTTPException(
            status_code=400,
            detail=f"Generation is not complete. Current status: {generation.status}"
        )
    
    if not generation.file_path or not os.path.exists(generation.file_path):
        raise HTTPException(
            status_code=404,
            detail="Generated file not found. It may have been deleted."
        )
    
    # Get website for filename
    website = db.query(Website).filter(Website.id == generation.website_id).first()
    
    # Create a clean filename
    website_name = website.name or website.url
    # Remove special characters for filename
    clean_name = "".join(c for c in website_name if c.isalnum() or c in (' ', '-', '_'))
    clean_name = clean_name.replace(' ', '_')[:50]  # Limit length
    
    filename = f"llmready_{clean_name}_{generation.id}.zip"
    
    return FileResponse(
        path=generation.file_path,
        filename=filename,
        media_type='application/zip',
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )


@router.delete("/{generation_id}")
def delete_generation(
    generation_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Delete a generation record and its associated file.
    Can only delete completed or failed generations.
    """
    generation = db.query(Generation).filter(
        Generation.id == generation_id,
        Generation.user_id == current_user.id
    ).first()
    
    if not generation:
        raise HTTPException(status_code=404, detail="Generation not found")
    
    # Don't allow deletion of pending/processing generations
    if generation.status in ['pending', 'processing']:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete a generation that is in progress"
        )
    
    # Delete file if it exists
    if generation.file_path and os.path.exists(generation.file_path):
        try:
            os.remove(generation.file_path)
        except Exception as e:
            # Log error but continue with record deletion
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to delete file {generation.file_path}: {e}")
    
    # Delete database record
    db.delete(generation)
    db.commit()
    
    return {"message": "Generation deleted successfully"}
"""
Pydantic schemas for generation endpoints.
"""
from datetime import datetime
from typing import Optional, List, Literal
from uuid import UUID
from pydantic import BaseModel, Field


class FileRecommendation(BaseModel):
    """Schema for file recommendation."""
    type: Literal["minimal", "standard", "complete"]
    title: str
    description: str
    files: List[str]
    reason: str


class GenerationCreate(BaseModel):
    """Schema for creating a new generation."""
    website_id: UUID = Field(..., description="ID of the website to generate content for")


class GenerationResponse(BaseModel):
    """Schema for generation response."""
    id: UUID
    user_id: UUID
    website_id: UUID
    website_name: Optional[str] = None
    website_url: Optional[str] = None
    status: str
    progress_percentage: int
    pages_crawled: int
    total_pages: Optional[int] = None
    error_message: Optional[str] = None
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    total_files: int
    celery_task_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    recommendation: Optional[FileRecommendation] = None
    
    class Config:
        from_attributes = True


class GenerationListResponse(BaseModel):
    """Schema for paginated generation list."""
    items: List[GenerationResponse]
    total: int
    page: int
    per_page: int
    pages: int


class GenerationStartResponse(BaseModel):
    """Schema for starting a generation."""
    generation_id: UUID
    status: str
    message: str


class GenerationStatusResponse(BaseModel):
    """Schema for generation status check."""
    id: UUID
    status: str
    progress_percentage: int
    pages_crawled: int
    total_pages: Optional[int] = None
    error_message: Optional[str] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    can_download: bool
    recommendation: Optional[FileRecommendation] = None


class QuotaCheckResponse(BaseModel):
    """Schema for quota check response."""
    can_generate: bool
    generations_used: int
    generations_limit: int
    remaining_generations: int
    message: str
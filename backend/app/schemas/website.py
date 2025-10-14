"""
Website schemas for request/response validation.
"""
from pydantic import BaseModel, Field, HttpUrl, validator
from typing import Optional, List
from datetime import datetime
from uuid import UUID


class WebsiteBase(BaseModel):
    """Base website schema with common fields."""
    url: str = Field(..., description="Website URL to crawl")
    name: Optional[str] = Field(None, max_length=255, description="User-friendly name for the website")
    description: Optional[str] = Field(None, description="Optional description of the website")
    include_patterns: Optional[str] = Field(None, description="Comma-separated URL patterns to include (e.g., 'docs,blog,faq')")
    exclude_patterns: Optional[str] = Field(None, description="Comma-separated URL patterns to exclude (e.g., 'login,cart,admin')")
    max_pages: int = Field(100, ge=1, le=1000, description="Maximum number of pages to crawl")
    use_playwright: bool = Field(False, description="Use Playwright for JavaScript rendering")
    timeout: int = Field(300, ge=30, le=3600, description="Timeout in seconds")
    is_active: bool = Field(True, description="Whether the website is active")

    @validator('url')
    def validate_url(cls, v):
        """Ensure URL is valid and has a scheme."""
        if not v:
            raise ValueError("URL cannot be empty")
        
        # Add scheme if missing
        if not v.startswith(('http://', 'https://')):
            v = 'https://' + v
        
        # Basic validation
        if not v.startswith(('http://', 'https://')):
            raise ValueError("URL must start with http:// or https://")
        
        return v.rstrip('/')

    @validator('include_patterns', 'exclude_patterns')
    def validate_patterns(cls, v):
        """Clean up patterns."""
        if v:
            # Remove spaces, ensure lowercase
            return ','.join([p.strip().lower() for p in v.split(',') if p.strip()])
        return v


class WebsiteCreate(WebsiteBase):
    """Schema for creating a new website."""
    pass


class WebsiteUpdate(BaseModel):
    """Schema for updating a website (all fields optional)."""
    url: Optional[str] = Field(None, description="Website URL to crawl")
    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    include_patterns: Optional[str] = None
    exclude_patterns: Optional[str] = None
    max_pages: Optional[int] = Field(None, ge=1, le=1000)
    use_playwright: Optional[bool] = None
    timeout: Optional[int] = Field(None, ge=30, le=3600)
    is_active: Optional[bool] = None

    @validator('url')
    def validate_url(cls, v):
        """Ensure URL is valid if provided."""
        if v:
            if not v.startswith(('http://', 'https://')):
                v = 'https://' + v
            return v.rstrip('/')
        return v

    @validator('include_patterns', 'exclude_patterns')
    def validate_patterns(cls, v):
        """Clean up patterns if provided."""
        if v:
            return ','.join([p.strip().lower() for p in v.split(',') if p.strip()])
        return v


class WebsiteResponse(WebsiteBase):
    """Schema for website response."""
    id: UUID
    user_id: UUID
    last_generated_at: Optional[datetime] = None
    generation_count: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class WebsiteListResponse(BaseModel):
    """Schema for paginated website list."""
    items: List[WebsiteResponse]
    total: int
    page: int
    per_page: int
    pages: int


class WebsiteStats(BaseModel):
    """Statistics for a specific website."""
    website_id: UUID
    website_name: str
    website_url: str
    total_generations: int
    successful_generations: int
    failed_generations: int
    last_generation_at: Optional[datetime]
    success_rate: float  # Percentage


class UserStats(BaseModel):
    """Overall statistics for a user."""
    total_websites: int
    active_websites: int
    total_generations: int
    successful_generations: int
    failed_generations: int
    generations_this_month: int
    generations_remaining: int
    success_rate: float  # Percentage
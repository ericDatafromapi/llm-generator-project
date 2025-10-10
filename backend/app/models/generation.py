"""
Generation model for tracking file generation tasks.
Manages status, progress, and file metadata for each generation.
"""
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime

from app.core.database import Base


class Generation(Base):
    """File generation task model."""
    
    __tablename__ = "generations"
    
    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Foreign Keys
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    website_id = Column(UUID(as_uuid=True), ForeignKey("websites.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Status Tracking (pending, processing, completed, failed)
    status = Column(String(50), default='pending', nullable=False, index=True)
    
    # Progress Tracking
    progress_percentage = Column(Integer, default=0, nullable=False)
    pages_crawled = Column(Integer, default=0, nullable=False)
    total_pages = Column(Integer, nullable=True)
    
    # Error Handling
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0, nullable=False)
    
    # File Metadata
    file_path = Column(String(500), nullable=True)  # Path to generated ZIP file
    file_size = Column(Integer, nullable=True)  # Size in bytes
    total_files = Column(Integer, default=0, nullable=False)  # Number of files in generation
    
    # Celery Task ID (for Week 6)
    celery_task_id = Column(String(255), nullable=True, unique=True, index=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Duration in seconds
    duration_seconds = Column(Numeric(10, 2), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="generations")
    website = relationship("Website", back_populates="generations")
    
    def __repr__(self):
        return f"<Generation(id={self.id}, status={self.status}, website_id={self.website_id})>"
    
    def is_completed(self) -> bool:
        """Check if generation is completed."""
        return self.status == 'completed'
    
    def is_failed(self) -> bool:
        """Check if generation has failed."""
        return self.status == 'failed'
    
    def is_in_progress(self) -> bool:
        """Check if generation is in progress."""
        return self.status in ['pending', 'processing']
"""
Website model for managing user's configured websites.
Stores URL, crawling patterns, and generation limits.
"""
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime

from app.core.database import Base


class Website(Base):
    """Website configuration model."""
    
    __tablename__ = "websites"
    
    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Foreign Key to User
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Website Configuration
    url = Column(String(500), nullable=False)
    name = Column(String(255), nullable=True)  # User-friendly name
    description = Column(Text, nullable=True)
    
    # Crawling Configuration
    include_patterns = Column(Text, nullable=True)  # Comma-separated patterns
    exclude_patterns = Column(Text, nullable=True)  # Comma-separated patterns
    max_pages = Column(Integer, default=100, nullable=False)
    use_playwright = Column(Integer, default=0, nullable=False)  # 0=False, 1=True (for SQLite compatibility)
    timeout = Column(Integer, default=300, nullable=False)  # seconds
    
    # Metadata
    is_active = Column(Integer, default=1, nullable=False)  # 0=False, 1=True
    last_generated_at = Column(DateTime, nullable=True)
    generation_count = Column(Integer, default=0, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="websites")
    generations = relationship("Generation", back_populates="website", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Website(id={self.id}, url={self.url}, user_id={self.user_id})>"
    
    @property
    def is_active_bool(self) -> bool:
        """Return is_active as boolean."""
        return bool(self.is_active)
    
    @property
    def use_playwright_bool(self) -> bool:
        """Return use_playwright as boolean."""
        return bool(self.use_playwright)
"""
StripeEvent model for tracking processed webhook events.
Provides persistent idempotency and prevents duplicate event processing.
"""
from sqlalchemy import Column, String, Integer, DateTime, Text
from datetime import datetime

from app.core.database import Base


class StripeEvent(Base):
    """Model for tracking processed Stripe webhook events."""
    
    __tablename__ = "stripe_events"
    
    # Primary Key - Stripe event ID
    id = Column(String(255), primary_key=True, index=True)
    
    # Event details
    type = Column(String(100), nullable=False, index=True)
    created = Column(Integer, nullable=False, index=True)  # Stripe timestamp
    
    # Processing status
    status = Column(String(50), default="processed", nullable=False)  # processed, failed
    processed_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Error tracking (if processing failed)
    error_message = Column(Text, nullable=True)
    
    def __repr__(self):
        return f"<StripeEvent(id={self.id}, type={self.type}, status={self.status})>"
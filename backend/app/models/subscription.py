"""
Subscription model for managing user plans and billing.
Integrates with Stripe for payment processing.
"""
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Boolean, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime

from app.core.database import Base


class Subscription(Base):
    """User subscription and billing model."""
    
    __tablename__ = "subscriptions"
    
    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Foreign Key to User
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    
    # Subscription Plan (free, standard, pro)
    plan_type = Column(String(50), default='free', nullable=False)
    
    # Stripe Integration
    stripe_customer_id = Column(String(255), nullable=True, unique=True, index=True)
    stripe_subscription_id = Column(String(255), nullable=True, unique=True, index=True)
    stripe_price_id = Column(String(255), nullable=True)
    
    # Subscription Status (active, canceled, past_due, incomplete)
    status = Column(String(50), default='active', nullable=False)
    
    # Usage Tracking
    generations_used = Column(Integer, default=0, nullable=False)
    generations_limit = Column(Integer, default=1, nullable=False)  # free: 1, standard: 10, pro: 25
    
    # Websites Tracking
    websites_count = Column(Integer, default=0, nullable=False)
    websites_limit = Column(Integer, default=1, nullable=False)  # free: 1, standard: 5, pro: 999
    
    # Billing
    current_period_start = Column(DateTime, nullable=True)
    current_period_end = Column(DateTime, nullable=True)
    cancel_at_period_end = Column(Boolean, default=False, nullable=False)
    
    # Pricing
    amount = Column(Numeric(10, 2), default=0.00, nullable=False)  # Monthly amount in EUR
    currency = Column(String(3), default='EUR', nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    canceled_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="subscription")
    
    def __repr__(self):
        return f"<Subscription(id={self.id}, user_id={self.user_id}, plan={self.plan_type}, status={self.status})>"
    
    def has_generations_remaining(self) -> bool:
        """Check if user has generation credits remaining."""
        return self.generations_used < self.generations_limit
    
    def can_add_website(self) -> bool:
        """Check if user can add more websites."""
        return self.websites_count < self.websites_limit
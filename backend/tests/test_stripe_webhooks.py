"""
Comprehensive tests for Stripe webhook implementation.
Tests all P0 and P1 fixes from the audit report.
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from uuid import uuid4

from app.api.v1.webhooks import (
    is_event_processed,
    should_process_event,
    mark_event_processed,
    mark_event_failed,
    handle_checkout_session_completed,
    handle_subscription_updated,
    handle_subscription_deleted,
    handle_payment_failed,
    handle_payment_succeeded,
    handle_charge_disputed,
    handle_charge_refunded,
    handle_payment_action_required,
    handle_customer_deleted
)
from app.models.stripe_event import StripeEvent
from app.models.subscription import Subscription
from app.models.user import User


class TestWebhookIdempotency:
    """Test P0 Fix #1: Persistent webhook idempotency"""
    
    def test_is_event_processed_returns_false_for_new_event(self, db_session):
        """New events should not be marked as processed"""
        event_id = "evt_test_123"
        assert is_event_processed(db_session, event_id) == False
    
    def test_is_event_processed_returns_true_for_existing_event(self, db_session):
        """Processed events should be detected"""
        event_id = "evt_test_456"
        event = StripeEvent(
            id=event_id,
            type="invoice.payment_succeeded",
            created=int(datetime.utcnow().timestamp()),
            status="processed"
        )
        db_session.add(event)
        db_session.commit()
        
        assert is_event_processed(db_session, event_id) == True
    
    def test_mark_event_processed_creates_record(self, db_session):
        """Marking event as processed should create database record"""
        event_id = "evt_test_789"
        event_type = "checkout.session.completed"
        event_created = int(datetime.utcnow().timestamp())
        
        mark_event_processed(db_session, event_id, event_type, event_created)
        
        event = db_session.query(StripeEvent).filter(StripeEvent.id == event_id).first()
        assert event is not None
        assert event.type == event_type
        assert event.status == "processed"
        assert event.created == event_created


class TestEventOrdering:
    """Test P0 Fix #8: Event ordering logic"""
    
    def test_should_process_event_allows_new_events(self, db_session):
        """New events should be allowed to process"""
        event_id = "evt_new_123"
        event_type = "customer.subscription.updated"
        event_created = int(datetime.utcnow().timestamp())
        
        assert should_process_event(db_session, event_id, event_type, event_created) == True
    
    def test_should_process_event_rejects_old_events(self, db_session):
        """Old events should be rejected if newer one already processed"""
        event_type = "customer.subscription.updated"
        
        # Process newer event first
        newer_event_id = "evt_newer_123"
        newer_created = int(datetime.utcnow().timestamp())
        mark_event_processed(db_session, newer_event_id, event_type, newer_created)
        
        # Try to process older event
        older_event_id = "evt_older_123"
        older_created = newer_created - 3600  # 1 hour earlier
        
        result = should_process_event(db_session, older_event_id, event_type, older_created)
        assert result == False
    
    def test_should_process_event_rejects_duplicate(self, db_session):
        """Already processed events should be rejected"""
        event_id = "evt_duplicate_123"
        event_type = "invoice.payment_failed"
        event_created = int(datetime.utcnow().timestamp())
        
        mark_event_processed(db_session, event_id, event_type, event_created)
        
        result = should_process_event(db_session, event_id, event_type, event_created)
        assert result == False


class TestErrorHandling:
    """Test P0 Fix #2: Webhook error handling returns 200"""
    
    def test_mark_event_failed_stores_error(self, db_session):
        """Failed events should be logged with error message"""
        event_id = "evt_failed_123"
        event_type = "charge.refunded"
        event_created = int(datetime.utcnow().timestamp())
        error_message = "Database connection failed"
        
        mark_event_failed(db_session, event_id, event_type, event_created, error_message)
        
        event = db_session.query(StripeEvent).filter(StripeEvent.id == event_id).first()
        assert event is not None
        assert event.status == "failed"
        assert event.error_message == error_message


class TestPaymentSuccessHandler:
    """Test P0 Fix #3: Payment success handler"""
    
    @patch('app.services.email.send_payment_success_email')
    def test_handle_payment_succeeded_activates_subscription(self, mock_email, db_session):
        """Payment success should activate subscription"""
        user = User(
            id=uuid4(),
            email="test@example.com",
            password_hash="hash",
            full_name="Test User"
        )
        db_session.add(user)
        
        subscription = Subscription(
            user_id=user.id,
            plan_type="standard",
            stripe_subscription_id="sub_123",
            status="incomplete",
            generations_limit=10,
            websites_limit=5
        )
        db_session.add(subscription)
        db_session.commit()
        
        event_data = {
            "subscription": "sub_123",
            "amount_paid": 1500  # $15.00 in cents
        }
        
        handle_payment_succeeded(event_data, db_session)
        
        db_session.refresh(subscription)
        assert subscription.status == "active"
        assert mock_email.called


class TestGracePeriod:
    """Test P0 Fix #4: Subscription status enforcement with grace period"""
    
    def test_grace_period_allows_past_due_within_limit(self, db_session):
        """Past due subscriptions within grace period should work"""
        from app.services.subscription import SubscriptionService
        
        user_id = uuid4()
        user = User(id=user_id, email="test@example.com", password_hash="hash")
        db_session.add(user)
        
        # Create past_due subscription updated 2 days ago (within 3-day grace)
        subscription = Subscription(
            user_id=user_id,
            plan_type="standard",
            status="past_due",
            generations_used=5,
            generations_limit=10,
            websites_limit=5,
            updated_at=datetime.utcnow() - timedelta(days=2)
        )
        db_session.add(subscription)
        db_session.commit()
        
        service = SubscriptionService(db_session)
        can_generate = service.check_generation_quota(user_id)
        
        assert can_generate == True
    
    def test_grace_period_blocks_past_due_beyond_limit(self, db_session):
        """Past due subscriptions beyond grace period should be blocked"""
        from app.services.subscription import SubscriptionService
        
        user_id = uuid4()
        user = User(id=user_id, email="test@example.com", password_hash="hash")
        db_session.add(user)
        
        # Create past_due subscription updated 4 days ago (beyond 3-day grace)
        subscription = Subscription(
            user_id=user_id,
            plan_type="standard",
            status="past_due",
            generations_used=5,
            generations_limit=10,
            websites_limit=5,
            updated_at=datetime.utcnow() - timedelta(days=4)
        )
        db_session.add(subscription)
        db_session.commit()
        
        service = SubscriptionService(db_session)
        can_generate = service.check_generation_quota(user_id)
        
        assert can_generate == False


class TestChargebackHandler:
    """Test P0 Fix #5: Chargeback/dispute handling"""
    
    @patch('app.services.email.send_chargeback_email')
    def test_handle_charge_disputed_revokes_access(self, mock_email, db_session):
        """Chargeback should immediately revoke access"""
        user = User(id=uuid4(), email="test@example.com", password_hash="hash", full_name="Test User")
        db_session.add(user)
        
        subscription = Subscription(
            user_id=user.id,
            plan_type="pro",
            stripe_customer_id="cus_123",
            status="active",
            generations_limit=25,
            websites_limit=999
        )
        db_session.add(subscription)
        db_session.commit()
        
        event_data = {
            "customer": "cus_123",
            "amount": 2500  # $25.00
        }
        
        handle_charge_disputed(event_data, db_session)
        
        db_session.refresh(subscription)
        assert subscription.status == "canceled"
        assert subscription.plan_type == "free"
        assert mock_email.called


class TestRefundHandler:
    """Test P0 Fix #7: Refund handling"""
    
    @patch('app.services.email.send_refund_email')
    def test_handle_charge_refunded_downgrades_account(self, mock_email, db_session):
        """Full refund should downgrade to free"""
        user = User(id=uuid4(), email="test@example.com", password_hash="hash", full_name="Test User")
        db_session.add(user)
        
        subscription = Subscription(
            user_id=user.id,
            plan_type="standard",
            stripe_customer_id="cus_456",
            status="active",
            generations_limit=10,
            websites_limit=5
        )
        db_session.add(subscription)
        db_session.commit()
        
        event_data = {
            "customer": "cus_456",
            "amount_refunded": 1500,
            "refunded": True  # Full refund
        }
        
        handle_charge_refunded(event_data, db_session)
        
        db_session.refresh(subscription)
        assert subscription.plan_type == "free"
        assert subscription.status == "canceled"
        assert mock_email.called


class TestQuotaOverflow:
    """Test P1 Fix #12: Downgrade quota overflow handling"""
    
    def test_downgrade_with_quota_overflow_caps_usage(self, db_session):
        """Downgrading with usage over limit should cap at new limit"""
        user = User(id=uuid4(), email="test@example.com", password_hash="hash")
        db_session.add(user)
        
        # User on Pro (25 generations) has used 15
        subscription = Subscription(
            user_id=user.id,
            plan_type="pro",
            stripe_subscription_id="sub_789",
            status="active",
            generations_used=15,
            generations_limit=25,
            websites_limit=999
        )
        db_session.add(subscription)
        db_session.commit()
        
        # Simulate downgrade to Standard (10 generations)
        event_data = {
            "id": "sub_789",
            "status": "active",
            "items": {
                "data": [{
                    "price": {"id": "price_standard_id"}
                }]
            },
            "current_period_start": int(datetime.utcnow().timestamp()),
            "current_period_end": int((datetime.utcnow() + timedelta(days=30)).timestamp()),
            "cancel_at_period_end": False
        }
        
        with patch('app.core.config.settings.STRIPE_PRICE_STANDARD', 'price_standard_id'):
            handle_subscription_updated(event_data, db_session)
        
        db_session.refresh(subscription)
        assert subscription.plan_type == "standard"
        assert subscription.generations_limit == 10
        # Usage should be capped at new limit
        assert subscription.generations_used == 10


# Pytest fixtures
@pytest.fixture
def db_session():
    """Mock database session for testing"""
    from unittest.mock import MagicMock
    session = MagicMock()
    session.query.return_value.filter.return_value.first.return_value = None
    return session


if __name__ == "__main__":
    print("✅ Stripe webhook tests defined")
    print("Run with: pytest backend/tests/test_stripe_webhooks.py -v")
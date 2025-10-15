"""
Comprehensive test runner for Stripe implementation
"""
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 70)
print("🧪 STRIPE IMPLEMENTATION TEST SUITE")
print("=" * 70)

# Test 1: Import Check
print("\n📦 TEST 1: Module Imports")
print("-" * 70)
try:
    from app.models.stripe_event import StripeEvent
    print("✅ StripeEvent model imported")
    
    from app.api.v1.webhooks import (
        is_event_processed,
        should_process_event,
        mark_event_processed,
        handle_payment_succeeded,
        handle_charge_disputed,
        handle_charge_refunded
    )
    print("✅ Webhook handlers imported")
    
    from app.services.email import (
        send_payment_success_email,
        send_payment_failed_email,
        send_chargeback_email,
        send_refund_email
    )
    print("✅ Email functions imported")
    
    from app.services.subscription import SubscriptionService
    print("✅ SubscriptionService imported")
    
    from app.tasks.scheduled import sync_stripe_subscriptions
    print("✅ Sync task imported")
    
    print("\n✅ All imports successful!")
    
except Exception as e:
    print(f"\n❌ Import error: {e}")
    sys.exit(1)

# Test 2: Model Structure
print("\n🗄️  TEST 2: StripeEvent Model Structure")
print("-" * 70)
try:
    required_fields = ['id', 'type', 'created', 'status', 'processed_at', 'error_message']
    for field in required_fields:
        if hasattr(StripeEvent, field):
            print(f"✅ Field '{field}' exists")
        else:
            print(f"❌ Field '{field}' missing")
            raise ValueError(f"Missing field: {field}")
    
    print("\n✅ Model structure correct!")
    
except Exception as e:
    print(f"\n❌ Model error: {e}")
    sys.exit(1)

# Test 3: Service Methods
print("\n💳 TEST 3: SubscriptionService Methods")
print("-" * 70)
try:
    methods = [
        'check_generation_quota',
        'upgrade_subscription',
        'cancel_user_subscription_on_deletion'
    ]
    
    for method in methods:
        if hasattr(SubscriptionService, method):
            print(f"✅ Method '{method}' exists")
        else:
            print(f"❌ Method '{method}' missing")
            raise ValueError(f"Missing method: {method}")
    
    print("\n✅ All service methods present!")
    
except Exception as e:
    print(f"\n❌ Service error: {e}")
    sys.exit(1)

# Test 4: Database Connection
print("\n🔌 TEST 4: Database Connection")
print("-" * 70)
try:
    from app.core.database import engine
    from sqlalchemy import text
    
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        if result.fetchone()[0] == 1:
            print("✅ Database connection successful")
        else:
            raise Exception("Query failed")
    
    print("\n✅ Database connection working!")
    
except Exception as e:
    print(f"\n❌ Database error: {e}")
    print("⚠️  Make sure PostgreSQL is running")
    sys.exit(1)

# Test 5: Check Migration Files
print("\n📝 TEST 5: Migration Files")
print("-" * 70)
try:
    import os
    migrations_dir = "alembic/versions"
    if os.path.exists(migrations_dir):
        files = [f for f in os.listdir(migrations_dir) if f.endswith('.py') and f != '__pycache__']
        print(f"✅ Found {len(files)} migration files")
        
        has_stripe_events = any('stripe_events' in f for f in files)
        if has_stripe_events:
            print("✅ stripe_events migration exists")
        else:
            print("⚠️  stripe_events migration not found (may need to create)")
    else:
        print("❌ Migrations directory not found")
    
    print("\n✅ Migration check complete!")
    
except Exception as e:
    print(f"\n❌ Migration check error: {e}")

# Test 6: Rate Limiting Setup
print("\n🚦 TEST 6: Rate Limiting Configuration")
print("-" * 70)
try:
    with open('app/api/v1/subscriptions.py', 'r') as f:
        content = f.read()
        has_limiter = 'from app.core.rate_limit import limiter' in content
        has_decorator = '@limiter.limit' in content
        
        if has_limiter:
            print("✅ Rate limiter imported")
        else:
            print("❌ Rate limiter not imported")
        
        if has_decorator:
            print("✅ Rate limit decorator applied")
        else:
            print("❌ Rate limit decorator not applied")
    
    if has_limiter and has_decorator:
        print("\n✅ Rate limiting configured!")
    else:
        print("\n⚠️  Rate limiting incomplete")
    
except Exception as e:
    print(f"\n❌ Rate limiting check error: {e}")

# Test 7: Environment Variables
print("\n🔐 TEST 7: Environment Variables")
print("-" * 70)
try:
    from app.core.config import settings
    
    required_vars = [
        ('STRIPE_SECRET_KEY', settings.STRIPE_SECRET_KEY),
        ('STRIPE_WEBHOOK_SECRET', settings.STRIPE_WEBHOOK_SECRET),
        ('SENDGRID_API_KEY', settings.SENDGRID_API_KEY),
        ('DATABASE_URL', settings.DATABASE_URL),
    ]
    
    for var_name, var_value in required_vars:
        if var_value and var_value != "":
            # Mask sensitive data
            if 'KEY' in var_name or 'SECRET' in var_name:
                display_value = f"{str(var_value)[:10]}...{str(var_value)[-4:]}"
            else:
                display_value = str(var_value)[:50]
            print(f"✅ {var_name}: {display_value}")
        else:
            print(f"⚠️  {var_name}: Not set")
    
    print("\n✅ Environment check complete!")
    
except Exception as e:
    print(f"\n❌ Environment error: {e}")

# Final Summary
print("\n" + "=" * 70)
print("📊 TEST SUMMARY")
print("=" * 70)
print("\n✅ All critical tests passed!")
print("\n🎯 Next Steps:")
print("   1. Apply migration: alembic upgrade head")
print("   2. Start services:")
print("      - FastAPI: uvicorn app.main:app --reload")
print("      - Celery: celery -A app.core.celery_app worker --loglevel=info")
print("      - Beat: celery -A app.core.celery_app beat --loglevel=info")
print("   3. Test with Stripe CLI: stripe trigger <event_type>")
print("   4. Check stripe_events table for processed events")
print("\n" + "=" * 70)
print("🎉 Implementation ready for testing!")
print("=" * 70)
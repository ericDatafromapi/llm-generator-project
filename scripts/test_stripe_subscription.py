#!/usr/bin/env python3
"""
Test Stripe Subscription Workflow on Production Server
Tests the complete subscription flow including webhooks simulation
"""
import os
import sys
import json

# Add backend to path
sys.path.insert(0, '/opt/llmready/backend')

from app.core.database import SessionLocal
from app.models.user import User
from app.models.subscription import Subscription
from app.services.subscription import SubscriptionService
from app.core.subscription_plans import get_plan_limits, PLAN_FEATURES
import stripe
from app.core.config import settings

# Configure Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY

def log(message, status="INFO"):
    """Log with colors"""
    colors = {
        "INFO": "\033[0;36m",  # Cyan
        "SUCCESS": "\033[0;32m",  # Green
        "ERROR": "\033[0;31m",  # Red
        "WARNING": "\033[1;33m",  # Yellow
    }
    reset = "\033[0m"
    print(f"{colors.get(status, '')}{status}: {message}{reset}")

def test_stripe_connection():
    """Test Stripe API connectivity"""
    log("\n=== Testing Stripe Connection ===", "INFO")
    
    try:
        # Try to list products
        products = stripe.Product.list(limit=3)
        log(f"Connected to Stripe successfully", "SUCCESS")
        log(f"Found {len(products.data)} products", "INFO")
        return True
    except stripe._error.AuthenticationError as e:
        log(f"Stripe authentication failed: {e}", "ERROR")
        log("Check STRIPE_SECRET_KEY in .env", "WARNING")
        return False
    except Exception as e:
        log(f"Stripe connection error: {e}", "ERROR")
        return False

def test_stripe_prices():
    """Test if all required Stripe prices exist"""
    log("\n=== Testing Stripe Price Configuration ===", "INFO")
    
    price_ids = {
        "STARTER_MONTHLY": getattr(settings, 'STRIPE_PRICE_STARTER_MONTHLY', None),
        "STARTER_YEARLY": getattr(settings, 'STRIPE_PRICE_STARTER_YEARLY', None),
        "STANDARD_MONTHLY": getattr(settings, 'STRIPE_PRICE_STANDARD_MONTHLY', None),
        "STANDARD_YEARLY": getattr(settings, 'STRIPE_PRICE_STANDARD_YEARLY', None),
        "PRO_MONTHLY": getattr(settings, 'STRIPE_PRICE_PRO_MONTHLY', None),
        "PRO_YEARLY": getattr(settings, 'STRIPE_PRICE_PRO_YEARLY', None),
    }
    
    all_configured = True
    for name, price_id in price_ids.items():
        if price_id:
            try:
                price = stripe.Price.retrieve(price_id)
                log(f"✅ {name}: {price_id} ({price.currency.upper()} {price.unit_amount/100})", "SUCCESS")
            except stripe._error.InvalidRequestError:
                log(f"❌ {name}: {price_id} (NOT FOUND IN STRIPE)", "ERROR")
                all_configured = False
        else:
            log(f"❌ {name}: NOT CONFIGURED in .env", "ERROR")
            all_configured = False
    
    return all_configured

def test_webhook_endpoint():
    """Test if webhook endpoint is configured"""
    log("\n=== Testing Webhook Configuration ===", "INFO")
    
    if not settings.STRIPE_WEBHOOK_SECRET:
        log("STRIPE_WEBHOOK_SECRET not configured", "ERROR")
        return False
    
    log(f"Webhook secret configured: {settings.STRIPE_WEBHOOK_SECRET[:12]}...", "SUCCESS")
    
    # List webhooks
    try:
        webhooks = stripe.WebhookEndpoint.list(limit=10)
        log(f"Found {len(webhooks.data)} webhook endpoints", "INFO")
        
        for webhook in webhooks.data:
            log(f"  URL: {webhook.url}", "INFO")
            log(f"  Status: {webhook.status}", "INFO")
            log(f"  Events: {', '.join(webhook.enabled_events[:5])}...", "INFO")
        
        return True
    except Exception as e:
        log(f"Error listing webhooks: {e}", "ERROR")
        return False

def test_subscription_database():
    """Test subscription data in database"""
    log("\n=== Testing Subscription Database ===", "INFO")
    
    db = SessionLocal()
    try:
        # Get all subscriptions
        subscriptions = db.query(Subscription).all()
        log(f"Total subscriptions: {len(subscriptions)}", "INFO")
        
        # Show subscription breakdown
        plan_counts = {}
        status_counts = {}
        
        for sub in subscriptions:
            plan_counts[sub.plan_type] = plan_counts.get(sub.plan_type, 0) + 1
            status_counts[sub.status] = status_counts.get(sub.status, 0) + 1
        
        log("\nBy Plan Type:", "INFO")
        for plan, count in plan_counts.items():
            log(f"  {plan}: {count}", "INFO")
        
        log("\nBy Status:", "INFO")
        for status, count in status_counts.items():
            log(f"  {status}: {count}", "INFO")
        
        # Show recent subscriptions
        recent_subs = db.query(Subscription).order_by(Subscription.created_at.desc()).limit(5).all()
        
        if recent_subs:
            log("\nRecent Subscriptions:", "INFO")
            for sub in recent_subs:
                user = db.query(User).filter(User.id == sub.user_id).first()
                log(f"  User: {user.email if user else 'Unknown'}", "INFO")
                log(f"    Plan: {sub.plan_type}", "INFO")
                log(f"    Status: {sub.status}", "INFO")
                log(f"    Usage: {sub.generations_used}/{sub.generations_limit}", "INFO")
                if sub.stripe_customer_id:
                    log(f"    Stripe Customer: {sub.stripe_customer_id}", "INFO")
                if sub.stripe_subscription_id:
                    log(f"    Stripe Subscription: {sub.stripe_subscription_id}", "INFO")
        
        return True
        
    except Exception as e:
        log(f"Database error: {e}", "ERROR")
        return False
    finally:
        db.close()

def test_subscription_service():
    """Test subscription service functionality"""
    log("\n=== Testing Subscription Service ===", "INFO")
    
    db = SessionLocal()
    try:
        service = SubscriptionService(db)
        
        # Get a test user
        user = db.query(User).first()
        
        if not user:
            log("No users in database to test with", "WARNING")
            return False
        
        log(f"Testing with user: {user.email}", "INFO")
        
        # Test get subscription
        try:
            sub_info = service.get_subscription_info(user)
            log(f"✅ Get subscription info works", "SUCCESS")
            log(f"  Plan: {sub_info.plan_type}", "INFO")
            log(f"  Status: {sub_info.status}", "INFO")
            log(f"  Usage: {sub_info.generations_used}/{sub_info.generations_limit}", "INFO")
        except Exception as e:
            log(f"❌ Get subscription info failed: {e}", "ERROR")
            return False
        
        # Test usage stats
        try:
            stats = service.get_usage_stats(user)
            log(f"✅ Get usage stats works", "SUCCESS")
            log(f"  Websites: {stats.websites_count}/{stats.max_websites}", "INFO")
            log(f"  Generations: {stats.generations_used}/{stats.generations_limit}", "INFO")
        except Exception as e:
            log(f"❌ Get usage stats failed: {e}", "ERROR")
            return False
        
        # Test quota check
        try:
            can_generate = service.check_generation_quota(user.id)
            log(f"✅ Check generation quota works: {can_generate}", "SUCCESS")
        except Exception as e:
            log(f"❌ Check generation quota failed: {e}", "ERROR")
            return False
        
        return True
        
    except Exception as e:
        log(f"Service test error: {e}", "ERROR")
        return False
    finally:
        db.close()

def test_plan_configuration():
    """Test plan configuration"""
    log("\n=== Testing Plan Configuration ===", "INFO")
    
    plans = ['free', 'starter', 'standard', 'pro']
    
    for plan in plans:
        try:
            limits = get_plan_limits(plan)
            features = PLAN_FEATURES.get(plan, {})
            
            log(f"\n{plan.upper()} Plan:", "INFO")
            log(f"  Generations: {limits.get('generations_limit', 'N/A')}", "INFO")
            log(f"  Websites: {limits.get('max_websites', 'N/A')}", "INFO")
            log(f"  Max Pages: {limits.get('max_pages', 'N/A')}", "INFO")
            log(f"  Features: {len(features.get('features', []))}", "INFO")
            
        except Exception as e:
            log(f"Error getting plan {plan}: {e}", "ERROR")
            return False
    
    return True

def simulate_checkout(user_email: str = None):
    """Simulate a checkout process"""
    log("\n=== Simulating Checkout Process ===", "INFO")
    
    if not user_email:
        log("No user email provided for simulation", "WARNING")
        return False
    
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == user_email).first()
        
        if not user:
            log(f"User {user_email} not found", "ERROR")
            return False
        
        service = SubscriptionService(db)
        
        log(f"Creating checkout session for {user.email}...", "INFO")
        log("Plan: standard, Billing: monthly", "INFO")
        
        try:
            result = service.create_checkout_session(
                user=user,
                plan_type='standard',
                billing_interval='monthly',
                success_url='http://localhost/success',
                cancel_url='http://localhost/cancel'
            )
            
            log(f"✅ Checkout session created!", "SUCCESS")
            log(f"  Session ID: {result.session_id}", "INFO")
            log(f"  Checkout URL: {result.checkout_url[:50]}...", "INFO")
            
            return True
            
        except Exception as e:
            log(f"❌ Checkout creation failed: {e}", "ERROR")
            return False
        
    finally:
        db.close()

def main():
    """Run all Stripe/subscription tests"""
    print("\n" + "="*60)
    print("💳 LLMReady Stripe Subscription Test (Production)")
    print("="*60 + "\n")
    
    results = {
        "stripe_connection": test_stripe_connection(),
        "stripe_prices": test_stripe_prices(),
        "webhook_config": test_webhook_endpoint(),
        "database": test_subscription_database(),
        "service": test_subscription_service(),
        "plan_config": test_plan_configuration(),
    }
    
    # Ask if user wants to test checkout
    print("\n" + "="*60)
    log("Would you like to test checkout session creation?", "INFO")
    log("This will create a test Stripe checkout session.", "WARNING")
    response = input("Enter user email to test (or press Enter to skip): ").strip()
    
    if response:
        results["checkout_simulation"] = simulate_checkout(response)
    
    # Summary
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name.upper()}: {status}")
    
    all_passed = all(results.values())
    
    if all_passed:
        print("\n🎉 All tests passed! Stripe integration is working.")
    else:
        print("\n⚠️  Some tests failed. Review errors above.")
        
        # Provide recommendations
        print("\n💡 Recommendations:")
        if not results.get("stripe_connection"):
            print("  1. Check STRIPE_SECRET_KEY in /opt/llmready/backend/.env")
        if not results.get("stripe_prices"):
            print("  2. Configure all Stripe price IDs in .env")
        if not results.get("webhook_config"):
            print("  3. Set up Stripe webhook with STRIPE_WEBHOOK_SECRET")
        if not results.get("database"):
            print("  4. Check database connection")
    
    print("="*60 + "\n")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
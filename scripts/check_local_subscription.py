#!/usr/bin/env python3
"""
Check local database subscription state
"""
import sys
sys.path.insert(0, 'backend')

from app.core.database import SessionLocal
from app.models.subscription import Subscription
from app.models.user import User

db = SessionLocal()

print("="*60)
print("📊 Local Subscription Status")
print("="*60)
print("")

users = db.query(User).all()

if not users:
    print("❌ No users found in database")
else:
    for user in users:
        print(f"User: {user.email}")
        
        sub = db.query(Subscription).filter(Subscription.user_id == user.id).first()
        
        if sub:
            print(f"  Plan: {sub.plan_type}")
            print(f"  Status: {sub.status}")
            print(f"  Stripe Customer: {sub.stripe_customer_id or 'None'}")
            print(f"  Stripe Subscription: {sub.stripe_subscription_id or 'None'}")
            print(f"  Generations: {sub.generations_used}/{sub.generations_limit}")
        else:
            print("  ❌ No subscription found")
        
        print("")

db.close()

print("="*60)
print("💡 If stripe_subscription_id is None, webhooks aren't")
print("   updating the database. Use Stripe CLI for local testing:")
print("   stripe listen --forward-to localhost:8000/api/v1/webhooks/stripe")
print("="*60)
# Production Testing Guide

**Date:** October 16, 2025  
**Purpose:** Test generation and subscription workflows directly on production server

## 🎯 Overview

This guide helps you test the two main workflows:
1. **Generation Workflow** - File generation with mdream crawler
2. **Subscription Workflow** - Stripe integration and subscriptions

---

## 🧪 Test 1: Generation Workflow

### Run the Generation Test

```bash
# SSH to production server
ssh user@your-server

# Navigate to project
cd /opt/llmready

# Make script executable
chmod +x scripts/test_generation_workflow.py

# Run the test
python3 scripts/test_generation_workflow.py
```

### What This Tests

✅ **Docker availability** - Checks if Docker is installed and mdream image exists  
✅ **npx availability** - Checks if Node.js/npx is available as fallback  
✅ **Database connectivity** - Tests connection and shows generation records  
✅ **Celery tasks** - Verifies tasks are registered (must show 4 tasks)  
✅ **Actual crawler** - Runs a real test generation with example.com  

### Expected Output

```
🧪 LLMReady Generation Workflow Test (Production)
============================================================

INFO: Testing Docker availability...
SUCCESS: Docker installed: Docker version X.X.X
SUCCESS: mdream Docker image found

INFO: Testing npx availability...
SUCCESS: npx installed: X.X.X

=== Testing Database Connectivity ===
INFO: Total users in database: 5
INFO: Total websites in database: 3
INFO: Total generations in database: 10

=== Testing Celery/Redis Connectivity ===
SUCCESS: Registered Celery tasks: 4
INFO:   - app.tasks.generation.generate_llm_content
INFO:   - app.tasks.scheduled.cleanup_old_generations
INFO:   - app.tasks.scheduled.reset_monthly_quotas
INFO:   - app.tasks.scheduled.sync_stripe_subscriptions
SUCCESS: Redis is responding

=== Testing Crawler with Simple Website ===
INFO: Testing crawler with: https://example.com
SUCCESS: Crawler succeeded in 15.23s
SUCCESS: llms.txt exists (12345 bytes)
SUCCESS: ZIP created successfully (8192 bytes)

📊 TEST SUMMARY
============================================================
DOCKER: ✅ PASS
NPX: ✅ PASS
DATABASE: ✅ PASS
CELERY: ✅ PASS
CRAWLER: ✅ PASS

🎉 All tests passed! Generation should work.
```

### Common Issues & Fixes

#### ❌ Docker: FAIL

**Problem:** Docker not installed or mdream image missing

**Fix:**
```bash
# Install Docker
sudo /opt/llmready/scripts/install-docker.sh

# Or pull mdream image
docker pull harlanzw/mdream
```

#### ❌ Celery: FAIL (No tasks registered)

**Problem:** Tasks not imported in `__init__.py`

**Fix:**
```bash
# Check if fix is applied
cat /opt/llmready/backend/app/tasks/__init__.py

# Should see imports of all tasks
# If not, pull latest code:
cd /opt/llmready
git pull origin main

# Restart worker
sudo systemctl restart llmready-celery-worker
```

#### ❌ Crawler: FAIL

**Problem:** Neither Docker nor npx available

**Fix:** Install at least one:
```bash
# Option 1: Docker (recommended)
sudo /opt/llmready/scripts/install-docker.sh

# Option 2: Node.js/npx
sudo apt-get update
sudo apt-get install -y nodejs npm
```

---

## 💳 Test 2: Subscription Workflow

### Run the Subscription Test

```bash
# SSH to production server
ssh user@your-server

# Navigate to project
cd /opt/llmready

# Make script executable
chmod +x scripts/test_stripe_subscription.py

# Run the test
python3 scripts/test_stripe_subscription.py
```

### What This Tests

✅ **Stripe API connectivity** - Tests connection to Stripe  
✅ **Stripe price configuration** - Verifies all price IDs are configured  
✅ **Webhook configuration** - Checks webhook secret and endpoints  
✅ **Subscription database** - Shows subscription records  
✅ **Subscription service** - Tests service layer functionality  
✅ **Plan configuration** - Validates plan limits and features  
✅ **Checkout simulation** (optional) - Creates a test checkout session  

### Expected Output

```
💳 LLMReady Stripe Subscription Test (Production)
============================================================

=== Testing Stripe Connection ===
SUCCESS: Connected to Stripe successfully
INFO: Found 3 products

=== Testing Stripe Price Configuration ===
SUCCESS: ✅ STARTER_MONTHLY: price_xxxxx (EUR 19)
SUCCESS: ✅ STARTER_YEARLY: price_xxxxx (EUR 171)
SUCCESS: ✅ STANDARD_MONTHLY: price_xxxxx (EUR 39)
SUCCESS: ✅ STANDARD_YEARLY: price_xxxxx (EUR 351)
SUCCESS: ✅ PRO_MONTHLY: price_xxxxx (EUR 79)
SUCCESS: ✅ PRO_YEARLY: price_xxxxx (EUR 711)

=== Testing Webhook Configuration ===
SUCCESS: Webhook secret configured: whsec_xxxxx...
INFO: Found 1 webhook endpoints
INFO:   URL: https://api.llmready.ai/api/v1/webhooks/stripe
INFO:   Status: enabled

=== Testing Subscription Database ===
INFO: Total subscriptions: 5

By Plan Type:
  free: 3
  standard: 2

By Status:
  active: 4
  canceled: 1

=== Testing Subscription Service ===
SUCCESS: ✅ Get subscription info works
SUCCESS: ✅ Get usage stats works
SUCCESS: ✅ Check generation quota works: True

📊 TEST SUMMARY
============================================================
STRIPE_CONNECTION: ✅ PASS
STRIPE_PRICES: ✅ PASS
WEBHOOK_CONFIG: ✅ PASS
DATABASE: ✅ PASS
SERVICE: ✅ PASS
PLAN_CONFIG: ✅ PASS

🎉 All tests passed! Stripe integration is working.
```

### Common Issues & Fixes

#### ❌ Stripe Connection: FAIL

**Problem:** Invalid or missing Stripe API key

**Fix:**
```bash
# Check .env file
grep STRIPE_SECRET_KEY /opt/llmready/backend/.env

# Should start with sk_live_ for production
# If missing or incorrect, update it:
nano /opt/llmready/backend/.env
# Add: STRIPE_SECRET_KEY=sk_live_xxxxx

# Restart backend
sudo systemctl restart llmready-backend
```

#### ❌ Stripe Prices: FAIL

**Problem:** Price IDs not configured or don't exist in Stripe

**Fix:**
```bash
# Check all price IDs in .env
grep STRIPE_PRICE /opt/llmready/backend/.env

# Should see all 6 price IDs:
# STRIPE_PRICE_STARTER_MONTHLY=price_xxxxx
# STRIPE_PRICE_STARTER_YEARLY=price_xxxxx
# STRIPE_PRICE_STANDARD_MONTHLY=price_xxxxx
# STRIPE_PRICE_STANDARD_YEARLY=price_xxxxx
# STRIPE_PRICE_PRO_MONTHLY=price_xxxxx
# STRIPE_PRICE_PRO_YEARLY=price_xxxxx

# If missing, get them from Stripe Dashboard:
# https://dashboard.stripe.com/prices
```

#### ❌ Webhook Config: FAIL

**Problem:** Webhook secret not configured

**Fix:**
```bash
# Check webhook secret
grep STRIPE_WEBHOOK_SECRET /opt/llmready/backend/.env

# Should start with whsec_
# Get it from Stripe Dashboard → Webhooks → Your endpoint → Signing secret

# Update .env
nano /opt/llmready/backend/.env
# Add: STRIPE_WEBHOOK_SECRET=whsec_xxxxx

# Restart backend
sudo systemctl restart llmready-backend
```

---

## 🔍 Manual Testing After Fixes

### Test Real Generation

After fixing generation issues:

```bash
# 1. Create a website via API or UI
# 2. Trigger a generation
# 3. Monitor the process

# Watch Celery logs in real-time
sudo journalctl -u llmready-celery-worker -f

# Check generation status in database
sudo -u postgres psql llmready_prod
SELECT id, status, error_message, created_at 
FROM generations 
ORDER BY created_at DESC 
LIMIT 5;
```

### Test Real Subscription

After fixing Stripe issues:

```bash
# 1. Go to frontend and subscribe to a plan
# 2. Complete Stripe checkout
# 3. Check if webhook was received

# Check webhook logs
sudo journalctl -u llmready-backend -f | grep webhook

# Check subscription in database
sudo -u postgres psql llmready_prod
SELECT u.email, s.plan_type, s.status, s.stripe_subscription_id
FROM subscriptions s
JOIN users u ON u.id = s.user_id
ORDER BY s.updated_at DESC
LIMIT 5;

# Verify in Stripe Dashboard
# https://dashboard.stripe.com/subscriptions
```

---

## 📊 Quick Diagnostic Commands

### Check All Services Status

```bash
# Check all LLMReady services
sudo systemctl status llmready-backend
sudo systemctl status llmready-celery-worker
sudo systemctl status llmready-celery-beat

# Check Docker
docker --version
docker images | grep mdream

# Check Redis
redis-cli ping
redis-cli LLEN celery
redis-cli LLEN generation
```

### View Recent Logs

```bash
# Backend logs
sudo journalctl -u llmready-backend -n 100 --no-pager

# Celery worker logs
sudo journalctl -u llmready-celery-worker -n 100 --no-pager

# Look for errors
sudo journalctl -u llmready-backend --since "1 hour ago" | grep -i error
sudo journalctl -u llmready-celery-worker --since "1 hour ago" | grep -i error
```

### Database Quick Checks

```bash
# Connect to database
sudo -u postgres psql llmready_prod

# Check recent activity
SELECT 
    (SELECT COUNT(*) FROM users) as total_users,
    (SELECT COUNT(*) FROM websites) as total_websites,
    (SELECT COUNT(*) FROM generations) as total_generations,
    (SELECT COUNT(*) FROM subscriptions WHERE status='active') as active_subscriptions;

# Check recent generations
SELECT id, status, created_at, error_message 
FROM generations 
WHERE created_at > NOW() - INTERVAL '24 hours'
ORDER BY created_at DESC;

# Exit
\q
```

---

## 🚨 Emergency Troubleshooting

### Generation Completely Broken

```bash
# 1. Check if Celery worker is running
sudo systemctl status llmready-celery-worker

# 2. Check if tasks are registered
cd /opt/llmready/backend
python3 -c "from app.core.celery_app import celery_app; print([t for t in celery_app.tasks.keys() if 'app.' in t])"

# 3. Restart everything
sudo systemctl restart llmready-celery-worker
sudo systemctl restart llmready-celery-beat

# 4. Test with script
python3 /opt/llmready/scripts/test_generation_workflow.py
```

### Subscriptions Not Updating

```bash
# 1. Check webhook endpoint is accessible
curl -X POST https://api.llmready.ai/api/v1/webhooks/stripe \
  -H "Content-Type: application/json" \
  -d '{"type":"test"}'

# Should return 400 (missing signature) not 404/500

# 2. Check Stripe webhook logs
# Go to: https://dashboard.stripe.com/webhooks
# Click your endpoint → View logs

# 3. Manual webhook sync
cd /opt/llmready/backend
python3 -c "
from app.core.celery_app import celery_app
from app.tasks.scheduled import sync_stripe_subscriptions
sync_stripe_subscriptions()
"
```

---

## 📝 Report Template

After running tests, use this template to report issues:

```
## Test Results

**Date:** [Date]
**Server:** [Production/Staging]

### Generation Test
- Docker: [PASS/FAIL]
- Celery Tasks: [PASS/FAIL]
- Crawler: [PASS/FAIL]
- Error Details: [If any]

### Subscription Test
- Stripe Connection: [PASS/FAIL]
- Price Config: [PASS/FAIL]
- Webhook Config: [PASS/FAIL]
- Error Details: [If any]

### Next Steps
[List what you plan to fix]
```

---

**Last Updated:** 2025-10-16  
**Version:** 1.0.0
# Quick Test Commands for Production

Run these commands directly on your production server to test workflows.

## 🚀 Quick Start

```bash
# SSH to production server
ssh user@your-server
cd /opt/llmready

# Make scripts executable
chmod +x scripts/test_generation_workflow.py
chmod +x scripts/test_stripe_subscription.py
```

## 1️⃣ Test Generation Workflow

```bash
# Run complete generation test
python3 scripts/test_generation_workflow.py
```

**Tests:** Docker, npx, database, Celery tasks, actual crawler

**Fix if fails:**
```bash
# Install Docker (if missing)
sudo scripts/install-docker.sh

# Restart Celery worker (if tasks not registered)
sudo systemctl restart llmready-celery-worker
```

---

## 2️⃣ Test Subscription/Stripe

```bash
# Run complete Stripe test
python3 scripts/test_stripe_subscription.py
```

**Tests:** Stripe API, prices, webhooks, database, service layer

**Fix if fails:**
```bash
# Check environment variables
grep STRIPE /opt/llmready/backend/.env

# Should see:
# STRIPE_SECRET_KEY=sk_live_...
# STRIPE_WEBHOOK_SECRET=whsec_...
# STRIPE_PRICE_STARTER_MONTHLY=price_...
# ... (all 6 price IDs)
```

---

## 🔍 Quick Diagnostics

### Check Services
```bash
sudo systemctl status llmready-backend
sudo systemctl status llmready-celery-worker
sudo systemctl status llmready-celery-beat
```

### Check Celery Tasks
```bash
cd /opt/llmready/backend
python3 -c "from app.core.celery_app import celery_app; print([t for t in celery_app.tasks.keys() if 'app.' in t])"
```

**Expected output (4 tasks):**
```
['app.tasks.generation.generate_llm_content', 
 'app.tasks.scheduled.cleanup_old_generations',
 'app.tasks.scheduled.reset_monthly_quotas',
 'app.tasks.scheduled.sync_stripe_subscriptions']
```

### Check Docker
```bash
docker --version
docker images | grep mdream
```

### View Logs
```bash
# Backend logs (last 50 lines)
sudo journalctl -u llmready-backend -n 50

# Celery worker logs (last 50 lines)
sudo journalctl -u llmready-celery-worker -n 50

# Real-time logs
sudo journalctl -u llmready-celery-worker -f
```

### Check Database
```bash
sudo -u postgres psql llmready_prod

-- Recent generations
SELECT id, status, created_at, error_message 
FROM generations 
ORDER BY created_at DESC 
LIMIT 5;

-- Active subscriptions
SELECT u.email, s.plan_type, s.status 
FROM subscriptions s 
JOIN users u ON u.id = s.user_id 
WHERE s.status = 'active';

-- Exit
\q
```

---

## 🐛 Common Fixes

### Celery Tasks Not Registered
```bash
cd /opt/llmready
git pull origin main
sudo systemctl restart llmready-celery-worker
```

### Docker Missing
```bash
sudo /opt/llmready/scripts/install-docker.sh
```

### Generation Failing
```bash
# Check logs
sudo journalctl -u llmready-celery-worker -n 100 | grep -i error

# Verify Docker works
docker run --rm harlanzw/mdream --help

# Restart worker
sudo systemctl restart llmready-celery-worker
```

### Stripe Not Working
```bash
# Verify credentials
grep STRIPE_SECRET_KEY /opt/llmready/backend/.env

# Test connection
cd /opt/llmready/backend
python3 -c "import stripe; from app.core.config import settings; stripe.api_key=settings.STRIPE_SECRET_KEY; print(stripe.Product.list(limit=1))"
```

---

## 📖 Full Documentation

- **Complete testing guide:** [`PRODUCTION_TESTING_GUIDE.md`](PRODUCTION_TESTING_GUIDE.md)
- **All fixes applied:** [`PRODUCTION_FIXES.md`](PRODUCTION_FIXES.md)
- **Monitoring commands:** [`PRODUCTION_MONITORING_COMMANDS.md`](PRODUCTION_MONITORING_COMMANDS.md)
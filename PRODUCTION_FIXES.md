# Production Fixes Documentation

**Date:** October 16, 2025  
**Issues Resolved:** Registration, Celery Worker, Generation, Subscription UI

## 🐛 Issues Identified

### 1. Registration Not Returning Tokens
**Problem:** Backend registration endpoint returned only `UserResponse` but frontend expected `LoginResponse` with access/refresh tokens.

**Impact:** Users couldn't log in immediately after registration, showing "Registration failed" error despite successful account creation.

### 2. Celery Worker Tasks Not Registered
**Problem:** Celery tasks were not being imported in `__init__.py`, causing the worker to have NO registered tasks.

**Impact:** All background generation jobs failed silently. No tasks were picked up by the worker.

### 3. Generation Failing - No Docker or npx
**Problem:** Production server had neither Docker nor npx (Node.js) installed, causing all crawl operations to fail with `[Errno 2] No such file or directory: 'npx'`.

**Impact:** All file generation requests failed immediately.

### 4. Subscription Plan Update Not Reflecting in UI
**Problem:** After successful subscription upgrade, UI wasn't refreshing to show new plan.

**Impact:** Users saw old plan data after upgrading, causing confusion.

---

## ✅ Fixes Applied

### Fix 1: Registration Endpoint Returns Tokens

**File:** [`backend/app/api/v1/auth.py`](backend/app/api/v1/auth.py:42)

**Changes:**
1. Changed response model from `UserResponse` to `LoginResponse`
2. Added token generation in registration endpoint
3. Returns complete auth response with tokens for immediate login

```python
# Before: Only returned user object
return new_user

# After: Returns tokens + user object
access_token = create_access_token(
    data={"sub": str(new_user.id), "email": new_user.email}
)
refresh_token = create_refresh_token(
    data={"sub": str(new_user.id)}
)

return {
    "user": new_user,
    "access_token": access_token,
    "refresh_token": refresh_token,
    "token_type": "bearer",
    "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
}
```

### Fix 2: Celery Tasks Registration

**File:** [`backend/app/tasks/__init__.py`](backend/app/tasks/__init__.py:1)

**Changes:**
1. Added explicit imports of all task functions
2. Added `__all__` export list for proper module exposure

```python
# Import tasks to ensure they are registered with Celery
from app.tasks.generation import generate_llm_content
from app.tasks.scheduled import (
    reset_monthly_quotas,
    cleanup_old_generations,
    sync_stripe_subscriptions
)

__all__ = [
    'generate_llm_content',
    'reset_monthly_quotas',
    'cleanup_old_generations',
    'sync_stripe_subscriptions'
]
```

### Fix 3: Docker Installation Script

**File:** [`scripts/install-docker.sh`](scripts/install-docker.sh:1)

**Created:** Complete Docker installation script for production server

**Features:**
- Installs Docker Engine on Debian/Ubuntu
- Pulls `harlanzw/mdream` container
- Configures Docker service
- Tests installation

### Fix 4: Subscription UI Refresh

**File:** [`frontend/src/pages/SubscriptionPage.tsx`](frontend/src/pages/SubscriptionPage.tsx:102)

**Changes:**
1. Added handling for `upgraded=true` query parameter
2. Forces both invalidation AND refetch of subscription data
3. Shows success toast after upgrade

```typescript
// Added upgraded parameter handling
const upgraded = searchParams.get('upgraded')

if (upgraded === 'true') {
  toast.success('Subscription upgraded successfully!')
  queryClient.invalidateQueries({ queryKey: ['subscription'] })
  queryClient.refetchQueries({ queryKey: ['subscription'] })
  setSearchParams({})
}
```

---

## 🚀 Deployment Instructions

### Step 1: Deploy Backend Changes

```bash
# SSH to production server
ssh user@your-server

# Navigate to project
cd /opt/llmready

# Pull latest changes
git pull origin main

# Restart backend service
sudo systemctl restart llmready-backend
```

### Step 2: Install Docker

```bash
# Run Docker installation script
cd /opt/llmready
sudo chmod +x scripts/install-docker.sh
sudo ./scripts/install-docker.sh

# Verify Docker installation
docker --version
docker images | grep mdream
```

### Step 3: Restart Celery Worker

```bash
# Restart worker to load new tasks
sudo systemctl restart llmready-celery-worker

# Verify tasks are registered
cd /opt/llmready/backend
python -c "
from app.core.celery_app import celery_app
print('Registered tasks:')
for task in sorted(celery_app.tasks.keys()):
    if 'app.' in task:
        print(f'  - {task}')
"

# Should show:
#   - app.tasks.generation.generate_llm_content
#   - app.tasks.scheduled.cleanup_old_generations
#   - app.tasks.scheduled.reset_monthly_quotas
#   - app.tasks.scheduled.sync_stripe_subscriptions
```

### Step 4: Deploy Frontend Changes

```bash
# On local machine
cd frontend
npm run build

# Deploy to production (adjust based on your deployment method)
# Example for manual deployment:
scp -r dist/* user@your-server:/var/www/llmready/

# Or if using CI/CD, push to main branch
git push origin main
```

### Step 5: Verify All Services

```bash
# Check backend status
sudo systemctl status llmready-backend

# Check Celery worker status
sudo systemctl status llmready-celery-worker

# Check Celery beat status (scheduled tasks)
sudo systemctl status llmready-celery-beat

# Check logs for any errors
sudo journalctl -u llmready-backend -n 50
sudo journalctl -u llmready-celery-worker -n 50
```

---

## 🧪 Testing

### Production Testing Script

We've created a comprehensive testing script: [`scripts/test_production.py`](scripts/test_production.py:1)

**Run the test:**

```bash
# On your local machine or production server
cd /opt/llmready
python3 scripts/test_production.py https://api.llmready.ai
```

**Tests performed:**
1. ✅ API health check
2. ✅ User registration (with token return)
3. ✅ Get subscription info
4. ✅ Create website
5. ✅ Create generation (tests Celery tasks)

### Manual Testing Checklist

- [ ] Register new user → Should receive tokens and auto-login
- [ ] Subscribe to paid plan → Plan should update immediately in UI
- [ ] Create website → Should succeed
- [ ] Generate files → Should process successfully (check Celery logs)
- [ ] Check subscription after payment → Should show new plan

---

## 📊 Monitoring Commands

### Check Celery Task Queue

```bash
# Connect to Redis
docker exec -it $(docker ps -qf "name=redis") redis-cli

# Check pending tasks
LLEN celery
LLEN generation
LLEN scheduled

# View task details
LRANGE celery 0 -1
```

### View Celery Worker Logs

```bash
# Real-time logs
sudo journalctl -u llmready-celery-worker -f

# Last 100 lines
sudo journalctl -u llmready-celery-worker -n 100
```

### Check Generation Status

```bash
# In production database
sudo -u postgres psql llmready_prod

# Check recent generations
SELECT id, status, created_at, error_message 
FROM generations 
ORDER BY created_at DESC 
LIMIT 10;
```

---

## 🔍 Troubleshooting

### Issue: Tasks still not registered

**Solution:**
```bash
# Ensure tasks are imported properly
cd /opt/llmready/backend
python -c "from app.tasks import *; print('Success')"

# Restart worker with verbose logging
sudo systemctl stop llmready-celery-worker
cd /opt/llmready/backend
/opt/llmready/venv/bin/celery -A app.core.celery_app worker --loglevel=debug
```

### Issue: Docker container fails to run

**Solution:**
```bash
# Check Docker service
sudo systemctl status docker

# Test mdream container manually
docker run --rm -v /tmp/test:/app/output harlanzw/mdream --url https://example.com

# Check Docker logs
docker logs $(docker ps -lq)
```

### Issue: Registration still returns error

**Solution:**
```bash
# Check backend logs for specific error
sudo journalctl -u llmready-backend -f

# Test registration endpoint directly
curl -X POST https://api.llmready.ai/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"TestPass123!","full_name":"Test User"}'
```

### Issue: Subscription not updating in UI

**Solution:**
1. Check browser console for errors
2. Verify webhook was received: Check Stripe Dashboard → Webhooks
3. Check subscription in database:
```sql
SELECT * FROM subscriptions WHERE user_id = 'USER_ID';
```

---

## 📝 Environment Variables

Ensure these are set in `/opt/llmready/backend/.env`:

```bash
# Required for Celery
REDIS_URL=redis://localhost:6379/0

# Required for Stripe webhooks
STRIPE_WEBHOOK_SECRET=whsec_...

# Required for emails
SENDGRID_API_KEY=SG...
FROM_EMAIL=noreply@llmready.ai

# Required for file storage
FILE_STORAGE_PATH=/opt/llmready/storage
```

---

## 🎯 Success Criteria

All issues should be resolved when:

1. ✅ New user registration auto-logs in user
2. ✅ Celery worker shows 4 registered tasks
3. ✅ File generation completes successfully
4. ✅ Subscription UI updates immediately after payment
5. ✅ All tests in `test_production.py` pass

---

## 📞 Support

If issues persist after applying these fixes:

1. Check all logs: backend, celery-worker, celery-beat
2. Verify all environment variables are set
3. Ensure Docker is running and mdream image is pulled
4. Check Redis connection
5. Verify Stripe webhook endpoint is accessible

---

**Last Updated:** 2025-10-16  
**Version:** 1.0.0
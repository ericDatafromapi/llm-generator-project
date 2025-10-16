# Monitoring Production Deployment Guide

Congratulations on successfully testing Sentry! Now let's deploy it to production safely.

## 📋 Pre-Deployment Checklist

### 1. Sentry Projects Setup

**Important**: You should have **separate Sentry projects** for production:

- ✅ **Production Backend Project** (separate from your dev backend)
- ✅ **Production Frontend Project** (separate from your dev frontend)

**Why?** This keeps development errors separate from production, making it easier to:
- Monitor real user issues without dev noise
- Set different alert rules
- Track separate error budgets

**To Create Production Projects:**
1. Go to Sentry → **Create Project**
2. Select platform (Python for backend, React for frontend)
3. Name: `llmready-backend-production` and `llmready-frontend-production`
4. Copy the new production DSNs

---

## 🚀 Backend Production Setup

### Step 1: Update Production Environment

Edit your server's [`backend/.env`](../backend/.env) file (or use environment variables):

```bash
# Monitoring & Logging - PRODUCTION
SENTRY_DSN=https://YOUR_PRODUCTION_BACKEND_DSN@sentry.io/PROJECT_ID
SENTRY_TRACES_SAMPLE_RATE=0.1  # 10% sampling for production
SENTRY_PROFILES_SAMPLE_RATE=0.1
LOG_LEVEL=INFO
ENVIRONMENT=production  # IMPORTANT: Set to production
```

**Key Changes from Development:**
- Different DSN (production project)
- Sample rate: `1.0` → `0.1` (10% to reduce costs)
- Environment: `development` → `production`

### Step 2: Remove Test Endpoint (Optional)

For production, you may want to remove the test endpoint from [`backend/app/main.py`](../backend/app/main.py:140-148):

```python
# Comment out or remove this in production:
# @app.get("/test-sentry", tags=["Testing"])
# async def test_sentry():
#     """Test endpoint..."""
#     raise ValueError("Test error")
```

Or keep it but add authentication/rate limiting.

### Step 3: Deploy Backend

```bash
# On your server
cd /path/to/backend

# Pull latest code
git pull origin main

# Install dependencies (if not already)
pip install -r requirements.txt

# Restart backend service
sudo systemctl restart llmready-backend

# Verify Sentry initialization
sudo journalctl -u llmready-backend -f | grep -i sentry
```

You should see: `Sentry initialized - Environment: production`

---

## 🌐 Frontend Production Setup

### Step 1: Update Production Environment

Create or update [`frontend/.env.production`](../frontend/.env.production):

```bash
# API Configuration
VITE_API_URL=https://your-api-domain.com

# Monitoring & Error Tracking - PRODUCTION
VITE_SENTRY_DSN=https://YOUR_PRODUCTION_FRONTEND_DSN@sentry.io/PROJECT_ID
VITE_ENVIRONMENT=production

# Source Maps Upload (REQUIRED for production)
VITE_SENTRY_AUTH_TOKEN=your_sentry_auth_token
VITE_SENTRY_ORG=your-org-slug
VITE_SENTRY_PROJECT=llmready-frontend-production
```

**Key Changes from Development:**
- Different DSN (production project)
- Environment: `development` → `production`
- Remove `VITE_SENTRY_DEBUG` (or set to `false`)
- Add source map upload credentials (required)

### Step 2: Build with Source Maps

```bash
cd frontend

# Build for production
npm run build
```

**What happens:**
1. Vite creates optimized production build
2. Source maps are generated
3. Source maps are uploaded to Sentry (if auth token configured)
4. Original code visible in Sentry stack traces

### Step 3: Deploy Frontend

Deploy the `dist/` folder to your hosting (Vercel, Netlify, S3, etc.)

---

## 🔒 Security Considerations

### 1. Don't Commit Sensitive Data

Ensure `.env` files are in `.gitignore`:

```bash
# Verify
cat .gitignore | grep .env
```

Should show:
```
.env
.env.local
.env.production
```

### 2. Use Environment Variables on Server

**Backend**: Set via systemd service or server environment
**Frontend**: Set via hosting platform's environment variables

### 3. Restrict Sentry Test Endpoint

If keeping the test endpoint in production:

```python
from app.api.dependencies import get_current_user

@app.get("/test-sentry", dependencies=[Depends(get_current_user)])
async def test_sentry():
    # Only accessible to authenticated users
    raise ValueError("Test error")
```

---

## 📊 Production Monitoring Setup

### 1. Configure Alerts

In Sentry dashboard for **each production project**:

**Go to: Alerts → Create Alert Rule**

**Recommended Alerts:**

**Critical Error Alert:**
- Condition: Error count > 10 in 5 minutes
- Action: Email + Slack notification
- Priority: High

**New Issue Alert:**
- Condition: A new issue is created
- Action: Email notification
- Priority: Medium

**Performance Alert:**
- Condition: Transaction duration > 3 seconds
- Action: Email notification
- Priority: Low

### 2. Set Up Integrations

**Slack Integration:**
1. Sentry → Settings → Integrations → Slack
2. Connect your workspace
3. Choose channels for notifications

**Email Notifications:**
1. Sentry → Settings → Account → Notifications
2. Enable email alerts
3. Set notification preferences

### 3. Create Dashboard

Go to **Dashboards → Create Dashboard**

**Recommended Widgets:**
- Error rate over time
- Most common errors
- Slowest transactions
- Users affected by errors

---

## 🧪 Post-Deployment Testing

### 1. Verify Backend

**Test that Sentry captures production errors:**

```bash
# SSH into your server and test
curl https://your-api-domain.com/test-sentry
```

Check Sentry dashboard - error should appear within 30 seconds.

### 2. Verify Frontend

Visit your production site and open console:

```javascript
// Should see initialization message
// Then test error tracking:
throw new Error('Production test error');
```

Check Sentry dashboard for the error.

### 3. Monitor First 24 Hours

**Day 1 Checklist:**
- [ ] Check for unexpected errors
- [ ] Verify performance data is being collected
- [ ] Confirm alerts are working
- [ ] Review error patterns
- [ ] Adjust sample rates if needed

---

## 📈 Optimization Tips

### 1. Adjust Sample Rates Based on Traffic

**Low Traffic (<1,000 req/day):**
```bash
SENTRY_TRACES_SAMPLE_RATE=1.0  # 100%
```

**Medium Traffic (1,000-10,000 req/day):**
```bash
SENTRY_TRACES_SAMPLE_RATE=0.1  # 10%
```

**High Traffic (>10,000 req/day):**
```bash
SENTRY_TRACES_SAMPLE_RATE=0.01  # 1%
```

### 2. Filter Known Issues

Update [`backend/app/core/logging_config.py`](../backend/app/core/logging_config.py) to ignore specific errors:

```python
def before_send(event, hint):
    # Ignore known non-critical errors
    if 'connection reset by peer' in str(event):
        return None
    return event
```

### 3. Set Up Release Tracking

**Backend:**
```bash
# In your deployment script
export SENTRY_RELEASE=$(git rev-parse HEAD)
```

**Frontend:**
```bash
# In package.json
"version": "1.2.3"
```

This helps track which release introduced which errors.

---

## 🚨 Troubleshooting Production Issues

### Issue: No Events in Production Sentry

**Check:**
1. DSN is correctly set in production environment
2. Service restarted after environment changes
3. Sample rate isn't 0
4. Firewall allows outbound to `sentry.io`
5. Check logs for Sentry initialization message

### Issue: Too Many Events

**Solution:**
1. Lower sample rates
2. Add filtering in `beforeSend`
3. Upgrade Sentry plan
4. Review and resolve common errors

### Issue: Source Maps Not Working

**Frontend Only:**
1. Verify `VITE_SENTRY_AUTH_TOKEN` is set
2. Check build output for "Uploading source maps"
3. Verify token permissions in Sentry

---

## 📊 Monitoring Best Practices

### 1. Daily Monitoring

**First Week:**
- Check Sentry dashboard daily
- Review new issues
- Identify patterns
- Fix critical bugs

**After Stabilization:**
- Review weekly
- Focus on high-impact errors
- Monitor performance trends

### 2. Weekly Review

Create a weekly routine:
- [ ] Review top 10 errors
- [ ] Check performance metrics
- [ ] Update alert thresholds
- [ ] Review resolved issues

### 3. Monthly Optimization

- [ ] Review sample rates
- [ ] Update ignored errors list
- [ ] Check Sentry costs
- [ ] Review alert effectiveness

---

## 💰 Cost Management

### Free Tier Limits

**Sentry Free:**
- 5,000 errors/month
- 10,000 performance transactions/month

**Monitor Usage:**
- Sentry → Settings → Usage & Billing

**Optimize if Approaching Limit:**
1. Reduce sample rates
2. Filter more errors
3. Fix common errors to reduce volume
4. Upgrade plan if needed

---

## 🔄 Rollback Plan

If issues arise after deployment:

```bash
# Backend: Disable Sentry temporarily
SENTRY_DSN=
sudo systemctl restart llmready-backend

# Frontend: Rebuild without Sentry
# Set VITE_SENTRY_DSN to empty in build environment
npm run build
```

---

## ✅ Production Deployment Checklist

### Pre-Deployment
- [ ] Created separate production Sentry projects
- [ ] Updated backend `.env` with production DSN
- [ ] Updated frontend `.env.production` with production DSN
- [ ] Set sample rates to 0.1 (10%)
- [ ] Set ENVIRONMENT to "production"
- [ ] Removed or secured test endpoint
- [ ] Configured source map uploads (frontend)

### Deployment
- [ ] Deployed backend with new environment variables
- [ ] Deployed frontend with production build
- [ ] Verified Sentry initialization logs
- [ ] Tested error capture in production

### Post-Deployment
- [ ] Set up Sentry alerts
- [ ] Configured Slack/email notifications
- [ ] Created monitoring dashboard
- [ ] Tested error tracking end-to-end
- [ ] Documented monitoring procedures

---

## 📚 Additional Resources

- **Main Setup Guide**: [`MONITORING_SETUP_GUIDE.md`](./MONITORING_SETUP_GUIDE.md)
- **Implementation Summary**: [`MONITORING_SUMMARY.md`](./MONITORING_SUMMARY.md)
- **Sentry Documentation**: https://docs.sentry.io/
- **Performance Monitoring**: https://docs.sentry.io/product/performance/

---

**Remember**: Monitoring is an ongoing process. Review your Sentry dashboard regularly and continuously optimize based on real production data! 🚀
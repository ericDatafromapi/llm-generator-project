# Deploying Monitoring with GitHub Actions

Your existing GitHub Actions deployment workflow has been updated to automatically configure Sentry monitoring in production. Here's how to deploy:

## 🔐 Required GitHub Secrets

Add these secrets to your GitHub repository at **Settings → Secrets and variables → Actions**:

### Backend Sentry Secrets

```
BACKEND_SENTRY_DSN
```
**Value**: Your production backend Sentry DSN
```
https://xxxxx@o4510198050521088.ingest.de.sentry.io/BACKEND_PROJECT_ID
```

### Frontend Sentry Secrets

```
FRONTEND_SENTRY_DSN
```
**Value**: Your production frontend Sentry DSN
```
https://xxxxx@o4510198050521088.ingest.de.sentry.io/FRONTEND_PROJECT_ID
```

```
SENTRY_AUTH_TOKEN
```
**Value**: Your Sentry authentication token (for source map uploads)
- Get from: https://sentry.io/settings/account/api/auth-tokens/
- Create new token with scopes: `project:releases` and `project:write`

```
SENTRY_ORG
```
**Value**: Your Sentry organization slug (e.g., `your-org-name`)

```
SENTRY_FRONTEND_PROJECT
```
**Value**: Your frontend project slug (e.g., `llmready-frontend-production`)

## 📋 Pre-Deployment Checklist

### 1. Create Production Sentry Projects

Go to [Sentry](https://sentry.io) and create:
- [ ] **Backend Production Project** → Copy DSN
- [ ] **Frontend Production Project** → Copy DSN

### 2. Add GitHub Secrets

Go to your GitHub repository → **Settings** → **Secrets and variables** → **Actions**:

- [ ] Add `BACKEND_SENTRY_DSN`
- [ ] Add `FRONTEND_SENTRY_DSN`
- [ ] Add `SENTRY_AUTH_TOKEN`
- [ ] Add `SENTRY_ORG`
- [ ] Add `SENTRY_FRONTEND_PROJECT`

### 3. Verify Existing Secrets

Make sure these are already configured:
- [ ] `PRODUCTION_API_URL`
- [ ] `STRIPE_PUBLIC_KEY`
- [ ] `SSH_PRIVATE_KEY`
- [ ] `SERVER_HOST`
- [ ] `SERVER_USER`
- [ ] `PRODUCTION_DOMAIN`

## 🚀 Deploy to Production

### Option 1: Using the Deploy Script (Recommended)

```bash
# From project root
./scripts/deploy.sh
```

This will:
1. Check for uncommitted changes
2. Ask for confirmation
3. Trigger the GitHub Actions workflow
4. Show you the workflow run URL

### Option 2: Manual GitHub Dispatch

1. Go to **Actions** tab in GitHub
2. Select **"Deploy to Production"** workflow
3. Click **"Run workflow"**
4. Type `deploy` to confirm
5. Click **"Run workflow"**

### Option 3: Push to Main Branch

Simply push to the `main` branch (unless files are in `docs/` or `*.md`):

```bash
git push origin main
```

## 📊 What Happens During Deployment

### 1. Build & Test Phase
- Backend tests run with PostgreSQL and Redis
- Frontend builds with production Sentry configuration
- Source maps are generated and uploaded to Sentry

### 2. Backend Deployment
- Code deployed to server
- `.env` automatically updated with:
  - `SENTRY_DSN` (from GitHub secret)
  - `ENVIRONMENT=production`
  - `SENTRY_TRACES_SAMPLE_RATE=0.1`
- Database migrations run
- Backend service restarts

### 3. Frontend Deployment
- Optimized build deployed to `/var/www/llmready`
- Includes Sentry SDK with source maps
- Nginx reloaded

### 4. Verification
- Health check on backend: `https://your-domain.com/health`
- Frontend check: `https://your-domain.com`
- Email notification sent

## ✅ Post-Deployment Verification

### 1. Check Sentry Initialization

**Backend logs:**
```bash
ssh user@your-server
sudo journalctl -u llmready-backend -n 50 | grep -i sentry
```

You should see: `Sentry initialized - Environment: production`

**Frontend:**
Open your production site, check browser console (should see initialization message)

### 2. Test Error Tracking

**Backend:**
```bash
curl https://your-domain.com/test-sentry
```

**Frontend:**
Open browser console on your site:
```javascript
throw new Error('Production test error');
```

Both errors should appear in respective Sentry projects within 30 seconds.

### 3. Verify in Sentry Dashboard

- **Backend**: https://sentry.io → Your backend production project
- **Frontend**: https://sentry.io → Your frontend production project

Check that:
- [ ] Errors appear
- [ ] Stack traces show original code (source maps working)
- [ ] Environment tagged as "production"
- [ ] Performance transactions are being captured

## 🔍 Troubleshooting

### Issue: Sentry Not Initialized

**Check:**
1. GitHub secrets are correctly set
2. Deployment logs show environment update
3. `.env` file on server has correct `SENTRY_DSN`

**Fix:**
```bash
ssh user@your-server
cd /opt/llmready/backend
nano .env  # Add SENTRY_DSN manually
sudo systemctl restart llmready-backend
```

### Issue: Frontend Source Maps Not Working

**Check:**
1. `SENTRY_AUTH_TOKEN` secret is set
2. Token has correct permissions
3. Build logs show "Uploading source maps to Sentry"

**Fix:**
- Create new Sentry auth token with `project:releases` and `project:write` scopes
- Update GitHub secret
- Re-run deployment

### Issue: Too Many Sentry Events

**Solution:**
Adjust sample rate on server:

```bash
ssh user@your-server
cd /opt/llmready/backend
nano .env  # Change SENTRY_TRACES_SAMPLE_RATE to 0.01 (1%)
sudo systemctl restart llmready-backend
```

## 📈 Monitoring Best Practices

### 1. Set Up Alerts (First Day)

In Sentry dashboard:
- Create alert for errors > 10 in 5 minutes
- Create alert for new issues
- Connect Slack or email notifications

### 2. Daily Checks (First Week)

- [ ] Review Sentry dashboard
- [ ] Check for new errors
- [ ] Monitor performance metrics
- [ ] Verify alerts are working

### 3. Weekly Reviews

- [ ] Review top 10 errors
- [ ] Check users affected
- [ ] Prioritize fixes
- [ ] Update ignored errors list

## 🎯 Quick Reference

### Deploy Command
```bash
./scripts/deploy.sh
```

### View Logs
```bash
# Backend
ssh user@server 'sudo journalctl -u llmready-backend -f'

# Deployment
# Go to GitHub Actions tab
```

### Check Sentry
```bash
# Backend errors
curl https://your-domain.com/test-sentry

# Check dashboard
# https://sentry.io → Projects → Select your project
```

## 📚 Related Documentation

- **Production Deployment Guide**: [`MONITORING_PRODUCTION_DEPLOYMENT.md`](./MONITORING_PRODUCTION_DEPLOYMENT.md)
- **Complete Setup Guide**: [`MONITORING_SETUP_GUIDE.md`](./MONITORING_SETUP_GUIDE.md)
- **Implementation Summary**: [`MONITORING_SUMMARY.md`](./MONITORING_SUMMARY.md)

---

**Ready to deploy?** Run `./scripts/deploy.sh` and your production monitoring will be automatically configured! 🚀
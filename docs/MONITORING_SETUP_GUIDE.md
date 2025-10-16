# Centralized Monitoring & Error Tracking Setup Guide

This guide explains how to set up **Sentry** for centralized monitoring, error tracking, and performance monitoring across the LLMReady platform (backend and frontend).

## Table of Contents

1. [Why Monitoring Matters](#why-monitoring-matters)
2. [What is Sentry?](#what-is-sentry)
3. [Setting Up Sentry](#setting-up-sentry)
4. [Backend Configuration](#backend-configuration)
5. [Frontend Configuration](#frontend-configuration)
6. [Testing Your Setup](#testing-your-setup)
7. [Understanding Sentry Dashboard](#understanding-sentry-dashboard)
8. [Best Practices](#best-practices)
9. [Troubleshooting](#troubleshooting)

---

## Why Monitoring Matters

Centralized monitoring is **crucial** for production applications because it:

- **Detects issues proactively**: Know about errors before users report them
- **Provides context**: Full stack traces, user actions, and environment details
- **Tracks performance**: Identify slow endpoints and bottlenecks
- **Reduces MTTR**: Mean Time To Resolution - fix issues faster
- **Improves user experience**: Fix bugs that impact users most
- **Enables data-driven decisions**: Prioritize fixes based on actual impact

---

## What is Sentry?

[Sentry](https://sentry.io) is an industry-standard error tracking and performance monitoring platform that provides:

- **Error Tracking**: Automatic capture of exceptions with full context
- **Performance Monitoring**: Track slow transactions and database queries
- **Release Tracking**: Connect errors to specific code versions
- **Alerting**: Get notified via email, Slack, PagerDuty, etc.
- **Source Maps**: See original code in stack traces (not minified)
- **User Context**: Know which users are affected by errors

**Free Tier**: Sentry offers a generous free tier (5,000 errors/month) perfect for getting started.

---

## Setting Up Sentry

### Step 1: Create a Sentry Account

1. Go to [sentry.io](https://sentry.io) and sign up
2. Create an organization (e.g., "LLMReady" or your company name)

### Step 2: Create Projects

You need **two separate projects**:

#### Backend Project (Python/FastAPI)

1. Click **"Create Project"**
2. Select platform: **Python**
3. Set alert frequency: **On every new issue**
4. Name: `llmready-backend`
5. Copy the **DSN** (Data Source Name) - looks like: `https://xxxxx@sentry.io/xxxxxx`

#### Frontend Project (React)

1. Click **"Create Project"**
2. Select platform: **React**
3. Set alert frequency: **On every new issue**
4. Name: `llmready-frontend`
5. Copy the **DSN**

### Step 3: Get Auth Token (Optional - for Source Maps)

For frontend source map uploads:

1. Go to **Settings** → **Auth Tokens**
2. Click **"Create New Token"**
3. Scopes: Select **`project:releases`** and **`project:write`**
4. Name: `llmready-frontend-upload`
5. Copy the token

---

## Backend Configuration

### 1. Install Dependencies

Dependencies are already added to [`requirements.txt`](../backend/requirements.txt):

```bash
cd backend
pip install -r requirements.txt
```

This installs:
- `sentry-sdk[fastapi]==1.40.0` - Sentry SDK with FastAPI integration
- `python-json-logger==2.0.7` - Structured JSON logging

### 2. Configure Environment Variables

Update your `.env` file (or `.env.production` for production):

```bash
# Monitoring & Logging
SENTRY_DSN=https://your-backend-dsn@sentry.io/project-id
SENTRY_TRACES_SAMPLE_RATE=0.1  # 10% of transactions (adjust based on traffic)
SENTRY_PROFILES_SAMPLE_RATE=0.1
LOG_LEVEL=INFO
ENVIRONMENT=production  # or development, staging, etc.
```

**Important**: 
- Development: You can leave `SENTRY_DSN` empty to disable Sentry locally
- Production: **Always set the DSN** in production

### 3. Implementation Details

The monitoring is already configured in:

- **[`backend/app/core/logging_config.py`](../backend/app/core/logging_config.py)**: Sentry initialization and structured logging
- **[`backend/app/main.py`](../backend/app/main.py)**: Global exception handler and monitoring setup

Key features:
- ✅ Automatic error capture with full stack traces
- ✅ Performance monitoring for all API endpoints
- ✅ SQLAlchemy query tracking
- ✅ Celery task monitoring
- ✅ Redis operation tracking
- ✅ Structured JSON logging (production)
- ✅ Global exception handler with Sentry integration

### 4. Restart Backend

```bash
# Development
python -m uvicorn app.main:app --reload

# Production (via systemd)
sudo systemctl restart llmready-backend
```

---

## Frontend Configuration

### 1. Install Dependencies

Dependencies are already added to [`package.json`](../frontend/package.json):

```bash
cd frontend
npm install
```

This installs:
- `@sentry/react` - Sentry SDK for React
- `@sentry/vite-plugin` - Vite plugin for source map uploads

### 2. Configure Environment Variables

#### Development (`.env`):

```bash
VITE_API_URL=http://localhost:8000

# Monitoring (optional in development)
VITE_SENTRY_DSN=
VITE_ENVIRONMENT=development
VITE_SENTRY_DEBUG=false
```

#### Production (`.env.production`):

```bash
VITE_API_URL=https://your-domain.com

# Monitoring (required in production)
VITE_SENTRY_DSN=https://your-frontend-dsn@sentry.io/project-id
VITE_ENVIRONMENT=production

# For source map uploads (highly recommended)
VITE_SENTRY_AUTH_TOKEN=your_auth_token_from_sentry
VITE_SENTRY_ORG=your-org-slug
VITE_SENTRY_PROJECT=llmready-frontend
```

### 3. Implementation Details

The monitoring is already configured in:

- **[`frontend/src/lib/sentry.ts`](../frontend/src/lib/sentry.ts)**: Sentry initialization and utilities
- **[`frontend/src/main.tsx`](../frontend/src/main.tsx)**: Error boundary and Sentry setup
- **[`frontend/vite.config.ts`](../frontend/vite.config.ts)**: Source map upload configuration

Key features:
- ✅ Automatic error capture with React error boundaries
- ✅ Performance monitoring for page loads and navigation
- ✅ User context tracking (set on login)
- ✅ Breadcrumbs for debugging user actions
- ✅ Source map uploads (production builds)
- ✅ Network error filtering

### 4. Build and Deploy

```bash
# Development
npm run dev

# Production build (uploads source maps if configured)
npm run build
```

---

## Testing Your Setup

### Backend Testing

#### Test 1: Health Check

```bash
curl http://localhost:8000/health
```

Should return `200 OK` with database status.

#### Test 2: Trigger an Error

Create a test endpoint or modify existing code to throw an exception:

```python
@app.get("/test-sentry")
async def test_sentry():
    """Test Sentry error tracking"""
    raise ValueError("This is a test error for Sentry!")
```

Then visit: `http://localhost:8000/test-sentry`

Check Sentry dashboard - you should see the error within seconds!

#### Test 3: Check Logs

```bash
# View logs
tail -f /var/log/llmready/app.log

# Or if running in terminal
# Logs should show: "Sentry initialized - Environment: production"
```

### Frontend Testing

#### Test 1: Console Check

Open browser console after loading the app. You should see:

```
Sentry initialized - Environment: development
```

#### Test 2: Trigger an Error

Use the browser console:

```javascript
// This will be caught by Sentry
throw new Error("Test error from console");
```

Check Sentry dashboard for the error.

#### Test 3: Error Boundary

Modify a component to throw an error:

```typescript
// Add this to any component
if (someCondition) {
  throw new Error("Test React error boundary");
}
```

The error boundary should display a fallback UI and report to Sentry.

---

## Understanding Sentry Dashboard

### Issues Tab

- **New Issues**: Recently discovered errors
- **For Review**: Issues that need attention
- **Ignored**: Issues you've marked as non-critical
- **Resolved**: Fixed issues

### Key Metrics

- **Users Affected**: How many unique users experienced this error
- **Frequency**: How often the error occurs
- **First Seen**: When error first appeared
- **Last Seen**: Most recent occurrence
- **Environment**: production, staging, development

### Issue Details

Each issue shows:
- **Stack Trace**: Full error stack with file names and line numbers
- **Breadcrumbs**: User actions leading to the error
- **Tags**: Environment, release, user info, etc.
- **Context**: Request data, user agent, etc.

### Performance Tab

- **Transaction Summary**: Slowest API endpoints/pages
- **Web Vitals**: LCP, FID, CLS metrics
- **Database Queries**: Slow queries identified

---

## Best Practices

### 1. Environment Separation

Always use different Sentry projects for:
- **Production**: Real user data
- **Staging**: Pre-production testing
- **Development**: Local testing (or disable Sentry)

### 2. Sample Rates

Adjust based on traffic:

```python
# High traffic site (100k+ requests/day)
SENTRY_TRACES_SAMPLE_RATE=0.01  # 1%

# Medium traffic (10k-100k requests/day)  
SENTRY_TRACES_SAMPLE_RATE=0.1   # 10%

# Low traffic (<10k requests/day)
SENTRY_TRACES_SAMPLE_RATE=1.0   # 100%
```

### 3. Add User Context

In your authentication code:

```python
# Backend (after login)
from app.core.logging_config import sentry_sdk

sentry_sdk.set_user({
    "id": user.id,
    "email": user.email,
    "username": user.email.split("@")[0]
})
```

```typescript
// Frontend (after login)
import { setSentryUser } from '@/lib/sentry';

setSentryUser({
  id: user.id,
  email: user.email,
  username: user.name
});
```

### 4. Set Up Alerts

In Sentry:
1. Go to **Alerts** → **Create Alert**
2. Configure:
   - **When**: Error count > 10 in 1 hour
   - **Then**: Send email/Slack notification
   - **To**: Your team

### 5. Release Tracking

Tag your releases:

```bash
# Backend (use git tag)
export SENTRY_RELEASE=$(git rev-parse HEAD)

# Frontend (automatically handled by Vite plugin)
```

### 6. Ignore Non-Critical Errors

Some errors can be safely ignored:
- Browser extension errors
- Ad blocker errors
- Network timeout errors (sometimes)

Configure in [`frontend/src/lib/sentry.ts`](../frontend/src/lib/sentry.ts):

```typescript
ignoreErrors: [
  'ResizeObserver loop limit exceeded',
  'Non-Error promise rejection captured',
  // Add more as needed
]
```

---

## Troubleshooting

### Issue: No Events in Sentry

**Checklist**:
- ✅ DSN is correctly set in `.env`
- ✅ DSN is actually loaded (check logs: "Sentry initialized")
- ✅ You've triggered an actual error
- ✅ Sample rate isn't 0
- ✅ No firewall blocking sentry.io

**Test**:
```python
# Backend
import sentry_sdk
sentry_sdk.capture_message("Test message")
```

```typescript
// Frontend  
import { captureMessage } from '@/lib/sentry';
captureMessage("Test message");
```

### Issue: Source Maps Not Working

**Frontend**:
- Ensure `VITE_SENTRY_AUTH_TOKEN` is set
- Check build output for "Uploading source maps to Sentry"
- Verify token has correct permissions

**Backend**:
- Python source maps work automatically if code is deployed with source

### Issue: Too Many Events

**Solutions**:
1. Reduce sample rates
2. Filter known errors in `beforeSend`
3. Upgrade Sentry plan
4. Use Sentry's rate limiting features

### Issue: Sensitive Data in Events

**Solutions**:
1. Set `send_default_pii=False` (already configured)
2. Use `before_send` to scrub data
3. Configure Sentry's data scrubbing rules

Example:
```python
def before_send(event, hint):
    # Remove sensitive data
    if 'request' in event:
        if 'headers' in event['request']:
            event['request']['headers'].pop('Authorization', None)
    return event
```

---

## Quick Reference

### Backend Environment Variables

```bash
SENTRY_DSN=                        # Your Sentry DSN
SENTRY_TRACES_SAMPLE_RATE=0.1      # 10% transaction sampling
SENTRY_PROFILES_SAMPLE_RATE=0.1    # 10% profile sampling
LOG_LEVEL=INFO                     # Logging level
ENVIRONMENT=production             # Environment name
```

### Frontend Environment Variables

```bash
VITE_SENTRY_DSN=                   # Your Sentry DSN
VITE_ENVIRONMENT=production        # Environment name
VITE_SENTRY_AUTH_TOKEN=            # For source map uploads
VITE_SENTRY_ORG=                   # Your org slug
VITE_SENTRY_PROJECT=               # Your project slug
```

### Useful Commands

```bash
# Backend: Install dependencies
pip install -r requirements.txt

# Backend: Restart service
sudo systemctl restart llmready-backend

# Frontend: Install dependencies
npm install

# Frontend: Build with source maps
npm run build

# View backend logs
tail -f /var/log/llmready/app.log

# Test Sentry capture
curl http://localhost:8000/test-sentry
```

---

## Next Steps

1. ✅ Set up Sentry account and projects
2. ✅ Configure environment variables
3. ✅ Test error capturing
4. ✅ Set up alerting rules
5. ✅ Add user context on login
6. ✅ Monitor dashboard daily (initially)
7. ✅ Set up Slack/email notifications
8. 📊 Create a monitoring dashboard (optional)

---

## Support & Resources

- **Sentry Docs**: https://docs.sentry.io/
- **FastAPI Integration**: https://docs.sentry.io/platforms/python/guides/fastapi/
- **React Integration**: https://docs.sentry.io/platforms/javascript/guides/react/
- **Performance Monitoring**: https://docs.sentry.io/product/performance/
- **Sentry Support**: https://sentry.io/support/

---

**Remember**: Monitoring is not "set and forget" - regularly review your Sentry dashboard to catch issues early and improve your platform! 🚀
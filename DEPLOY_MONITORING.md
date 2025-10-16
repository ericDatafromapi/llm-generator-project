# Deploy Monitoring to Production - Simple Steps

## Step 1: Create Production Sentry Projects (5 minutes)

1. Go to https://sentry.io
2. Click **"Create Project"**
3. Choose **Python** → Name: `llmready-backend-production` → Copy the DSN
4. Click **"Create Project"** again
5. Choose **React** → Name: `llmready-frontend-production` → Copy the DSN

## Step 2: Get Sentry Auth Token (2 minutes)

1. Go to https://sentry.io/settings/account/api/auth-tokens/
2. Click **"Create New Token"**
3. Name: `GitHub Actions`
4. Select scopes: `project:releases` and `project:write`
5. Click **"Create Token"** → Copy the token

## Step 3: Add GitHub Secrets (3 minutes)

1. Go to your GitHub repository
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **"New repository secret"** and add these 5 secrets:

| Secret Name | Where to Get Value |
|------------|-------------------|
| `BACKEND_SENTRY_DSN` | Backend project DSN from Step 1 |
| `FRONTEND_SENTRY_DSN` | Frontend project DSN from Step 1 |
| `SENTRY_AUTH_TOKEN` | Token from Step 2 |
| `SENTRY_ORG` | Your Sentry org slug (see URL: sentry.io/organizations/YOUR-ORG/) |
| `SENTRY_FRONTEND_PROJECT` | `llmready-frontend-production` |

## Step 4: Deploy (1 minute)

Run your deployment script:

```bash
./scripts/deploy.sh
```

Type `deploy` when prompted.

Wait for GitHub Actions to complete (check the link it shows).

## Step 5: Verify It's Working (2 minutes)

### Test Backend:
```bash
curl https://your-domain.com/test-sentry
```

### Test Frontend:
1. Open your production site
2. Open browser console (F12)
3. Type: `throw new Error('Test error');`
4. Press Enter

### Check Sentry:
Go to https://sentry.io → Projects

You should see both test errors appear within 30 seconds!

## Step 6: Set Up Alerts (3 minutes)

1. Go to https://sentry.io
2. Select your **backend production project**
3. Go to **Alerts** → **Create Alert Rule**
4. Choose: **Errors** → **Number of Errors**
5. Set: "Alert when errors > 10 in 5 minutes"
6. Add your email
7. Click **Save Rule**
8. Repeat for **frontend production project**

---

## Done! 🎉

You're now monitoring errors in production. Any errors will:
- ✅ Appear in Sentry dashboard
- ✅ Show full stack traces with source code
- ✅ Include user and environment context
- ✅ Trigger email alerts

Check Sentry daily at first, then weekly once stable.

---

## Quick Troubleshooting

**No errors showing in Sentry?**
1. Check GitHub secrets are correctly set
2. SSH to server: `sudo journalctl -u llmready-backend | grep -i sentry`
3. Should see: "Sentry initialized - Environment: production"

**Source maps not working (minified code)?**
- Re-check `SENTRY_AUTH_TOKEN` has correct permissions
- Verify token scopes: `project:releases` and `project:write`
# 🚀 Deployment Quick Start Guide

Get your application deployed in production in 5 simple steps!

---

## Prerequisites

- ✅ GitHub repository with your code
- ✅ Production server (Ubuntu 20.04+)
- ✅ Domain name pointing to your server
- ✅ GitHub Personal Access Token ([create one here](https://github.com/settings/tokens))

---

## Step 1: Setup Your Server (5-10 minutes)

### Option A: Automated Setup (Recommended)

```bash
# On your local machine, upload the setup script
scp scripts/server-setup.sh root@your-server-ip:/tmp/

# SSH into your server
ssh root@your-server-ip

# Run the setup script
cd /tmp
chmod +x server-setup.sh
sudo bash server-setup.sh
```

The script will:
- Install Docker, Docker Compose, Nginx, and other dependencies
- Create deployment user and directories
- Configure firewall
- Set up nginx
- Optionally configure SSL

### Option B: Manual Setup

See the detailed steps in [`CI_CD_DEPLOYMENT_GUIDE.md`](CI_CD_DEPLOYMENT_GUIDE.md#option-2-manual-setup)

---

## Step 2: Configure GitHub Secrets (3-5 minutes)

1. Go to your repository on GitHub
2. Navigate to **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Add these secrets (see [`.github/SECRETS_TEMPLATE.md`](.github/SECRETS_TEMPLATE.md) for details):

### Essential Secrets

```
SSH_PRIVATE_KEY          # Your deployment SSH private key
SERVER_HOST              # e.g., 123.45.67.89
SERVER_USER              # e.g., llmready
PRODUCTION_DOMAIN        # e.g., llmready.com
PRODUCTION_API_URL       # e.g., https://llmready.com/api
STRIPE_PUBLIC_KEY        # pk_live_...
MAIL_SERVER              # e.g., smtp.gmail.com
MAIL_PORT                # e.g., 587
MAIL_USERNAME            # your-email@gmail.com
MAIL_PASSWORD            # your-app-password
NOTIFICATION_EMAIL       # where to receive alerts
```

💡 **SSH Key Options:**

**Option 1: Use your existing SSH key** (simpler, see [`SSH_KEY_CLARIFICATION.md`](SSH_KEY_CLARIFICATION.md))
```bash
cat ~/.ssh/id_ed25519  # or ~/.ssh/id_rsa
# Copy this to GitHub Secret: SSH_PRIVATE_KEY
# Public key already on server ✅
```

**Option 2: Create dedicated key** (more secure, recommended)
```bash
ssh-keygen -t ed25519 -C "github-actions" -f ~/.ssh/github_actions_deploy
cat ~/.ssh/github_actions_deploy      # Private key → GitHub Secret
cat ~/.ssh/github_actions_deploy.pub  # Public key → Server
```

See **[SSH Key Setup Guide](SSH_KEY_CLARIFICATION.md)** for detailed comparison.

---

## Step 3: Create Production Environment File (2 minutes)

SSH into your server and create `/opt/llmready/backend/.env`:

```bash
ssh llmready@your-server-ip
cd /opt/llmready
mkdir -p backend
nano backend/.env
```

Paste this content (update with your values):

```env
# Database
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost:5432/llmready_prod
REDIS_URL=redis://localhost:6379/0

# Security
SECRET_KEY=your-super-secret-key-minimum-32-characters-long
ENVIRONMENT=production

# Stripe
STRIPE_SECRET_KEY=sk_live_YOUR_SECRET_KEY
STRIPE_WEBHOOK_SECRET=whsec_YOUR_WEBHOOK_SECRET

# SendGrid
SENDGRID_API_KEY=SG.YOUR_API_KEY
SENDGRID_FROM_EMAIL=noreply@yourdomain.com
SENDGRID_FROM_NAME=LLMReady

# Frontend
FRONTEND_URL=https://yourdomain.com

# Celery
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2
```

Save and exit (Ctrl+X, then Y, then Enter)

---

## Step 4: Push Your Code to GitHub (1 minute)

```bash
# If not already done
git add .
git commit -m "Add CI/CD configuration"
git push origin main
```

---

## Step 5: Deploy from VSCode! (30 seconds)

### Method 1: Using the Deployment Script

```bash
# Set your GitHub token (one-time setup)
export GITHUB_TOKEN="your_github_personal_access_token"

# Deploy!
./scripts/deploy.sh
```

### Method 2: Using VSCode Command Palette

1. Press `Cmd+Shift+P` (Mac) or `Ctrl+Shift+P` (Windows/Linux)
2. Type: **Tasks: Run Task**
3. Select: **🚀 Deploy to Production**
4. Type `deploy` to confirm
5. Done! ✨

### Method 3: From GitHub Actions UI

1. Go to your repository on GitHub
2. Click **Actions** tab
3. Click **Deploy to Production**
4. Click **Run workflow**
5. Type `deploy` and click **Run workflow**

---

## 🎉 That's It!

Your deployment will:
- ✅ Run all tests
- ✅ Build frontend
- ✅ Deploy backend with zero downtime
- ✅ Run database migrations
- ✅ Deploy frontend
- ✅ Send you an email notification

View progress at: `https://github.com/YOUR_USERNAME/YOUR_REPO/actions`

---

## 📊 Verify Deployment

```bash
# Check backend health
curl https://yourdomain.com/api/health

# Check frontend
curl https://yourdomain.com

# View logs on server
ssh llmready@your-server-ip
cd /opt/llmready
docker-compose logs -f backend
```

---

## 🔄 Daily Workflow

### Making Changes and Deploying

```bash
# 1. Create feature branch
git checkout -b feature/my-feature

# 2. Make your changes
# ... edit files ...

# 3. Commit and push
git add .
git commit -m "Add awesome feature"
git push origin feature/my-feature

# 4. Create Pull Request on GitHub
# Tests run automatically ✅

# 5. Merge PR after tests pass

# 6. Deploy to production
git checkout main
git pull origin main
./scripts/deploy.sh
```

---

## 🆘 Quick Troubleshooting

### Deployment Fails with SSH Error

```bash
# Test SSH connection
ssh -i ~/.ssh/llmready_deploy llmready@your-server-ip

# Check key permissions
chmod 600 ~/.ssh/llmready_deploy
```

### Not Receiving Email Notifications

- Check spam folder
- Verify MAIL_* secrets in GitHub
- For Gmail, use an [App Password](https://support.google.com/accounts/answer/185833)

### Backend Not Starting

```bash
# SSH to server
ssh llmready@your-server-ip
cd /opt/llmready

# Check logs
docker-compose logs backend

# Check environment file
cat backend/.env

# Restart services
docker-compose restart
```

### Frontend Not Loading

```bash
# Check nginx configuration
sudo nginx -t

# Check nginx logs
sudo tail -f /var/log/nginx/error.log

# Restart nginx
sudo systemctl restart nginx
```

---

## 📚 Need More Details?

- **Full Guide**: [`CI_CD_DEPLOYMENT_GUIDE.md`](CI_CD_DEPLOYMENT_GUIDE.md)
- **Secrets Setup**: [`.github/SECRETS_TEMPLATE.md`](.github/SECRETS_TEMPLATE.md)
- **PR Testing**: See [`.github/workflows/pr-test.yml`](.github/workflows/pr-test.yml)
- **Deployment Workflow**: See [`.github/workflows/deploy-production.yml`](.github/workflows/deploy-production.yml)

---

## 💡 Pro Tips

1. **Always test locally first**: `docker-compose up` before deploying
2. **Use feature branches**: Never push directly to main
3. **Monitor your deploys**: Check GitHub Actions after each deployment
4. **Keep backups**: Automatic backups are created, but verify them
5. **SSL renewal**: Certbot auto-renews, but check occasionally

---

## 🎯 What You've Set Up

✅ **Automated PR Testing**
- Every PR is tested automatically
- Email notifications on pass/fail
- Prevents broken code from reaching main

✅ **One-Command Deployment**
- Deploy from VSCode with `./scripts/deploy.sh`
- Zero-downtime deployments
- Automatic rollback on failure

✅ **Production-Ready Setup**
- Docker containerization
- Nginx reverse proxy
- SSL/HTTPS support
- Automated backups
- Health monitoring

✅ **Complete CI/CD Pipeline**
- GitHub Actions workflows
- Automated testing
- Continuous deployment
- Email notifications

---

## 🚀 Start Deploying!

You're all set! Run your first deployment:

```bash
./scripts/deploy.sh
```

Happy deploying! 🎉
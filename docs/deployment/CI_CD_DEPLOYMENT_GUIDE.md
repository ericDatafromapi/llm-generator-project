# 🚀 CI/CD & Deployment Guide

Complete guide for setting up continuous integration, continuous deployment, and deploying your LLMReady application to production.

## 📋 Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [GitHub Repository Setup](#github-repository-setup)
4. [Server Setup](#server-setup)
5. [GitHub Actions Configuration](#github-actions-configuration)
6. [Deploying from VSCode](#deploying-from-vscode)
7. [PR Testing Workflow](#pr-testing-workflow)
8. [Production Deployment Workflow](#production-deployment-workflow)
9. [Rollback Procedures](#rollback-procedures)
10. [Troubleshooting](#troubleshooting)

---

## Overview

This project includes two automated workflows:

1. **PR Testing** - Automatically tests every pull request
2. **Production Deployment** - Deploys to production server

Both workflows include email notifications on success/failure.

---

## Prerequisites

### Required Tools

- GitHub repository with push access
- Production server (Ubuntu 20.04+ recommended)
- Domain name pointing to your server
- GitHub Personal Access Token with `repo` and `workflow` scopes

### Required Accounts & Keys

- GitHub account
- Stripe account (publishable and secret keys)
- SendGrid account (API key)
- Email account for SMTP notifications

---

## GitHub Repository Setup

### 1. Push Your Code to GitHub

```bash
# Initialize git if not already done
git init

# Add all files
git add .

# Create initial commit
git commit -m "Initial commit"

# Add remote (replace with your repo URL)
git remote add origin git@github.com:yourusername/llmready.git

# Push to main branch
git push -u origin main
```

### 2. Configure GitHub Secrets

Go to your repository → Settings → Secrets and variables → Actions → New repository secret

Add the following secrets:

#### Server Access Secrets
```
SSH_PRIVATE_KEY          # Private SSH key for server access
SERVER_HOST              # Your server IP or domain (e.g., 123.45.67.89)
SERVER_USER              # Server username (e.g., llmready)
```

#### Domain & API Secrets
```
PRODUCTION_DOMAIN        # Your production domain (e.g., llmready.com)
PRODUCTION_API_URL       # Your API URL (e.g., https://llmready.com/api)
```

#### Stripe Secrets
```
STRIPE_PUBLIC_KEY        # Your Stripe publishable key (pk_live_...)
```

#### Email Notification Secrets
```
MAIL_SERVER             # SMTP server (e.g., smtp.gmail.com)
MAIL_PORT               # SMTP port (e.g., 587)
MAIL_USERNAME           # SMTP username
MAIL_PASSWORD           # SMTP password or app password
NOTIFICATION_EMAIL      # Email to receive deployment notifications
```

### 3. Generate SSH Key for Deployment

On your local machine:

```bash
# Generate SSH key pair
ssh-keygen -t ed25519 -C "github-actions@llmready" -f ~/.ssh/llmready_deploy

# Copy public key (you'll add this to server)
cat ~/.ssh/llmready_deploy.pub

# Copy private key (you'll add this to GitHub Secrets)
cat ~/.ssh/llmready_deploy
```

Add the **private key** to GitHub Secrets as `SSH_PRIVATE_KEY`.
Save the **public key** for the server setup step.

---

## Server Setup

### Option 1: Automated Setup (Recommended)

1. **Upload the setup script to your server:**

```bash
scp scripts/server-setup.sh root@your-server-ip:/tmp/
```

2. **SSH into your server:**

```bash
ssh root@your-server-ip
```

3. **Run the setup script:**

```bash
cd /tmp
chmod +x server-setup.sh
sudo bash server-setup.sh
```

4. **Follow the prompts:**
   - Enter your GitHub Actions public key when prompted
   - Enter your domain name
   - Choose whether to set up SSL

### Option 2: Manual Setup

If you prefer manual setup, follow these steps:

#### 1. Update System

```bash
apt-get update && apt-get upgrade -y
```

#### 2. Install Docker

```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
systemctl enable docker
systemctl start docker
```

#### 3. Install Docker Compose

```bash
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose
```

#### 4. Install Nginx

```bash
apt-get install -y nginx certbot python3-certbot-nginx
```

#### 5. Create Deployment User

```bash
useradd -m -s /bin/bash llmready
usermod -aG docker llmready
```

#### 6. Set Up SSH Access

```bash
mkdir -p /home/llmready/.ssh
chmod 700 /home/llmready/.ssh

# Add your GitHub Actions public key
echo "your-public-key-here" >> /home/llmready/.ssh/authorized_keys
chmod 600 /home/llmready/.ssh/authorized_keys
chown -R llmready:llmready /home/llmready/.ssh
```

#### 7. Create Directories

```bash
mkdir -p /opt/llmready/backups
mkdir -p /var/www/llmready
chown -R llmready:llmready /opt/llmready
chown -R www-data:www-data /var/www/llmready
```

#### 8. Configure Nginx

Create `/etc/nginx/sites-available/llmready`:

```nginx
server {
    listen 80;
    listen [::]:80;
    server_name yourdomain.com www.yourdomain.com;
    
    root /var/www/llmready/dist;
    index index.html;
    
    gzip on;
    gzip_vary on;
    gzip_min_length 1000;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/json;
    
    location / {
        try_files $uri $uri/ /index.html;
    }
    
    location /api {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        proxy_read_timeout 300s;
        proxy_connect_timeout 300s;
    }
    
    location /health {
        proxy_pass http://localhost:8000/health;
        access_log off;
    }
    
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

Enable site:
```bash
ln -s /etc/nginx/sites-available/llmready /etc/nginx/sites-enabled/
rm /etc/nginx/sites-enabled/default
nginx -t
systemctl reload nginx
```

#### 9. Set Up SSL (Optional but Recommended)

```bash
certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

#### 10. Configure Firewall

```bash
ufw enable
ufw allow ssh
ufw allow http
ufw allow https
```

### Create Production Environment File

On your server, create `/opt/llmready/backend/.env`:

```env
# Database
DATABASE_URL=postgresql://postgres:your_password@localhost:5432/llmready_prod
REDIS_URL=redis://localhost:6379/0

# Security
SECRET_KEY=your-super-secret-key-here-min-32-chars
ENVIRONMENT=production

# Stripe
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...

# SendGrid
SENDGRID_API_KEY=SG....
SENDGRID_FROM_EMAIL=noreply@yourdomain.com
SENDGRID_FROM_NAME=LLMReady

# Frontend
FRONTEND_URL=https://yourdomain.com

# Optional: Celery
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2
```

---

## GitHub Actions Configuration

The workflows are already created in `.github/workflows/`:

### 1. PR Test Workflow ([`.github/workflows/pr-test.yml`](.github/workflows/pr-test.yml:1))

**Triggers:**
- Every pull request to `main` or `develop`
- Every push to `main` or `develop`

**What it does:**
- Runs backend tests with PostgreSQL and Redis
- Runs frontend linting and build
- Tests Docker Compose configuration
- Sends email notification with results

### 2. Production Deployment Workflow ([`.github/workflows/deploy-production.yml`](.github/workflows/deploy-production.yml:1))

**Triggers:**
- Manual trigger from GitHub Actions UI or VSCode
- Automatic trigger on push to `main` (excluding docs)

**What it does:**
- Validates deployment confirmation
- Runs all tests
- Builds production frontend
- Deploys backend to server via SSH
- Deploys frontend to server
- Runs database migrations
- Performs zero-downtime deployment
- Sends email notification with results

---

## Deploying from VSCode

### Quick Deployment

The easiest way to deploy is using the deployment script:

```bash
# Make the script executable (if not already done)
chmod +x scripts/deploy.sh

# Run deployment
./scripts/deploy.sh
```

### What the Script Does

1. Checks you're in a git repository
2. Detects repository owner and name from git remote
3. Prompts for GitHub Personal Access Token
4. Shows current branch and asks for confirmation
5. Triggers the GitHub Actions deployment workflow
6. Provides links to view the deployment progress

### Setting Environment Variables (Optional)

To avoid entering your token every time:

```bash
# Add to your ~/.bashrc or ~/.zshrc
export GITHUB_TOKEN="your_github_personal_access_token"
export GITHUB_REPO_OWNER="yourusername"
export GITHUB_REPO_NAME="llmready"
```

Then just run:
```bash
./scripts/deploy.sh
```

### VSCode Integrated Terminal

You can also add a task to VSCode. Create or edit [`.vscode/tasks.json`](.vscode/tasks.json:1):

```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "Deploy to Production",
      "type": "shell",
      "command": "./scripts/deploy.sh",
      "problemMatcher": [],
      "group": "build"
    }
  ]
}
```

Then use `Cmd+Shift+P` → `Tasks: Run Task` → `Deploy to Production`

---

## PR Testing Workflow

### How It Works

When you create a pull request:

1. **Automatic Trigger**: Workflow starts automatically
2. **Backend Tests**: 
   - Spins up PostgreSQL and Redis containers
   - Installs Python dependencies
   - Runs database migrations
   - Executes test suite
3. **Frontend Tests**:
   - Installs Node.js dependencies
   - Runs linter
   - Builds production bundle
4. **Docker Test**: Validates docker-compose.yml
5. **Notification**: Sends email with test results

### Viewing Results

- Check the PR page for status checks
- Click "Details" next to any check to view logs
- Receive email notification when tests complete

### Example PR Flow

```bash
# Create feature branch
git checkout -b feature/new-feature

# Make changes
# ... edit files ...

# Commit changes
git add .
git commit -m "Add new feature"

# Push branch
git push origin feature/new-feature

# Create PR on GitHub
# Tests run automatically
# Review results in PR and email
# Merge if all tests pass
```

---

## Production Deployment Workflow

### Manual Deployment from GitHub

1. Go to your repository on GitHub
2. Click **Actions** tab
3. Click **Deploy to Production** workflow
4. Click **Run workflow**
5. Type `deploy` in the confirmation field
6. Click **Run workflow**
7. Monitor progress and receive email notification

### Automatic Deployment

When you push directly to `main` branch:

```bash
git checkout main
git pull origin main
# Make changes
git add .
git commit -m "Update production"
git push origin main
# Deployment starts automatically
```

### Deployment Steps

The workflow performs these steps:

1. **Validation**: Confirms deployment request
2. **Testing**: Runs full test suite
3. **Build**: Creates production builds
4. **Backend Deployment**:
   - Creates backup of current deployment
   - Uploads new backend code
   - Runs database migrations
   - Restarts Docker containers with zero downtime
5. **Frontend Deployment**:
   - Creates backup of current frontend
   - Uploads new build
   - Updates nginx configuration
6. **Verification**: Checks deployment health
7. **Notification**: Sends success/failure email

### Zero-Downtime Deployment

The workflow uses Docker Compose's `--force-recreate` flag to ensure:
- Old containers continue running while new ones start
- New containers are health-checked before traffic switches
- Rollback happens automatically if health checks fail

---

## Rollback Procedures

### Quick Rollback

If a deployment fails or causes issues, you can quickly rollback:

#### SSH into Server

```bash
ssh llmready@your-server-ip
```

#### Rollback Backend

```bash
cd /opt/llmready

# List available backups
ls -lh backups/

# Choose the backup you want to restore
# Format: backup_YYYYMMDD_HHMMSS.tar.gz
BACKUP_FILE="backup_20250115_120000.tar.gz"

# Stop current services
docker-compose down

# Remove current version
rm -rf backend/ docker-compose.yml

# Restore backup
tar -xzf backups/$BACKUP_FILE

# Start services
docker-compose up -d

# Check logs
docker-compose logs -f
```

#### Rollback Frontend

```bash
cd /var/www/llmready

# List available backups
ls -lh backups/

# Choose the backup you want to restore
BACKUP_DIR="dist_20250115_120000"

# Remove current version
sudo rm -rf dist/

# Restore backup
sudo mv backups/$BACKUP_DIR dist/

# Set permissions
sudo chown -R www-data:www-data dist/

# Reload nginx
sudo systemctl reload nginx
```

### Database Rollback

If you need to rollback database migrations:

```bash
cd /opt/llmready/backend

# Check current migration
docker-compose run --rm backend alembic current

# Downgrade to previous version
docker-compose run --rm backend alembic downgrade -1

# Or downgrade to specific revision
docker-compose run --rm backend alembic downgrade <revision_id>
```

---

## Troubleshooting

### Common Issues

#### 1. SSH Connection Failed

**Problem**: Workflow fails with "Permission denied (publickey)"

**Solution**:
```bash
# On your local machine, test SSH connection
ssh -i ~/.ssh/llmready_deploy llmready@your-server-ip

# Verify the key is added to GitHub Secrets
# Verify the public key is in /home/llmready/.ssh/authorized_keys
```

#### 2. Docker Permission Denied

**Problem**: "permission denied while trying to connect to Docker daemon"

**Solution**:
```bash
# On server
sudo usermod -aG docker llmready
# Logout and login again for changes to take effect
```

#### 3. Nginx Configuration Error

**Problem**: nginx fails to reload

**Solution**:
```bash
# Test nginx configuration
sudo nginx -t

# Check error logs
sudo tail -f /var/log/nginx/error.log

# Fix configuration and reload
sudo systemctl reload nginx
```

#### 4. Database Connection Failed

**Problem**: Backend can't connect to database

**Solution**:
```bash
# Check if PostgreSQL is running
docker-compose ps

# Check backend logs
docker-compose logs backend

# Verify DATABASE_URL in .env
cat /opt/llmready/backend/.env | grep DATABASE_URL

# Test database connection
docker-compose exec postgres psql -U postgres -d llmready_prod -c "SELECT 1;"
```

#### 5. Port Already in Use

**Problem**: "port is already allocated"

**Solution**:
```bash
# Check what's using port 8000
sudo lsof -i :8000

# Stop the process or change port in docker-compose.yml
docker-compose down
docker-compose up -d
```

#### 6. Frontend Build Fails

**Problem**: "npm run build" fails in workflow

**Solution**:
- Check for TypeScript errors locally: `npm run build`
- Verify all environment variables in `.env.production`
- Check Node.js version compatibility

#### 7. Email Notifications Not Sending

**Problem**: No email notifications received

**Solution**:
- Verify all MAIL_* secrets are set correctly
- For Gmail, use an App Password, not your regular password
- Check spam folder
- Test SMTP credentials manually

### Viewing Logs

#### GitHub Actions Logs
1. Go to repository → Actions
2. Click on the workflow run
3. Click on job name
4. Expand steps to view logs

#### Server Logs
```bash
# Backend logs
docker-compose logs -f backend

# Nginx access logs
sudo tail -f /var/log/nginx/access.log

# Nginx error logs
sudo tail -f /var/log/nginx/error.log

# System logs
journalctl -f
```

### Health Checks

Check if your deployment is healthy:

```bash
# Check backend health
curl https://yourdomain.com/api/health

# Check frontend
curl https://yourdomain.com

# Check SSL certificate
curl -vI https://yourdomain.com 2>&1 | grep -i "SSL"

# Check all Docker containers
docker-compose ps

# Check container health
docker-compose ps | grep "healthy"
```

---

## Best Practices

### 1. Always Use Feature Branches

```bash
# Create feature branch
git checkout -b feature/new-feature

# Make changes and commit
git add .
git commit -m "Add feature"

# Push and create PR
git push origin feature/new-feature
```

### 2. Keep Main Branch Protected

Configure branch protection rules on GitHub:
- Require pull request reviews
- Require status checks to pass
- No direct pushes to main

### 3. Regular Backups

Set up automated backups:

```bash
# Add to server crontab
0 2 * * * cd /opt/llmready && tar -czf backups/scheduled_$(date +\%Y\%m\%d_\%H\%M\%S).tar.gz backend/ docker-compose.yml

# Keep only last 7 days
0 3 * * * find /opt/llmready/backups -name "scheduled_*.tar.gz" -mtime +7 -delete
```

### 4. Monitor Your Application

Set up monitoring for:
- Server resources (CPU, memory, disk)
- Application errors
- Response times
- Database performance

### 5. Keep Dependencies Updated

Regularly update dependencies:

```bash
# Backend
pip list --outdated

# Frontend
npm outdated

# Update and test before deploying
```

---

## Quick Reference

### Deploy from VSCode
```bash
./scripts/deploy.sh
```

### View Deployment Status
```
https://github.com/yourusername/yourrepo/actions
```

### SSH to Server
```bash
ssh llmready@your-server-ip
```

### View Logs
```bash
docker-compose logs -f backend
```

### Restart Services
```bash
docker-compose restart
```

### Check Health
```bash
curl https://yourdomain.com/api/health
```

---

## Need Help?

If you encounter issues not covered here:

1. Check the workflow logs on GitHub
2. Check server logs: `docker-compose logs`
3. Review this guide's troubleshooting section
4. Create an issue on the repository

---

## Summary

You now have:
- ✅ Automated PR testing with email notifications
- ✅ One-command deployment from VSCode
- ✅ Zero-downtime production deployments
- ✅ Automatic backups and rollback capability
- ✅ SSL/HTTPS support
- ✅ Email notifications for all deployments

Happy deploying! 🚀
# 🚀 LLMReady - Production Deployment Guide

**Version**: 1.0  
**Last Updated**: October 15, 2025  
**Status**: Production Ready

---

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Architecture Overview](#architecture-overview)
3. [Environment Setup](#environment-setup)
4. [Database Configuration](#database-configuration)
5. [Backend Deployment](#backend-deployment)
6. [Frontend Deployment](#frontend-deployment)
7. [Celery & Redis Setup](#celery--redis-setup)
8. [Stripe Configuration](#stripe-configuration)
9. [Email Configuration](#email-configuration)
10. [Security Checklist](#security-checklist)
11. [Monitoring & Logging](#monitoring--logging)
12. [Backup & Recovery](#backup--recovery)
13. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Services
- **VPS/Cloud Server**: 2+ CPUs, 4GB+ RAM
- **Domain**: Your custom domain with DNS access
- **PostgreSQL**: 14+ (managed or self-hosted)
- **Redis**: 6+ (managed or self-hosted)
- **Stripe Account**: For payments
- **SendGrid Account**: For emails

### Required Tools
```bash
# On your server
- Docker & Docker Compose
- Nginx
- Python 3.11+
- Node.js 18+
- Git
- SSL Certificate (Let's Encrypt)
```

---

## Architecture Overview

```
┌─────────────────────────────────────────────────┐
│           User Browser (HTTPS)                   │
└──────────────────┬──────────────────────────────┘
                   │
           ┌───────▼───────┐
           │     Nginx     │ (Reverse Proxy + SSL)
           │  Port 80/443  │
           └───────┬───────┘
                   │
        ┌──────────┴──────────┐
        │                     │
   ┌────▼────┐          ┌─────▼─────┐
   │ Frontend│          │  Backend  │
   │ (React) │          │ (FastAPI) │
   │ Port 80 │          │ Port 8000 │
   └─────────┘          └─────┬─────┘
                              │
                    ┌─────────┴─────────┐
                    │                   │
              ┌─────▼─────┐      ┌──────▼──────┐
              │PostgreSQL │      │   Redis     │
              │Port 5432  │      │  Port 6379  │
              └───────────┘      └──────┬──────┘
                                        │
                                 ┌──────▼──────┐
                                 │   Celery    │
                                 │  Workers    │
                                 └─────────────┘
```

---

## Environment Setup

### 1. Create Production User

```bash
# SSH into your server
ssh root@your-server.com

# Create dedicated user
adduser llmready
usermod -aG sudo llmready
su - llmready
```

### 2. Clone Repository

```bash
cd /home/llmready
git clone https://github.com/yourusername/llmready.git
cd llmready
```

### 3. Install System Dependencies

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Install Nginx
sudo apt install nginx -y

# Install Certbot for SSL
sudo apt install certbot python3-certbot-nginx -y

# Install Node.js
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install nodejs -y

# Install Python
sudo apt install python3.11 python3.11-venv python3-pip -y
```

---

## Database Configuration

### Option 1: Managed PostgreSQL (Recommended)

Use a managed service like:
- **AWS RDS**
- **DigitalOcean Managed Database**
- **Heroku Postgres**
- **Supabase**

Benefits:
- Automatic backups
- High availability
- Managed updates
- Monitoring included

### Option 2: Self-Hosted PostgreSQL

```bash
# Create docker-compose.prod.yml
cat > docker-compose.prod.yml << 'EOF'
version: '3.8'

services:
  postgres:
    image: postgres:15
    container_name: llmready_postgres_prod
    restart: always
    environment:
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: llmready_prod
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backups:/backups
    ports:
      - "127.0.0.1:5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER}"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: llmready_redis_prod
    restart: always
    command: redis-server --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_data:/data
    ports:
      - "127.0.0.1:6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 5

volumes:
  postgres_data:
  redis_data:
EOF

# Start databases
docker-compose -f docker-compose.prod.yml up -d
```

---

## Backend Deployment

### 1. Setup Backend Environment

```bash
cd backend

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install gunicorn
```

### 2. Configure Production Environment

```bash
# Create production .env file
cat > .env << 'EOF'
# Application
ENVIRONMENT=production
DEBUG=false
SECRET_KEY=your-super-secret-key-change-this-in-production
ALLOWED_HOSTS=your-domain.com,www.your-domain.com

# Database
DATABASE_URL=postgresql://user:password@host:5432/llmready_prod

# Redis
REDIS_URL=redis://:password@localhost:6379/0

# JWT
JWT_SECRET_KEY=your-jwt-secret-key-change-this
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Stripe
STRIPE_SECRET_KEY=sk_live_your_stripe_secret_key
STRIPE_PUBLISHABLE_KEY=pk_live_your_stripe_publishable_key
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret
STRIPE_PRICE_FREE=price_free_plan_id
STRIPE_PRICE_STANDARD=price_standard_monthly_id
STRIPE_PRICE_PRO=price_pro_monthly_id

# SendGrid
SENDGRID_API_KEY=SG.your_sendgrid_api_key
SENDGRID_FROM_EMAIL=noreply@your-domain.com
SENDGRID_FROM_NAME=LLMReady

# Frontend URL
FRONTEND_URL=https://your-domain.com

# CORS
CORS_ORIGINS=https://your-domain.com,https://www.your-domain.com

# File Storage
UPLOAD_DIR=/home/llmready/llmready/uploads
MAX_UPLOAD_SIZE=104857600

# Rate Limiting
RATE_LIMIT_PER_MINUTE=60
EOF

# Secure the file
chmod 600 .env
```

### 3. Run Database Migrations

```bash
source venv/bin/activate
alembic upgrade head
```

### 4. Create Systemd Service

```bash
# Create service file
sudo nano /etc/systemd/system/llmready-backend.service
```

Add this content:

```ini
[Unit]
Description=LLMReady Backend API
After=network.target postgresql.service redis.service

[Service]
Type=notify
User=llmready
Group=llmready
WorkingDirectory=/home/llmready/llmready/backend
Environment="PATH=/home/llmready/llmready/backend/venv/bin"
ExecStart=/home/llmready/llmready/backend/venv/bin/gunicorn \
    --bind 127.0.0.1:8000 \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --timeout 120 \
    --access-logfile /var/log/llmready/access.log \
    --error-logfile /var/log/llmready/error.log \
    app.main:app

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# Create log directory
sudo mkdir -p /var/log/llmready
sudo chown llmready:llmready /var/log/llmready

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable llmready-backend
sudo systemctl start llmready-backend
sudo systemctl status llmready-backend
```

---

## Frontend Deployment

### 1. Build Frontend

```bash
cd ../frontend

# Install dependencies
npm install

# Create production .env
cat > .env << 'EOF'
VITE_API_URL=https://api.your-domain.com
VITE_STRIPE_PUBLISHABLE_KEY=pk_live_your_stripe_publishable_key
EOF

# Build for production
npm run build

# The build output is in dist/
```

### 2. Deploy Frontend

**Option A: Nginx (Recommended)**

```bash
# Copy build to nginx directory
sudo mkdir -p /var/www/llmready
sudo cp -r dist/* /var/www/llmready/
sudo chown -R www-data:www-data /var/www/llmready
```

**Option B: Vercel (Easiest)**

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
vercel --prod
```

**Option C: Netlify**

```bash
# Install Netlify CLI
npm i -g netlify-cli

# Deploy
netlify deploy --prod --dir=dist
```

---

## Nginx Configuration

### 1. Create Nginx Config

```bash
sudo nano /etc/nginx/sites-available/llmready
```

Add this configuration:

```nginx
# Redirect HTTP to HTTPS
server {
    listen 80;
    listen [::]:80;
    server_name your-domain.com www.your-domain.com;
    return 301 https://$server_name$request_uri;
}

# Main HTTPS server
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name your-domain.com www.your-domain.com;

    # SSL Configuration (managed by Certbot)
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers off;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' https: data: 'unsafe-inline' 'unsafe-eval';" always;

    # Frontend
    root /var/www/llmready;
    index index.html;

    # Frontend routes
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Backend API
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        proxy_read_timeout 120s;
    }

    # WebSocket support for future features
    location /ws/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }

    # Static files caching
    location ~* \.(jpg|jpeg|png|gif|ico|css|js|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

### 2. Enable Site & Get SSL

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/llmready /etc/nginx/sites-enabled/

# Test configuration
sudo nginx -t

# Get SSL certificate
sudo certbot --nginx -d your-domain.com -d www.your-domain.com

# Restart Nginx
sudo systemctl restart nginx
```

---

## Celery & Redis Setup

### 1. Create Celery Worker Service

```bash
sudo nano /etc/systemd/system/llmready-celery.service
```

```ini
[Unit]
Description=LLMReady Celery Worker
After=network.target redis.service

[Service]
Type=forking
User=llmready
Group=llmready
WorkingDirectory=/home/llmready/llmready/backend
Environment="PATH=/home/llmready/llmready/backend/venv/bin"
ExecStart=/home/llmready/llmready/backend/venv/bin/celery -A app.core.celery_app worker \
    --loglevel=info \
    --concurrency=2 \
    --logfile=/var/log/llmready/celery.log

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 2. Create Celery Beat Service (Scheduled Tasks)

```bash
sudo nano /etc/systemd/system/llmready-celery-beat.service
```

```ini
[Unit]
Description=LLMReady Celery Beat Scheduler
After=network.target redis.service

[Service]
Type=simple
User=llmready
Group=llmready
WorkingDirectory=/home/llmready/llmready/backend
Environment="PATH=/home/llmready/llmready/backend/venv/bin"
ExecStart=/home/llmready/llmready/backend/venv/bin/celery -A app.core.celery_app beat \
    --loglevel=info \
    --logfile=/var/log/llmready/celery-beat.log

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 3. Start Celery Services

```bash
sudo systemctl daemon-reload
sudo systemctl enable llmready-celery llmready-celery-beat
sudo systemctl start llmready-celery llmready-celery-beat
```

---

## Stripe Configuration

### 1. Production API Keys

1. Go to [Stripe Dashboard](https://dashboard.stripe.com)
2. Switch to **Production** mode
3. Get your **Live** API keys
4. Add to backend `.env`:
   ```
   STRIPE_SECRET_KEY=sk_live_...
   STRIPE_PUBLISHABLE_KEY=pk_live_...
   ```

### 2. Configure Webhook

1. Go to **Developers** → **Webhooks**
2. Add endpoint: `https://your-domain.com/api/v1/webhooks/stripe`
3. Select events:
   - `checkout.session.completed`
   - `customer.subscription.created`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`
   - `invoice.payment_succeeded`
   - `invoice.payment_failed`
4. Copy webhook secret to `.env`:
   ```
   STRIPE_WEBHOOK_SECRET=whsec_...
   ```

### 3. Test Webhook

```bash
stripe listen --forward-to localhost:8000/api/v1/webhooks/stripe
```

---

## Email Configuration

### 1. SendGrid Setup

1. Create SendGrid account
2. Verify domain
3. Create API key with full permissions
4. Add to `.env`:
   ```
   SENDGRID_API_KEY=SG.your_key
   SENDGRID_FROM_EMAIL=noreply@your-domain.com
   ```

### 2. Create Email Templates

In SendGrid dashboard:
- Welcome email
- Password reset
- Email verification
- Generation complete notification

---

## Security Checklist

### Application Security

- [ ] Change all default secrets
- [ ] Use strong SECRET_KEY (64+ chars)
- [ ] Enable HTTPS only
- [ ] Configure CORS properly
- [ ] Set secure cookie flags
- [ ] Enable rate limiting
- [ ] Validate all inputs
- [ ] Sanitize file uploads

### Server Security

```bash
# Configure firewall
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable

# Disable root SSH
sudo nano /etc/ssh/sshd_config
# Set: PermitRootLogin no
sudo systemctl restart sshd

# Install fail2ban
sudo apt install fail2ban -y
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

### Database Security

- [ ] Use strong database password
- [ ] Enable SSL for database connections
- [ ] Restrict database access to localhost
- [ ] Regular backups
- [ ] Enable audit logging

---

## Monitoring & Logging

### 1. Setup Log Rotation

```bash
sudo nano /etc/logrotate.d/llmready
```

```
/var/log/llmready/*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 llmready llmready
    sharedscripts
    postrotate
        systemctl reload llmready-backend
    endscript
}
```

### 2. Monitor Services

```bash
# Check service status
sudo systemctl status llmready-backend
sudo systemctl status llmready-celery
sudo systemctl status nginx

# View logs
sudo journalctl -u llmready-backend -f
tail -f /var/log/llmready/access.log
tail -f /var/log/llmready/error.log
```

### 3. Setup Monitoring Tools (Optional)

**Option A: UptimeRobot**
- Free uptime monitoring
- Email alerts

**Option B: Sentry**
- Error tracking
- Performance monitoring

**Option C: New Relic**
- Full application monitoring

---

## Backup & Recovery

### 1. Database Backup Script

```bash
cat > ~/backup-db.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/home/llmready/backups"
DATE=$(date +%Y%m%d_%H%M%S)
DB_NAME="llmready_prod"

mkdir -p $BACKUP_DIR

# Backup database
docker exec llmready_postgres_prod pg_dump -U postgres $DB_NAME | gzip > "$BACKUP_DIR/db_$DATE.sql.gz"

# Keep only last 7 days
find $BACKUP_DIR -name "db_*.sql.gz" -mtime +7 -delete

echo "Backup completed: db_$DATE.sql.gz"
EOF

chmod +x ~/backup-db.sh

# Add to crontab (daily at 2 AM)
crontab -e
# Add: 0 2 * * * /home/llmready/backup-db.sh
```

### 2. Restore Database

```bash
# Restore from backup
gunzip < backups/db_YYYYMMDD_HHMMSS.sql.gz | \
    docker exec -i llmready_postgres_prod psql -U postgres llmready_prod
```

---

## Troubleshooting

### Backend Issues

```bash
# Check backend logs
sudo journalctl -u llmready-backend -n 100

# Check if port is listening
sudo netstat -tulpn | grep 8000

# Test API directly
curl http://localhost:8000/health
```

### Celery Issues

```bash
# Check celery logs
tail -f /var/log/llmready/celery.log

# Check Redis connection
redis-cli ping

# Restart celery
sudo systemctl restart llmready-celery
```

### Database Issues

```bash
# Check database logs
docker logs llmready_postgres_prod

# Connect to database
docker exec -it llmready_postgres_prod psql -U postgres llmready_prod

# Check connections
docker exec llmready_postgres_prod psql -U postgres -c "SELECT * FROM pg_stat_activity;"
```

### Nginx Issues

```bash
# Check nginx logs
sudo tail -f /var/log/nginx/error.log

# Test configuration
sudo nginx -t

# Restart nginx
sudo systemctl restart nginx
```

---

## Performance Optimization

### 1. Enable Caching

```bash
# Install Redis for caching
# Already configured in docker-compose.prod.yml
```

### 2. Database Optimization

```sql
-- Add indexes
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_generations_user_id ON generations(user_id);
CREATE INDEX idx_generations_status ON generations(status);
CREATE INDEX idx_websites_user_id ON websites(user_id);

-- Analyze tables
ANALYZE users;
ANALYZE websites;
ANALYZE generations;
```

### 3. Frontend Optimization

```bash
# Enable gzip in Nginx (already in config above)
# Enable browser caching (already in config above)
# Use CDN for static assets (optional)
```

---

## Post-Deployment Checklist

- [ ] All services running
- [ ] SSL certificate installed
- [ ] Database migrated
- [ ] Stripe webhooks working
- [ ] Email sending working
- [ ] Domain DNS configured
- [ ] Backups automated
- [ ] Monitoring configured
- [ ] Error tracking setup
- [ ] Documentation updated
- [ ] Team notified
- [ ] Test user registration
- [ ] Test payment flow
- [ ] Test generation flow

---

## Scaling Considerations

### Horizontal Scaling

1. **Load Balancer**: Add nginx load balancer
2. **Multiple Backend Workers**: Run multiple gunicorn instances
3. **Separate Celery Workers**: Dedicated servers for tasks
4. **Database Replication**: Read replicas for queries

### Vertical Scaling

1. Upgrade server resources (CPU, RAM)
2. Optimize database queries
3. Add caching layers
4. Use CDN for static files

---

## Support & Maintenance

### Regular Tasks

**Daily:**
- Check error logs
- Monitor disk space
- Review failed jobs

**Weekly:**
- Review user activity
- Check backup integrity
- Update dependencies

**Monthly:**
- Security updates
- Performance review
- Cost optimization

---

## Quick Commands Reference

```bash
# Start all services
sudo systemctl start llmready-backend llmready-celery llmready-celery-beat nginx

# Stop all services
sudo systemctl stop llmready-backend llmready-celery llmready-celery-beat

# Restart services
sudo systemctl restart llmready-backend

# View logs
sudo journalctl -u llmready-backend -f
tail -f /var/log/llmready/error.log

# Database backup
~/backup-db.sh

# Update application
cd /home/llmready/llmready
git pull
cd backend && source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
sudo systemctl restart llmready-backend
```

---

## 🎉 Deployment Complete!

Your LLMReady application is now running in production! 

**Access your application:**
- Website: https://your-domain.com
- API: https://your-domain.com/api/docs

**Next steps:**
1. Create your first admin user
2. Test the complete user flow
3. Monitor logs for any issues
4. Set up regular backups
5. Configure monitoring alerts

---

**Need help?** Review the troubleshooting section or check the application logs.

**Production URL:** https://your-domain.com  
**API Documentation:** https://your-domain.com/api/docs  
**Status Page:** https://your-domain.com/health
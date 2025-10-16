# Production Server Monitoring Commands

Quick reference for checking if everything is running correctly.

## 🚀 Quick Status Check (All Services)

```bash
# Check ALL LLMReady services at once
sudo systemctl status llmready-backend llmready-celery-worker llmready-celery-beat nginx
```

## 📊 Individual Service Status

### Backend API
```bash
# Check status
sudo systemctl status llmready-backend

# Is it running?
sudo systemctl is-active llmready-backend

# View last 20 lines of logs
sudo journalctl -u llmready-backend -n 20

# Follow logs in real-time
sudo journalctl -u llmready-backend -f

# Check for errors in last 100 lines
sudo journalctl -u llmready-backend -n 100 | grep -i error
```

### Celery Worker
```bash
# Check status
sudo systemctl status llmready-celery-worker

# Follow logs
sudo journalctl -u llmready-celery-worker -f

# Check if it's processing tasks
sudo journalctl -u llmready-celery-worker -n 50 | grep -i "task"
```

### Celery Beat (Scheduler)
```bash
# Check status
sudo systemctl status llmready-celery-beat

# Follow logs
sudo journalctl -u llmready-celery-beat -f

# Check scheduled tasks
sudo journalctl -u llmready-celery-beat -n 50 | grep -i "schedule"
```

### Nginx (Web Server)
```bash
# Check status
sudo systemctl status nginx

# Test configuration
sudo nginx -t

# View error logs
sudo tail -f /var/log/nginx/error.log

# View access logs
sudo tail -f /var/log/nginx/access.log
```

## 🐳 Docker Containers

### Check Running Containers
```bash
# List all running containers
docker ps

# Check specific services
docker ps --filter "name=postgres"
docker ps --filter "name=redis"
```

### PostgreSQL
```bash
# Check if running
docker ps | grep postgres

# Check connection
docker exec $(docker ps -qf "name=postgres") pg_isready -U postgres

# View logs
docker logs $(docker ps -qf "name=postgres") --tail 50
```

### Redis
```bash
# Check if running
docker ps | grep redis

# Test connection
docker exec $(docker ps -qf "name=redis") redis-cli ping

# View logs
docker logs $(docker ps -qf "name=redis") --tail 50
```

## 🔍 Backend API Health

### Test Endpoints
```bash
# Health check
curl http://localhost:8000/health | jq

# Root endpoint
curl http://localhost:8000/ | jq

# Check if API is responding
curl -I http://localhost:8000/health
```

### Test with External Access
```bash
# If you have a domain
curl https://your-domain.com/health | jq

# Check SSL certificate
curl -vI https://your-domain.com 2>&1 | grep -i "SSL"
```

## 📈 Resource Usage

### CPU & Memory
```bash
# Overall system resources
htop
# or
top

# Check specific process
ps aux | grep uvicorn
ps aux | grep celery

# Memory usage by service
systemctl status llmready-backend | grep Memory
systemctl status llmready-celery-worker | grep Memory
```

### Disk Space
```bash
# Check disk usage
df -h

# Check specific directories
du -sh /opt/llmready/*
du -sh /var/log/llmready/*
du -sh /var/www/llmready/*
```

### Network Connections
```bash
# Check open ports
sudo ss -tulpn | grep LISTEN

# Check specific ports
sudo ss -tulpn | grep :8000  # Backend
sudo ss -tulpn | grep :80    # HTTP
sudo ss -tulpn | grep :443   # HTTPS
sudo ss -tulpn | grep :5432  # PostgreSQL
sudo ss -tulpn | grep :6379  # Redis
```

## 🔐 Database

### PostgreSQL Status
```bash
# Check database connection
cd /opt/llmready/backend
source ../venv/bin/activate
python -c "from app.core.database import engine; from sqlalchemy import text; conn = engine.connect(); print('✅ Database connected!'); conn.execute(text('SELECT 1')); conn.close()"
```

### Check Migrations
```bash
cd /opt/llmready/backend
source ../venv/bin/activate

# Current migration version
alembic current

# Check if migrations needed
alembic check

# See migration history
alembic history
```

## 📧 Test Email & Tasks

### Send Test Email (via Celery)
```bash
cd /opt/llmready/backend
source ../venv/bin/activate

# Check if Celery can connect to Redis
python -c "from app.core.celery_app import celery_app; print('✅ Celery OK' if celery_app.control.inspect().active() else '❌ Celery NOT OK')"
```

### Check Recent Celery Tasks
```bash
# Check worker logs for task processing
sudo journalctl -u llmready-celery-worker -n 100 | grep -E "Task|Received|succeeded|failed"
```

## 🎯 Monitoring (Sentry)

### Check Sentry Configuration
```bash
# Check DSN is set
grep SENTRY_DSN /opt/llmready/backend/.env

# Check if Sentry is initialized
sudo journalctl -u llmready-backend -n 200 | grep -i "sentry initialized"

# Check for Sentry activity
sudo journalctl -u llmready-backend -n 100 | grep "\[sentry\]"
```

### Test Sentry Error Tracking
```bash
# Trigger test error
curl http://localhost:8000/test-sentry

# Check logs to confirm it was sent
sudo journalctl -u llmready-backend -n 20 | grep -i "sentry\|error"
```

## 🚨 Troubleshooting

### Service Won't Start
```bash
# Check why service failed
sudo systemctl status llmready-backend
sudo journalctl -xe

# Check configuration
cd /opt/llmready/backend
cat .env | grep -v "SECRET\|PASSWORD"
```

### High CPU/Memory Usage
```bash
# Find which process is consuming resources
ps aux --sort=-%cpu | head -10
ps aux --sort=-%mem | head -10

# Check specific service
systemctl status llmready-backend
systemctl status llmready-celery-worker
```

### Database Connection Issues
```bash
# Check if PostgreSQL is running
docker ps | grep postgres

# Check database logs
docker logs $(docker ps -qf "name=postgres") --tail 100

# Test connection from backend
cd /opt/llmready/backend
source ../venv/bin/activate
python -c "import psycopg2; from app.core.config import settings; conn = psycopg2.connect(settings.DATABASE_URL); print('✅ Connected'); conn.close()"
```

### Check All Log Files
```bash
# System logs
sudo journalctl -n 100

# Backend logs
sudo journalctl -u llmready-backend -n 50

# Celery logs
sudo journalctl -u llmready-celery-worker -n 50
sudo journalctl -u llmready-celery-beat -n 50

# Nginx logs
sudo tail -50 /var/log/nginx/error.log
sudo tail -50 /var/log/nginx/access.log
```

## 🔄 Restart Services

### Restart Individual Services
```bash
# Backend
sudo systemctl restart llmready-backend

# Celery worker
sudo systemctl restart llmready-celery-worker

# Celery beat
sudo systemctl restart llmready-celery-beat

# Nginx
sudo systemctl restart nginx

# PostgreSQL & Redis (Docker)
docker compose -f /opt/llmready/docker-compose.yml restart
```

### Restart Everything
```bash
# Restart all LLMReady services
sudo systemctl restart llmready-backend llmready-celery-worker llmready-celery-beat nginx

# Restart Docker services
cd /opt/llmready
docker compose restart
```

## 📊 One-Line Health Check

```bash
# Check if everything is running
echo "Backend: $(systemctl is-active llmready-backend) | Celery Worker: $(systemctl is-active llmready-celery-worker) | Celery Beat: $(systemctl is-active llmready-celery-beat) | Nginx: $(systemctl is-active nginx) | Postgres: $(docker ps | grep -q postgres && echo 'running' || echo 'stopped') | Redis: $(docker ps | grep -q redis && echo 'running' || echo 'stopped')"
```

## 🔔 Set Up Monitoring Dashboard (Optional)

### Create an alias for quick checks
```bash
# Add to ~/.bashrc
alias llm-status='sudo systemctl status llmready-backend llmready-celery-worker llmready-celery-beat nginx && docker ps'
alias llm-logs='sudo journalctl -u llmready-backend -f'
alias llm-restart='sudo systemctl restart llmready-backend llmready-celery-worker llmready-celery-beat'

# Then reload
source ~/.bashrc

# Use them
llm-status
llm-logs
llm-restart
```

---

## 📝 Daily Monitoring Routine

### Morning Check (1 minute)
```bash
# 1. Check all services are running
sudo systemctl status llmready-backend llmready-celery-worker llmready-celery-beat nginx

# 2. Check for errors in last 24 hours
sudo journalctl -u llmready-backend --since "24 hours ago" | grep -i error | wc -l

# 3. Check disk space
df -h | grep -E "Filesystem|/$"

# 4. Quick API test
curl -s http://localhost:8000/health | jq .status
```

### Weekly Review (5 minutes)
```bash
# 1. Check logs for patterns
sudo journalctl -u llmready-backend --since "7 days ago" | grep -i error | tail -20

# 2. Review Sentry dashboard
# Visit: https://sentry.io

# 3. Check resource usage trends
htop

# 4. Review Celery task success rate
sudo journalctl -u llmready-celery-worker --since "7 days ago" | grep -c "succeeded"
sudo journalctl -u llmready-celery-worker --since "7 days ago" | grep -c "failed"
```

---

**💡 Tip**: Save this file and keep it handy! Most issues can be diagnosed with these commands.
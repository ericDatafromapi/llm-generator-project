# 🚀 Week 6 Quick Start Guide

**File Generation is Ready!** Let's get it running.

---

## Prerequisites

✅ Weeks 1-5 completed  
✅ FastAPI running on port 8000  
✅ PostgreSQL & Redis running via Docker  
✅ Docker Desktop installed and running

---

## 🎯 Step-by-Step Setup (5 minutes)

### Step 1: Create File Storage Directory

```bash
# Create the directory where generated files will be stored
sudo mkdir -p /var/llmready/files
sudo chown $USER /var/llmready/files

# Verify
ls -ld /var/llmready/files
```

### Step 2: Update .env File

Add these lines to `backend/.env`:

```bash
# Celery Configuration (add if not present)
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Generation Settings (add if not present)
GENERATION_TIMEOUT=3600
GENERATION_MAX_RETRIES=2

# File Storage (update if different)
FILE_STORAGE_PATH=/var/llmready/files
```

### Step 3: Start Celery Worker

**Terminal 1** (keep this running):
```bash
cd backend
source venv/bin/activate
celery -A app.core.celery_app worker --loglevel=info
```

You should see:
```
celery@YourMacBook v5.3.4 (opalescent)
...
[tasks]
  . app.tasks.generation.generate_llm_content
  . app.tasks.scheduled.cleanup_old_generations
  . app.tasks.scheduled.reset_monthly_quotas

celery@YourMacBook ready.
```

### Step 4: Start Celery Beat (Optional)

**Terminal 2** (for scheduled tasks):
```bash
cd backend
source venv/bin/activate
celery -A app.core.celery_app beat --loglevel=info
```

### Step 5: Restart FastAPI

**Terminal 3**:
```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload
```

---

## 🧪 Test the Generation Flow

### Test 1: Create a Test Website

```bash
# First, login and get your token
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "your@email.com",
    "password": "your_password"
  }'

# Save the access_token from response
TOKEN="paste_your_token_here"

# Create a test website (you'll need to implement website endpoints first)
# For now, you can add one directly via database or use an existing website_id
```

### Test 2: Check Your Quota

```bash
curl -X GET "http://localhost:8000/api/v1/generations/quota/check" \
  -H "Authorization: Bearer $TOKEN"
```

Expected response:
```json
{
  "can_generate": true,
  "generations_used": 0,
  "generations_limit": 1,
  "remaining_generations": 1,
  "message": "You have 1 generation remaining this month."
}
```

### Test 3: Start a Generation

```bash
# Replace with your actual website_id
WEBSITE_ID="your-website-uuid"

curl -X POST "http://localhost:8000/api/v1/generations/start" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"website_id\": \"$WEBSITE_ID\"
  }"
```

Expected response:
```json
{
  "generation_id": "newly-created-uuid",
  "status": "pending",
  "message": "Generation started successfully. You will receive an email when it completes."
}
```

### Test 4: Watch It Process

In your Celery worker terminal, you should see:
```
[2025-10-13 17:00:00,000: INFO/MainProcess] Task app.tasks.generation.generate_llm_content[uuid] received
[2025-10-13 17:00:00,500: INFO/ForkPoolWorker-1] Starting generation uuid for website https://example.com
[2025-10-13 17:00:01,000: INFO/ForkPoolWorker-1] Running Docker command: docker run --rm -v ...
[2025-10-13 17:00:05,000: INFO/ForkPoolWorker-1] Mdream: Crawling https://example.com
[2025-10-13 17:00:10,000: INFO/ForkPoolWorker-1] Mdream: Found 25 pages
...
[2025-10-13 17:01:00,000: INFO/ForkPoolWorker-1] Generation uuid completed successfully
```

### Test 5: Check Status

```bash
GENERATION_ID="uuid-from-previous-response"

curl -X GET "http://localhost:8000/api/v1/generations/$GENERATION_ID" \
  -H "Authorization: Bearer $TOKEN"
```

### Test 6: Download the File

Once status is "completed":
```bash
curl -X GET "http://localhost:8000/api/v1/generations/$GENERATION_ID/download" \
  -H "Authorization: Bearer $TOKEN" \
  --output "my_generation.zip"

# Verify download
ls -lh my_generation.zip
unzip -l my_generation.zip
```

---

## 🎨 What's in the Generated ZIP?

```
my_generation.zip
├── llms.txt           # Summary file for LLMs
├── llms-full.txt      # Full content file
├── manifest.json      # Generation metadata
└── md/                # Individual markdown files
    ├── page1.md
    ├── page2.md
    └── ...
```

---

## 🐛 Common Issues & Fixes

### Issue: "Celery worker not starting"

**Check Redis:**
```bash
redis-cli ping
# Should return: PONG

# If not, start Docker
docker compose up -d
```

### Issue: "Docker not found"

**Install Docker:**
```bash
brew install --cask docker
open -a Docker
# Wait for Docker to start
```

### Issue: "Generation fails immediately"

**Check Celery logs:**
The worker terminal will show the error. Common causes:
- Website URL is invalid
- Docker not running
- File permissions on /var/llmready/files

**Fix permissions:**
```bash
sudo chown -R $USER /var/llmready/files
chmod 755 /var/llmready/files
```

### Issue: "File not found after generation"

**Check the file was created:**
```bash
ls -la /var/llmready/files/
```

**Check database:**
Query the Generation record to see the `file_path` and any error messages.

### Issue: "Email not sending"

**This is normal if SendGrid isn't configured.** Check logs:
```
SendGrid not configured. Would send email to user@email.com
```

To enable emails, add to `.env`:
```bash
SENDGRID_API_KEY=your_actual_key
FROM_EMAIL=noreply@yourdomain.com
```

---

## 📊 Monitoring Your System

### Check Celery Status

```bash
# See active tasks
celery -A app.core.celery_app inspect active

# See registered tasks
celery -A app.core.celery_app inspect registered

# See stats
celery -A app.core.celery_app inspect stats
```

### Check Redis

```bash
# Connect to Redis
redis-cli

# Check queued jobs
LLEN celery

# Monitor in real-time
MONITOR
```

### Check File Storage

```bash
# See generated files
ls -lah /var/llmready/files/

# Check disk usage
du -sh /var/llmready/files/
```

---

## 🎯 What's Next?

Now that generation is working, you can:

1. **Test with real websites** - Try different sites
2. **Monitor performance** - Track generation times
3. **Check email notifications** - Configure SendGrid
4. **Implement Week 7** - Website management endpoints

---

## 🚦 Daily Workflow

Every time you work on the project:

```bash
# Terminal 1: Start services
docker compose up -d

# Terminal 2: Start FastAPI
cd backend && source venv/bin/activate
uvicorn app.main:app --reload

# Terminal 3: Start Celery Worker
cd backend && source venv/bin/activate
celery -A app.core.celery_app worker -l info

# Terminal 4: (Optional) Start Celery Beat
cd backend && source venv/bin/activate
celery -A app.core.celery_app beat -l info
```

**Access Points:**
- API Docs: http://localhost:8000/api/docs
- Health Check: http://localhost:8000/health

---

## 📞 Need Help?

1. Check [`WEEK_6_GENERATION_COMPLETE.md`](WEEK_6_GENERATION_COMPLETE.md:1) for detailed docs
2. Look at Celery worker logs for errors
3. Check FastAPI logs for API issues
4. Verify Docker is running: `docker ps`

**You're all set for Week 6!** 🎉
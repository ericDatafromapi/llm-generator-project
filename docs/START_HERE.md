# 🚀 How to Start Your LLMReady Backend

## ✅ Everything is Set Up!

You've successfully completed Week 1. Here's how to work with your backend:

---

## 🎯 Quick Start (Every Time You Work)

### Option 1: Single Terminal (Recommended)

```bash
# 1. Start Docker in background
docker compose up -d

# 2. Navigate to backend and start FastAPI
cd backend
source venv/bin/activate
uvicorn app.main:app --reload

# Server will run on http://localhost:8000
# Press Ctrl+C to stop when done
```

### Option 2: Two Terminals

**Terminal 1: Docker (foreground)**
```bash
docker compose up
# Shows live logs from PostgreSQL and Redis
```

**Terminal 2: FastAPI**
```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload
```

---

## 🌐 Access Your Backend

Once FastAPI is running, open these URLs:

### 1. API Documentation (Swagger UI) ⭐
**http://localhost:8000/api/docs**

This is your interactive API documentation where you can:
- See all available endpoints
- Test endpoints directly
- View request/response schemas
- Explore the API structure

### 2. Alternative Documentation (ReDoc)
**http://localhost:8000/api/redoc**

Beautiful, clean API documentation.

### 3. Health Check
**http://localhost:8000/health**

Returns:
```json
{
  "status": "healthy",
  "database": "connected",
  "service": "LLMReady"
}
```

### 4. Root Endpoint
**http://localhost:8000/**

Returns:
```json
{
  "message": "LLMReady API",
  "version": "1.0.0",
  "status": "operational",
  "docs": "/api/docs"
}
```

---

## 🔍 What to Expect

### Current State (Week 1)
Right now, your API has:
- ✅ Root endpoint (/)
- ✅ Health check (/health)
- ✅ Auto-generated documentation (/api/docs)
- ✅ Database with 6 empty tables
- ✅ Full infrastructure ready

### Coming in Week 2-3
You'll add:
- 🔐 User registration
- 🔑 Login/logout
- 🎫 JWT tokens
- 📧 Email verification
- 🔒 Password reset
- And more!

---

## 🛑 Stopping Everything

```bash
# Stop FastAPI
# Press Ctrl+C in the terminal running uvicorn

# Stop Docker
docker compose down

# Or stop but keep data
docker compose stop
```

---

## 📊 Verify Everything Works

Run these commands in a new terminal:

```bash
# 1. Check Docker containers
docker ps
# Should show: llmready_postgres and llmready_redis

# 2. Test API
curl http://localhost:8000/health
# Should return: {"status":"healthy"...}

# 3. Check database tables
docker exec llmready_postgres psql -U postgres -d llmready_dev -c "\dt"
# Should show 7 tables

# 4. Check Redis
docker exec llmready_redis redis-cli ping
# Should return: PONG
```

---

## 🎨 Visual Tour

### API Documentation (Swagger)
Go to **http://localhost:8000/api/docs** and you'll see:

```
LLMReady - Version 1.0.0
Professional AI Content Optimization Platform

📁 Root
  GET / - Root endpoint

📁 Health  
  GET /health - Health check endpoint
```

Currently minimal, but in Week 2 you'll see:

```
📁 Auth
  POST /api/v1/auth/register
  POST /api/v1/auth/login
  POST /api/v1/auth/refresh
  GET  /api/v1/auth/me
  ...and more!
```

---

## 💡 Pro Tips

1. **Keep FastAPI running** while developing - it auto-reloads on code changes!
2. **Use `docker compose up -d`** (background) to avoid log clutter
3. **Bookmark http://localhost:8000/api/docs** - you'll use it constantly
4. **Check logs** if something breaks: `docker compose logs -f postgres`

---

## 🐛 Troubleshooting

**"Port 8000 already in use"**
```bash
lsof -ti:8000 | xargs kill -9
```

**"Connection refused" when testing**
```bash
# Make sure FastAPI is running
ps aux | grep uvicorn
# Should show a running process
```

**Database errors**
```bash
# Restart PostgreSQL
docker compose restart postgres
```

---

## 🎯 Your Backend at a Glance

**What's Running:**
- 🐘 PostgreSQL on port 5432
- 🔴 Redis on port 6379
- ⚡ FastAPI on port 8000

**What's Ready:**
- 6 database models
- Alembic migrations
- Environment config
- Health monitoring
- API documentation

**What's Next:**
- Week 2: Authentication
- Week 3: Email & Password Reset
- Week 4-5: Stripe Integration

---

## 📞 Need Help?

Check these docs:
- [`QUICK_REFERENCE.md`](QUICK_REFERENCE.md:1) - Common commands
- [`backend/README.md`](backend/README.md:1) - Detailed documentation
- [`WEEK_1_SUMMARY.md`](WEEK_1_SUMMARY.md:1) - What we built

---

**You're all set! Your backend is running and ready for development!** 🎉

Open http://localhost:8000/api/docs to explore your API! 🚀
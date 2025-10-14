# 🚀 LLMReady Backend - Quick Reference

## 🎯 Week 1 Status: ✅ COMPLETE

**Backend running at:** http://localhost:8000  
**API Docs:** http://localhost:8000/api/docs  
**Database:** PostgreSQL 15 with 6 tables  
**Services:** Docker Compose (PostgreSQL + Redis)

---

## 📊 Database Tables

| Table | Purpose | Rows |
|-------|---------|------|
| `users` | User accounts & auth | 0 |
| `subscriptions` | Plans & quotas | 0 |
| `websites` | Website configs | 0 |
| `generations` | Generation tasks | 0 |
| `password_reset_tokens` | Password resets | 0 |
| `email_verification_tokens` | Email verification | 0 |
| `alembic_version` | Migration tracking | 1 |

---

## 🔧 Common Commands

### Start Services
```bash
# Start Docker containers
docker compose up -d

# Start FastAPI server
cd backend
source venv/bin/activate
uvicorn app.main:app --reload
```

### Stop Services
```bash
# Stop FastAPI: Ctrl+C in terminal

# Stop Docker
docker compose down
```

### Database Access
```bash
# Connect to database
docker exec -it llmready_postgres psql -U postgres -d llmready_dev

# List tables
docker exec llmready_postgres psql -U postgres -d llmready_dev -c "\dt"

# View table structure
docker exec llmready_postgres psql -U postgres -d llmready_dev -c "\d users"
```

### Migrations
```bash
cd backend
source venv/bin/activate

# Create new migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback one version
alembic downgrade -1

# Show current version
alembic current
```

---

## 🧪 Testing Endpoints

```bash
# Health check
curl http://localhost:8000/health

# Root endpoint
curl http://localhost:8000/

# API documentation
open http://localhost:8000/api/docs
```

---

## 📁 Project Structure

```
backend/
├── app/
│   ├── main.py              # FastAPI app
│   ├── core/
│   │   ├── config.py       # Settings
│   │   └── database.py     # DB connection
│   ├── models/             # 6 SQLAlchemy models
│   ├── api/v1/             # API routes (Week 2+)
│   ├── schemas/            # Pydantic schemas (Week 2+)
│   └── services/           # Business logic (Week 2+)
├── alembic/                # Migrations
├── tests/                  # Tests (Week 10)
├── venv/                   # Virtual environment
└── .env                    # Configuration
```

---

## ⚡ Quick Verification

Run this to verify everything:

```bash
# Check all services
docker ps | grep llmready
curl http://localhost:8000/health
docker exec llmready_postgres psql -U postgres -d llmready_dev -c "SELECT COUNT(*) FROM pg_tables WHERE schemaname='public';"
```

Expected: 2 containers, healthy response, 7 tables

---

## 🐛 Troubleshooting

**Port 8000 already in use:**
```bash
lsof -ti:8000 | xargs kill -9
```

**Database connection error:**
```bash
docker compose restart postgres
```

**Alembic errors:**
```bash
# Check current version
alembic current

# Force to head
alembic upgrade head
```

---

## 📝 Environment Files

- `backend/.env` - Your local configuration
- `backend/.env.example` - Template for new environments

**Never commit `.env` to git!**

---

## ⏭️ Next: Week 2-3 (Authentication)

When ready to continue:
- JWT authentication endpoints
- User registration
- Email verification
- Password reset
- Rate limiting

---

## 🎯 Week 1 Achievements

- [x] Monorepo structure
- [x] 6 production-ready models
- [x] FastAPI running
- [x] PostgreSQL + Redis
- [x] Alembic migrations
- [x] Health checks
- [x] Complete documentation

**You're ready for Week 2!** 🚀
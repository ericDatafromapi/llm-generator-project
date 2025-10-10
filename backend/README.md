# 🚀 LLMReady Backend - Week 1 Foundation

Production-ready FastAPI backend with PostgreSQL, Redis, and comprehensive database models.

## 📁 Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application entry point
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py          # Application settings
│   │   └── database.py        # Database configuration
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py            # User model
│   │   ├── subscription.py    # Subscription model
│   │   ├── website.py         # Website model
│   │   ├── generation.py      # Generation model
│   │   ├── password_reset_token.py
│   │   └── email_verification_token.py
│   ├── schemas/               # Pydantic schemas (Week 2)
│   ├── api/                   # API routes (Week 2-7)
│   ├── services/              # Business logic (Week 2+)
│   └── utils/                 # Utilities (Week 2+)
├── tests/                     # Tests (Week 10)
├── .env.example              # Environment variables template
├── requirements.txt          # Python dependencies
└── README.md                 # This file
```

## 🗄️ Database Models

### User Model
- Email/password authentication
- Role-based access control
- Email verification status
- Timestamps and last login tracking

### Subscription Model
- Stripe integration ready
- Plan types: free, standard, pro
- Usage tracking (generations_used/limit)
- Website limits per plan
- Billing cycle management

### Website Model
- URL and configuration storage
- Crawling patterns (include/exclude)
- Generation limits and settings
- Activity tracking

### Generation Model
- Status tracking (pending, processing, completed, failed)
- Progress monitoring
- File metadata
- Error handling with retry logic
- Celery task ID for async processing

### PasswordResetToken Model
- 24-hour expiration
- Single-use tokens
- Secure password reset flow

### EmailVerificationToken Model
- 48-hour expiration
- Single-use tokens
- Email verification flow

## 🔧 Setup Instructions

### Prerequisites
- Python 3.8+
- Docker Desktop
- PostgreSQL 15 (optional, we use Docker)

### Installation

1. **Create virtual environment**:
```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

3. **Configure environment**:
```bash
cp .env.example .env
# Edit .env with your settings (use defaults for local development)
```

4. **Start Docker services** (PostgreSQL + Redis):
```bash
cd ..  # Go back to project root
docker compose up -d
```

5. **Initialize Alembic**:
```bash
cd backend
alembic init alembic
```

6. **Configure Alembic** (edit `alembic.ini`):
```ini
sqlalchemy.url = postgresql://postgres:postgres@localhost:5432/llmready_dev
```

7. **Update `alembic/env.py`**:
```python
from app.core.database import Base
from app.models import *  # Import all models
target_metadata = Base.metadata
```

8. **Create initial migration**:
```bash
alembic revision --autogenerate -m "Initial schema"
```

9. **Apply migration**:
```bash
alembic upgrade head
```

10. **Run the application**:
```bash
uvicorn app.main:app --reload
```

## 🧪 Testing

### Health Check
```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "database": "connected",
  "service": "LLMReady"
}
```

### API Documentation
- Swagger UI: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc

## 📝 Environment Variables

See `.env.example` for all available configuration options.

Key variables:
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `SECRET_KEY`: JWT secret (change in production!)
- `DEBUG`: Enable debug mode (True for development)

## 🐳 Docker Services

### Start services
```bash
docker compose up -d
```

### Stop services
```bash
docker compose down
```

### View logs
```bash
docker compose logs -f postgres
docker compose logs -f redis
```

### Access PostgreSQL
```bash
docker exec -it llmready_postgres psql -U postgres -d llmready_dev
```

## 🗺️ Next Steps (Week 2-3)

- [ ] Implement authentication endpoints
- [ ] Add JWT token handling
- [ ] Create user registration flow
- [ ] Add password reset functionality
- [ ] Implement email verification
- [ ] Add rate limiting middleware

## 🔗 Related Documentation

- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [SQLAlchemy Docs](https://docs.sqlalchemy.org/)
- [Alembic Docs](https://alembic.sqlalchemy.org/)
- [Pydantic Docs](https://docs.pydantic.dev/)

## 📊 Database Schema

```sql
-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    role VARCHAR(50) DEFAULT 'user',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    last_login_at TIMESTAMP
);

-- Subscriptions table
CREATE TABLE subscriptions (
    id UUID PRIMARY KEY,
    user_id UUID UNIQUE REFERENCES users(id),
    plan_type VARCHAR(50) DEFAULT 'free',
    stripe_customer_id VARCHAR(255) UNIQUE,
    stripe_subscription_id VARCHAR(255) UNIQUE,
    status VARCHAR(50) DEFAULT 'active',
    generations_used INTEGER DEFAULT 0,
    generations_limit INTEGER DEFAULT 1,
    websites_count INTEGER DEFAULT 0,
    websites_limit INTEGER DEFAULT 1,
    -- ... more fields
);

-- And 4 more tables: websites, generations, password_reset_tokens, email_verification_tokens
```

## 🎯 Week 1 Deliverables

✅ FastAPI application structure  
✅ 6 production-ready database models  
✅ Docker Compose configuration  
✅ Environment configuration  
✅ Database connection setup  
✅ Health check endpoint  
✅ Alembic migration support  

**Status**: Foundation complete! Ready for Week 2 (Authentication) 🚀
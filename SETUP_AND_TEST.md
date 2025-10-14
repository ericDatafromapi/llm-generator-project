# 🚀 Quick Setup and Test Guide

## Step 1: Install Dependencies

```bash
cd backend

# Make sure you're in your virtual environment
source .venv/bin/activate  # or `source venv/bin/activate`

# Install all dependencies
pip install -r requirements.txt
```

This will install:
- SQLAlchemy (database)
- Stripe SDK
- SendGrid (email)
- Celery (background tasks)
- All other required packages

## Step 2: Apply Database Migration

```bash
# Still in backend directory
alembic upgrade head
```

This creates the `stripe_events` table.

## Step 3: Verify Installation

```bash
python run_tests.py
```

Should show all tests passing!

## Step 4: Start Services

### Terminal 1: Backend API
```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload
```

### Terminal 2: Celery Worker
```bash
cd backend
source .venv/bin/activate
celery -A app.core.celery_app worker --loglevel=info
```

### Terminal 3: Celery Beat (for hourly sync)
```bash
cd backend
source .venv/bin/activate
celery -A app.core.celery_app beat --loglevel=info
```

## Step 5: Test with Stripe CLI

```bash
# In another terminal
stripe listen --forward-to localhost:8000/api/v1/webhooks/stripe

# In yet another terminal
stripe trigger invoice.payment_succeeded
stripe trigger invoice.payment_failed
stripe trigger charge.dispute.created
```

## Step 6: Verify Results

```bash
# Connect to your database
psql postgresql://postgres:postgres@localhost:5432/llmready_dev

# Check processed events
SELECT id, type, status, processed_at 
FROM stripe_events 
ORDER BY processed_at DESC 
LIMIT 10;
```

---

## 🐛 Troubleshooting

### Issue: "No module named 'X'"
**Solution**: Make sure you ran `pip install -r requirements.txt`

### Issue: "Database connection failed"
**Solution**: Make sure PostgreSQL is running:
```bash
# macOS
brew services start postgresql@14

# Check status
psql postgresql://postgres:postgres@localhost:5432/llmready_dev -c "SELECT 1"
```

### Issue: "Redis connection failed"
**Solution**: Make sure Redis is running:
```bash
# macOS
brew services start redis

# Check status
redis-cli ping  # Should return PONG
```

### Issue: "Alembic command not found"
**Solution**: Make sure you're in the virtual environment:
```bash
source .venv/bin/activate
which alembic  # Should show path in .venv
```

---

## ✅ Success Indicators

You'll know everything is working when:

1. ✅ `pip install` completes without errors
2. ✅ `alembic upgrade head` creates stripe_events table
3. ✅ `python run_tests.py` shows 9/9 tests passed
4. ✅ FastAPI starts without errors
5. ✅ Celery worker connects to Redis
6. ✅ Celery beat shows scheduled tasks
7. ✅ Stripe webhook events process successfully
8. ✅ Events appear in stripe_events table

---

## 📝 Quick Command Reference

```bash
# Install dependencies
pip install -r requirements.txt

# Run migration
alembic upgrade head

# Run tests
python run_tests.py

# Start FastAPI
uvicorn app.main:app --reload

# Start Celery Worker
celery -A app.core.celery_app worker --loglevel=info

# Start Celery Beat
celery -A app.core.celery_app beat --loglevel=info

# Test webhook
stripe trigger invoice.payment_succeeded

# Check events in DB
psql postgresql://postgres:postgres@localhost:5432/llmready_dev \
  -c "SELECT * FROM stripe_events ORDER BY processed_at DESC LIMIT 5;"
```

---

That's it! Follow these steps and you'll be testing in minutes. 🎉
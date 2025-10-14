# LLMReady - AI-Optimized Content Generator

A SaaS platform for generating LLM-optimized content from websites, with full Stripe subscription management.

## 🚀 Quick Start

1. **Setup Backend**:
   ```bash
   cd backend
   pip install -r requirements.txt
   alembic upgrade head
   ```

2. **Configure Environment** (`.env`):
   ```env
   DATABASE_URL=postgresql://user:pass@localhost/dbname
   REDIS_URL=redis://localhost:6379/0
   STRIPE_SECRET_KEY=sk_test_...
   STRIPE_WEBHOOK_SECRET=whsec_...
   SENDGRID_API_KEY=SG...
   ```

3. **Run Services**:
   ```bash
   # Terminal 1: API
   uvicorn app.main:app --reload
   
   # Terminal 2: Celery Worker
   celery -A app.core.celery_app worker --loglevel=info
   
   # Terminal 3: Celery Beat
   celery -A app.core.celery_app beat --loglevel=info
   ```

4. **Frontend**:
   ```bash
   cd frontend
   streamlit run app.py
   ```

## 📚 Documentation

### Essential Guides
- **[Stripe Improvements Implementation](STRIPE_IMPROVEMENTS_IMPLEMENTATION.md)** - Latest Stripe integration updates (Oct 2025)
- **[Installation Guide](docs/INSTALLATION_GUIDE.md)** - Complete setup instructions
- **[Quick Reference](docs/QUICK_REFERENCE.md)** - Common tasks and commands

### Detailed Documentation (in `/docs`)
- **Authentication**: [`AUTHENTICATION_IMPLEMENTATION_SUMMARY.md`](docs/AUTHENTICATION_IMPLEMENTATION_SUMMARY.md)
- **Database**: [`DATABASE_ACCESS_GUIDE.md`](docs/DATABASE_ACCESS_GUIDE.md)
- **Stripe Setup**: [`STRIPE_SETUP_GUIDE.md`](docs/STRIPE_SETUP_GUIDE.md)
- **SendGrid**: [`SENDGRID_SETUP_GUIDE.md`](docs/SENDGRID_SETUP_GUIDE.md)
- **Testing**: [`STRIPE_LOCAL_TESTING.md`](docs/STRIPE_LOCAL_TESTING.md)

### Implementation Summaries
- [`WEEK_6_GENERATION_COMPLETE.md`](docs/WEEK_6_GENERATION_COMPLETE.md) - Generation feature
- [`WEEK_4_5_STRIPE_COMPLETE.md`](docs/WEEK_4_5_STRIPE_COMPLETE.md) - Stripe integration
- [`STRIPE_AUDIT_REPORT.md`](docs/STRIPE_AUDIT_REPORT.md) - Security audit

## 🏗️ Project Structure

```
.
├── backend/
│   ├── app/
│   │   ├── api/v1/          # API endpoints
│   │   ├── models/          # Database models
│   │   ├── services/        # Business logic
│   │   ├── tasks/           # Celery tasks
│   │   └── core/            # Configuration
│   ├── alembic/             # Database migrations
│   └── requirements.txt
├── frontend/
│   └── app.py               # Streamlit app
└── docs/                    # Documentation
```

## ✨ Features

- **Authentication**: JWT-based with email verification
- **Subscriptions**: Stripe integration with 3 tiers (Free, Standard, Pro)
- **Content Generation**: Web scraping + LLM optimization
- **Webhooks**: Full Stripe webhook coverage (11 event types)
- **Email Notifications**: SendGrid integration
- **Background Tasks**: Celery for async processing

## 🔧 Tech Stack

- **Backend**: FastAPI, PostgreSQL, Redis, Celery
- **Frontend**: Streamlit
- **Payments**: Stripe
- **Email**: SendGrid
- **Scraping**: Playwright, BeautifulSoup

## 🎯 Recent Updates (October 2025)

### Stripe Integration Improvements
All P0 critical issues resolved:
- ✅ Persistent webhook idempotency
- ✅ Proper error handling (returns 200)
- ✅ Payment success handler
- ✅ Chargeback/refund handling
- ✅ Rate limiting on checkout
- ✅ Grace period for failed payments
- ✅ Email notifications (6 types)
- ✅ Backup sync task

See [STRIPE_IMPROVEMENTS_IMPLEMENTATION.md](STRIPE_IMPROVEMENTS_IMPLEMENTATION.md) for full details.

## 📊 Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1
```

## 🧪 Testing

```bash
# Test Stripe webhook
curl -X POST http://localhost:8000/api/v1/webhooks/stripe \
  -H "Content-Type: application/json" \
  -H "stripe-signature: test" \
  -d @test_webhook.json
```

## 📝 Environment Variables

Key variables needed in `.env`:

```env
# Database
DATABASE_URL=postgresql://...

# Redis
REDIS_URL=redis://localhost:6379/0

# Stripe
STRIPE_SECRET_KEY=sk_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PRICE_STANDARD=price_...
STRIPE_PRICE_PRO=price_...

# SendGrid
SENDGRID_API_KEY=SG...
FROM_EMAIL=noreply@yourdomain.com

# App
FRONTEND_URL=http://localhost:8501
SECRET_KEY=your-secret-key
```

## 🆘 Troubleshooting

### Webhook issues
- Check `stripe_events` table for errors
- Verify `STRIPE_WEBHOOK_SECRET` is correct
- Test with Stripe CLI: `stripe listen --forward-to localhost:8000/api/v1/webhooks/stripe`

### Database connection
- Verify PostgreSQL is running
- Check DATABASE_URL format
- Run migrations: `alembic upgrade head`

### Email not sending
- Verify SendGrid API key
- Check SendGrid dashboard for errors
- Test with: `python backend/test_sendgrid.py`

## 📄 License

Proprietary - All rights reserved

## 👥 Support

For issues or questions, check the documentation in `/docs` or review implementation summaries.
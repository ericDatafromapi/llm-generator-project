# 📚 Documentation Index

Welcome to the LLMReady documentation! All documentation is organized by topic for easy navigation.

## 🚀 Quick Start

**New to the project?** Start here:
- [START HERE](START_HERE.md) - Project overview and getting started
- [Quick Start Guide](QUICK_START_GUIDE.md) - Get running in 5 minutes
- [Installation Guide](INSTALLATION_GUIDE.md) - Detailed installation instructions

## 📂 Documentation by Topic

### 🚢 Deployment & CI/CD
Location: [`docs/deployment/`](deployment/)

- **[Deployment Quick Start](deployment/DEPLOYMENT_QUICKSTART.md)** - Deploy in 5 steps
- **[Complete Deployment Guide](deployment/CI_CD_DEPLOYMENT_GUIDE.md)** - Comprehensive deployment documentation
- **[Setup Complete Guide](deployment/DEPLOYMENT_SETUP_COMPLETE.md)** - What's been set up and next steps
- **[SSH Key Setup](deployment/SSH_KEY_CLARIFICATION.md)** - SSH key options explained
- **[CI/CD Fixes](deployment/CI_CD_FIXES.md)** - Common CI/CD issues and solutions

### 🔐 Authentication & Security
- [Authentication Implementation](AUTHENTICATION_IMPLEMENTATION_SUMMARY.md) - Auth system overview
- [SendGrid Setup](SENDGRID_SETUP_GUIDE.md) - Email configuration

### 💳 Payments & Subscriptions
- [Stripe Implementation](STRIPE_IMPLEMENTATION_SUMMARY.md) - Payment processing overview
- [Stripe Setup Guide](STRIPE_SETUP_GUIDE.md) - Step-by-step Stripe configuration
- [Stripe Local Testing](STRIPE_LOCAL_TESTING.md) - Testing payments locally
- [How to Find Stripe Price IDs](HOW_TO_FIND_STRIPE_PRICE_IDS.md) - Locating your price IDs
- [Subscription Management](../SUBSCRIPTION_MANAGEMENT_GUIDE.md) - Managing user subscriptions

### 🗄️ Database
- [Database Access Guide](DATABASE_ACCESS_GUIDE.md) - Managing the database
- [Stripe Fixes Verified](STRIPE_FIXES_VERIFIED.md) - Database-related Stripe fixes

### 🏗️ Architecture & Planning
- [Final Hybrid Plan](FINAL_HYBRID_PLAN.md) - Overall architecture
- [Stripe Audit Report](STRIPE_AUDIT_REPORT.md) - Stripe integration review
- [Stripe Improvements](STRIPE_IMPROVEMENTS_IMPLEMENTATION.md) - Enhancement details

### 📝 Weekly Progress Reports
- [Week 1 Summary](WEEK_1_SUMMARY.md) - Foundation
- [Week 4-5: Stripe Complete](WEEK_4_5_STRIPE_COMPLETE.md) - Payment integration
- [Week 6: Generation Complete](WEEK_6_GENERATION_COMPLETE.md) - Generation features
- [Week 6 Quick Start](WEEK_6_QUICK_START.md) - Week 6 setup
- [Week 7: Websites Complete](WEEK_7_WEBSITES_COMPLETE.md) - Website features
- [Week 7 Quick Start](WEEK_7_QUICK_START.md) - Week 7 setup

### 📖 Reference
- [Quick Reference](QUICK_REFERENCE.md) - Common commands and tips
- [Next Steps](NEXT_STEPS.md) - What to do next

## 🎯 Common Tasks

### Development
```bash
# Start local development
docker-compose up -d
cd backend && uvicorn app.main:app --reload
cd frontend && npm run dev
```

### Deployment
```bash
# Deploy to production
./scripts/deploy.sh
```

### Database
```bash
# Run migrations
cd backend && alembic upgrade head

# Create new migration
alembic revision --autogenerate -m "description"
```

### Testing
```bash
# Backend tests
cd backend && python run_tests.py

# Frontend build
cd frontend && npm run build
```

## 🆘 Troubleshooting

Having issues? Check these guides:
- [CI/CD Fixes](deployment/CI_CD_FIXES.md) - Common CI/CD problems
- [Deployment Troubleshooting](deployment/CI_CD_DEPLOYMENT_GUIDE.md#troubleshooting) - Deployment issues
- [Stripe Integration Verification](stripe_integration_verification.md) - Payment problems

## 📞 Need Help?

1. Check the relevant documentation section above
2. Search for your issue in the [CI/CD Fixes](deployment/CI_CD_FIXES.md)
3. Review the [Troubleshooting Guide](deployment/CI_CD_DEPLOYMENT_GUIDE.md#troubleshooting)
4. Create an issue on GitHub

---

**Tip**: Use `Cmd+F` (Mac) or `Ctrl+F` (Windows) to search this page for specific topics!
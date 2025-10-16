# 🌐 LLMReady - AI-Powered Website Intelligence Platform

A full-stack SaaS application that provides AI-powered insights and recommendations for websites.

## 📚 Documentation

**[📖 View Complete Documentation →](docs/README.md)**

All documentation has been organized by topic in the `docs/` folder for easy navigation.

---

## 🚀 Quick Start

### Local Development
```bash
# 1. Start services
docker-compose up -d

# 2. Set up backend
cd backend
cp .env.example .env
# Edit .env with your credentials
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload

# 3. Set up frontend
cd frontend
cp .env.example .env
npm install
npm run dev
```

Visit: http://localhost:5173

### Deploy to Production
```bash
# One command deployment!
./scripts/deploy.sh
```

Or use VSCode: `Cmd+Shift+P` → **Tasks: Run Task** → **🚀 Deploy to Production**

---

## 📖 Key Documentation

### Getting Started
- [Quick Start Guide](docs/QUICK_START_GUIDE.md) - 5-minute setup
- [Installation Guide](docs/INSTALLATION_GUIDE.md) - Detailed installation
- [Start Here](docs/START_HERE.md) - Project overview

### Deployment
- [🚀 Deploy in 5 Steps](docs/deployment/DEPLOYMENT_QUICKSTART.md)
- [Complete Deployment Guide](docs/deployment/CI_CD_DEPLOYMENT_GUIDE.md)
- [CI/CD Fixes](docs/deployment/CI_CD_FIXES.md)
- [SSH Key Setup](docs/deployment/SSH_KEY_CLARIFICATION.md)

### Development
- [Authentication](docs/AUTHENTICATION_IMPLEMENTATION_SUMMARY.md)
- [Database Guide](docs/DATABASE_ACCESS_GUIDE.md)
- [Stripe Integration](docs/STRIPE_IMPLEMENTATION_SUMMARY.md)
- [SendGrid Setup](docs/SENDGRID_SETUP_GUIDE.md)

---

## 🛠️ Tech Stack

**Backend:** FastAPI, PostgreSQL, Redis, Celery, Stripe, SendGrid  
**Frontend:** React, TypeScript, Tailwind CSS, shadcn/ui  
**DevOps:** Docker, GitHub Actions, Nginx

---

## ✨ Features

### For Users
- 🌐 Website analysis and insights
- 🤖 AI-powered recommendations
- 📊 Performance tracking
- 💳 Flexible subscription plans
- 📧 Email notifications

### For Developers
- ✅ Automated PR testing
- 🚀 One-command deployment
- 🔄 Zero-downtime deployments
- 📧 Email notifications for CI/CD
- 🐳 Docker containerization
- 🔒 Production-ready SSL setup

---

## 📋 VSCode Tasks

Press `Cmd+Shift+P` → **Tasks: Run Task**:

- 🚀 **Deploy to Production** - One-click deployment
- 🧪 **Run Backend Tests** - Execute test suite
- 🎨 **Build Frontend** - Production build
- 🐳 **Start/Stop Docker Services** - Manage containers
- 📊 **View Docker Logs** - Monitor logs

---

## 🎯 Common Commands

```bash
# Development
docker-compose up -d              # Start services
cd backend && uvicorn app.main:app --reload
cd frontend && npm run dev

# Testing
cd backend && python run_tests.py
cd frontend && npm run build

# Database
cd backend && alembic upgrade head
alembic revision --autogenerate -m "description"

# Deployment
./scripts/deploy.sh              # Deploy to production
```

---

## 🆘 Need Help?

1. Check the [Documentation Index](docs/README.md)
2. Review [CI/CD Fixes](docs/deployment/CI_CD_FIXES.md)
3. See [Troubleshooting Guide](docs/deployment/CI_CD_DEPLOYMENT_GUIDE.md#troubleshooting)

---

## 📄 License

[Your License Here]

---

Made with ❤️ by [Your Name]
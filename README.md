# 🌐 LLMReady - AI-Powered Website Intelligence Platform

A full-stack SaaS application that provides AI-powered insights and recommendations for websites.

## 📚 Documentation

### Getting Started
- **[Quick Start Guide](QUICK_START_GUIDE.md)** - Get up and running in 5 minutes
- **[Installation Guide](INSTALLATION_GUIDE.md)** - Detailed setup instructions
- **[Start Here](START_HERE.md)** - Project overview and architecture

### Development
- **[Authentication Implementation](AUTHENTICATION_IMPLEMENTATION_SUMMARY.md)** - Auth system details
- **[Database Access Guide](DATABASE_ACCESS_GUIDE.md)** - Database management
- **[Stripe Integration](STRIPE_IMPLEMENTATION_SUMMARY.md)** - Payment processing
- **[SendGrid Setup](SENDGRID_SETUP_GUIDE.md)** - Email configuration

### Deployment & CI/CD
- **[🚀 Deployment Quick Start](DEPLOYMENT_QUICKSTART.md)** - Deploy in 5 steps
- **[📖 Complete Deployment Guide](CI_CD_DEPLOYMENT_GUIDE.md)** - Comprehensive CI/CD documentation
- **[🔑 GitHub Secrets Template](.github/SECRETS_TEMPLATE.md)** - Required secrets configuration

## 🚀 Quick Deploy

Deploy to production with one command from VSCode:

```bash
./scripts/deploy.sh
```

Or use VSCode Command Palette: `Cmd+Shift+P` → **Tasks: Run Task** → **🚀 Deploy to Production**

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

## 🛠️ Tech Stack

### Backend
- **Framework**: FastAPI (Python)
- **Database**: PostgreSQL
- **Cache**: Redis
- **Task Queue**: Celery
- **Payments**: Stripe
- **Email**: SendGrid

### Frontend
- **Framework**: React + TypeScript
- **UI Library**: Tailwind CSS + shadcn/ui
- **State**: Zustand
- **Routing**: React Router
- **HTTP**: Axios

### DevOps
- **CI/CD**: GitHub Actions
- **Containers**: Docker + Docker Compose
- **Web Server**: Nginx
- **SSL**: Let's Encrypt (Certbot)

## 📦 Project Structure

```
.
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── api/            # API routes
│   │   ├── core/           # Core configuration
│   │   ├── models/         # Database models
│   │   ├── schemas/        # Pydantic schemas
│   │   ├── services/       # Business logic
│   │   └── tasks/          # Celery tasks
│   ├── alembic/            # Database migrations
│   └── tests/              # Backend tests
├── frontend/               # React frontend
│   ├── src/
│   │   ├── components/    # React components
│   │   ├── pages/         # Page components
│   │   ├── lib/           # Utilities
│   │   └── store/         # State management
├── scripts/               # Deployment scripts
│   ├── deploy.sh          # Deploy from VSCode
│   └── server-setup.sh    # Server setup script
├── .github/               # GitHub configuration
│   └── workflows/         # CI/CD workflows
│       ├── pr-test.yml           # PR testing
│       └── deploy-production.yml  # Production deployment
└── docs/                  # Additional documentation
```

## 🏁 Getting Started

### Local Development

1. **Clone the repository**
```bash
git clone <your-repo-url>
cd llmready
```

2. **Start services**
```bash
docker-compose up -d
```

3. **Set up backend**
```bash
cd backend
cp .env.example .env
# Edit .env with your credentials
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

4. **Set up frontend**
```bash
cd frontend
cp .env.example .env
# Edit .env with your API URL
npm install
npm run dev
```

Visit: http://localhost:5173

### Production Deployment

See **[Deployment Quick Start](DEPLOYMENT_QUICKSTART.md)** for step-by-step instructions.

## 🔧 Configuration

### Environment Variables

#### Backend (`.env`)
```env
DATABASE_URL=postgresql://...
REDIS_URL=redis://...
SECRET_KEY=your-secret-key
STRIPE_SECRET_KEY=sk_...
STRIPE_WEBHOOK_SECRET=whsec_...
SENDGRID_API_KEY=SG...
FRONTEND_URL=http://localhost:5173
```

#### Frontend (`.env`)
```env
VITE_API_URL=http://localhost:8000
VITE_STRIPE_PUBLIC_KEY=pk_...
```

See [`.env.example`](backend/.env.example) files for complete configuration.

## 🧪 Testing

### Run Backend Tests
```bash
cd backend
python run_tests.py
```

Or use VSCode: `Cmd+Shift+P` → **Tasks: Run Task** → **🧪 Run Backend Tests**

### Run Frontend Build
```bash
cd frontend
npm run build
```

Or use VSCode: `Cmd+Shift+P` → **Tasks: Run Task** → **🎨 Build Frontend**

## 📝 Available VSCode Tasks

Press `Cmd+Shift+P` → **Tasks: Run Task** to access:

- 🚀 **Deploy to Production** - One-click deployment
- 🧪 **Run Backend Tests** - Execute test suite
- 🎨 **Build Frontend** - Production build
- 🐳 **Start Docker Services** - Start all services
- 🛑 **Stop Docker Services** - Stop all services
- 📊 **View Docker Logs** - Monitor container logs

## 🔄 CI/CD Pipeline

### Automated PR Testing
Every pull request automatically:
- ✅ Runs backend tests with PostgreSQL and Redis
- ✅ Runs frontend linting and build
- ✅ Validates Docker configuration
- ✅ Sends email notification with results

### Production Deployment
Deployments automatically:
- ✅ Run full test suite
- ✅ Build production frontend
- ✅ Deploy backend with zero downtime
- ✅ Run database migrations
- ✅ Deploy frontend to nginx
- ✅ Send email notification with status

## 🔒 Security

- JWT authentication
- Password hashing with bcrypt
- Rate limiting on sensitive endpoints
- CORS configuration
- SQL injection prevention (SQLAlchemy ORM)
- Environment-based secrets
- SSL/HTTPS in production

## 📧 Email Notifications

Configure email settings in GitHub Secrets to receive notifications for:
- Pull request test results
- Deployment successes
- Deployment failures
- System alerts

## 🗄️ Database Migrations

Create migration:
```bash
cd backend
alembic revision --autogenerate -m "Description"
```

Apply migrations:
```bash
alembic upgrade head
```

Rollback:
```bash
alembic downgrade -1
```

## 🐳 Docker Commands

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# View logs
docker-compose logs -f

# Rebuild containers
docker-compose up -d --build

# Check status
docker-compose ps
```

## 🆘 Troubleshooting

See the **[Complete Deployment Guide](CI_CD_DEPLOYMENT_GUIDE.md#troubleshooting)** for detailed troubleshooting steps.

Common issues:
- [SSH Connection Failed](CI_CD_DEPLOYMENT_GUIDE.md#1-ssh-connection-failed)
- [Docker Permission Denied](CI_CD_DEPLOYMENT_GUIDE.md#2-docker-permission-denied)
- [Database Connection Failed](CI_CD_DEPLOYMENT_GUIDE.md#4-database-connection-failed)
- [Email Notifications Not Sending](CI_CD_DEPLOYMENT_GUIDE.md#7-email-notifications-not-sending)

## 📚 Additional Resources

- [Stripe Local Testing](STRIPE_LOCAL_TESTING.md)
- [Subscription Management](SUBSCRIPTION_MANAGEMENT_GUIDE.md)
- [Week-by-Week Progress](WEEK_1_SUMMARY.md)

## 🤝 Contributing

1. Create a feature branch: `git checkout -b feature/my-feature`
2. Make your changes
3. Commit: `git commit -m "Add feature"`
4. Push: `git push origin feature/my-feature`
5. Create a Pull Request
6. Automated tests will run
7. Merge after review and passing tests

## 📄 License

[Your License Here]

## 🙏 Support

For issues and questions:
- Check the [Deployment Guide](CI_CD_DEPLOYMENT_GUIDE.md)
- Review [Troubleshooting](CI_CD_DEPLOYMENT_GUIDE.md#troubleshooting)
- Create an issue on GitHub

---

Made with ❤️ by [Your Name]
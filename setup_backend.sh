#!/bin/bash

# LLMReady Backend Setup Script
# Automates the Week 1 backend setup process

set -e  # Exit on error

echo "🚀 LLMReady Backend Setup"
echo "=========================="
echo ""

# Check if we're in the right directory
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ Error: Please run this script from the project root directory"
    exit 1
fi

# Step 1: Check Docker
echo "📦 Step 1: Checking Docker..."
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker Desktop:"
    echo "   brew install --cask docker"
    exit 1
fi

if ! docker info &> /dev/null; then
    echo "❌ Docker is not running. Please start Docker Desktop and try again."
    exit 1
fi
echo "✅ Docker is running"
echo ""

# Step 2: Create virtual environment
echo "🐍 Step 2: Creating Python virtual environment..."
cd backend
if [ -d "venv" ]; then
    echo "⚠️  Virtual environment already exists. Skipping..."
else
    python3 -m venv venv
    echo "✅ Virtual environment created"
fi
echo ""

# Step 3: Install dependencies
echo "📚 Step 3: Installing Python dependencies..."
source venv/bin/activate
pip install --upgrade pip > /dev/null 2>&1
pip install -r requirements.txt
echo "✅ Dependencies installed"
echo ""

# Step 4: Create .env file
echo "⚙️  Step 4: Creating .env file..."
if [ -f ".env" ]; then
    echo "⚠️  .env file already exists. Skipping..."
else
    cp .env.example .env
    echo "✅ .env file created"
fi
echo ""

# Step 5: Start Docker services
echo "🐳 Step 5: Starting Docker services..."
cd ..
docker compose up -d
echo "✅ Docker services started"
echo ""

# Wait for PostgreSQL to be ready
echo "⏳ Waiting for PostgreSQL to be ready..."
sleep 5
until docker exec llmready_postgres pg_isready -U postgres > /dev/null 2>&1; do
    echo "   Still waiting..."
    sleep 2
done
echo "✅ PostgreSQL is ready"
echo ""

# Step 6: Setup Alembic (if not already done)
echo "🗄️  Step 6: Setting up Alembic..."
cd backend
if [ -d "alembic" ]; then
    echo "⚠️  Alembic already initialized. Skipping..."
else
    alembic init alembic
    
    # Update alembic.ini
    sed -i.bak 's|^sqlalchemy.url = .*|sqlalchemy.url = postgresql://postgres:postgres@localhost:5432/llmready_dev|' alembic.ini
    
    # Update alembic/env.py
    # Note: This is a simplified version - you may need to manually edit this file
    echo "⚠️  Please manually update alembic/env.py as described in NEXT_STEPS.md"
    echo "✅ Alembic initialized"
fi
echo ""

# Step 7: Instructions for migrations
echo "📝 Next Steps:"
echo "=============="
echo ""
echo "1. Update alembic/env.py with the following changes:"
echo "   - Add: from app.core.database import Base"
echo "   - Add: from app.models import *"
echo "   - Change: target_metadata = Base.metadata"
echo ""
echo "2. Create and apply migration:"
echo "   cd backend"
echo "   source venv/bin/activate"
echo "   alembic revision --autogenerate -m \"Initial schema\""
echo "   alembic upgrade head"
echo ""
echo "3. Start the FastAPI server:"
echo "   uvicorn app.main:app --reload"
echo ""
echo "4. Test the health endpoint:"
echo "   curl http://localhost:8000/health"
echo ""
echo "5. Open API docs in browser:"
echo "   http://localhost:8000/api/docs"
echo ""
echo "✨ Setup script completed! Follow the steps above to finish."
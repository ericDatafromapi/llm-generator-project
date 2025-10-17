#!/bin/bash
# Quick fix for production database - create tables

echo "=========================================="
echo "🔧 Fixing Production Database Tables"
echo "=========================================="
echo ""

cd /opt/llmready/backend

echo "Step 1: Checking if tables exist..."
docker exec -i $(docker ps -qf "name=postgres") psql -U postgres -d llmready_prod -c "\dt" 2>&1 | head -20

echo ""
echo "Step 2: Exporting DATABASE_URL..."
export $(grep DATABASE_URL .env | xargs)
echo "Using database: $DATABASE_URL"

echo ""
echo "Step 3: Running migrations..."
source ../venv/bin/activate
alembic upgrade head

echo ""
echo "Step 4: Verifying tables created..."
docker exec -i $(docker ps -qf "name=postgres") psql -U postgres -d llmready_prod -c "\dt"

echo ""
echo "Step 5: Restarting backend..."
sudo systemctl restart llmready-backend

echo ""
echo "=========================================="
echo "✅ Done! Try registering a user now."
echo "=========================================="
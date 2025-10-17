#!/bin/bash
# Recreate llmready_prod database and run migrations

echo "=========================================="
echo "🔧 Recreating llmready_prod Database"
echo "=========================================="
echo ""

cd /opt/llmready

echo "Step 1: Creating database..."
docker exec -i $(docker ps -qf "name=postgres") psql -U postgres -c "CREATE DATABASE llmready_prod;"

if [ $? -eq 0 ]; then
    echo "✅ Database created"
else
    echo "⚠️  Database might already exist or creation failed"
fi

echo ""
echo "Step 2: Running migrations..."
cd backend
source ../venv/bin/activate
alembic upgrade head

if [ $? -eq 0 ]; then
    echo "✅ Migrations completed"
else
    echo "❌ Migration failed"
    exit 1
fi

echo ""
echo "Step 3: Verifying database..."
docker exec -i $(docker ps -qf "name=postgres") psql -U postgres -d llmready_prod -c "\dt"

echo ""
echo "Step 4: Restarting backend..."
sudo systemctl restart llmready-backend

echo ""
echo "=========================================="
echo "✅ Database Recreation Complete"
echo "=========================================="
echo ""
echo "Try registering a user now!"
echo "=========================================="
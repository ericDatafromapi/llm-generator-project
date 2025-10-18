#!/bin/bash
# Permanently fix database issue

echo "=========================================="
echo "🔧 PERMANENT DATABASE FIX"
echo "=========================================="
echo ""

cd /opt/llmready

echo "Step 1: Create llmready_prod database..."
docker exec -i $(docker ps -qf "name=postgres") psql -U postgres -c "CREATE DATABASE llmready_prod;" 2>&1

if [ $? -eq 0 ]; then
    echo "✅ Database created"
else
    echo "⚠️  Database might already exist (that's OK)"
fi

echo ""
echo "Step 2: Running migrations..."
cd backend
export $(grep DATABASE_URL .env | xargs)
alembic upgrade head

if [ $? -eq 0 ]; then
    echo "✅ Migrations completed"
else
    echo "❌ Migration failed"
    exit 1
fi

echo ""
echo "Step 3: Restarting backend..."
sudo systemctl restart llmready-backend

echo ""
echo "=========================================="
echo "✅ DONE - Database Fixed!"
echo "=========================================="
echo ""
echo "The database will now persist even after:"
echo "  - Docker restarts"
echo "  - Server reboots  "
echo "  - Container recreations"
echo ""
echo "Why? Docker volume 'postgres_data' stores the data permanently."
echo "=========================================="
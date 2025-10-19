#!/bin/bash
# EMERGENCY: Fix database tables and prevent future loss

echo "=========================================="
echo "🚨 EMERGENCY DATABASE FIX"
echo "=========================================="
echo ""

cd /opt/llmready

echo "PROBLEM IDENTIFIED:"
echo "  Database exists but tables are EMPTY"
echo "  This happens when migrations don't run after container restart"
echo ""

echo "Step 1: Check current state..."
docker exec -i $(docker ps -qf "name=postgres") psql -U postgres -d llmready_prod -c "\dt" 2>&1 | head -5

echo ""
echo "Step 2: Running migrations NOW..."
cd backend
source ../venv/bin/activate
export $(grep DATABASE_URL .env | xargs)

echo "DATABASE_URL: $DATABASE_URL"

alembic upgrade head

if [ $? -eq 0 ]; then
    echo "✅ Migrations completed successfully"
else
    echo "❌ Migration failed!"
    exit 1
fi

echo ""
echo "Step 3: Verifying tables exist..."
cd ..
docker exec -i $(docker ps -qf "name=postgres") psql -U postgres -d llmready_prod -c "\dt"

echo ""
echo "Step 4: Creating startup script to run migrations automatically..."
cat > /opt/llmready/ensure-database.sh << 'SCRIPT'
#!/bin/bash
# Run this after every docker-compose up to ensure database is ready

cd /opt/llmready/backend
source ../venv/bin/activate
export $(grep DATABASE_URL .env | xargs)

# Create database if doesn't exist
DB_NAME=$(echo $DATABASE_URL | sed 's/.*\///')
docker exec -i $(docker ps -qf "name=postgres") psql -U postgres -c "CREATE DATABASE $DB_NAME;" 2>/dev/null || true

# Run migrations
alembic upgrade head
SCRIPT

chmod +x /opt/llmready/ensure-database.sh

echo ""
echo "Step 5: Restarting backend..."
sudo systemctl restart llmready-backend

echo ""
echo "=========================================="
echo "✅ EMERGENCY FIX COMPLETE"
echo "=========================================="
echo ""
echo "What was fixed:"
echo "  ✅ Migrations ran - tables created"
echo "  ✅ Created ensure-database.sh script"
echo ""
echo "IMPORTANT - Run after ANY docker restart:"
echo "  cd /opt/llmready && ./ensure-database.sh"
echo ""
echo "This ensures tables exist even if container restarts."
echo "=========================================="
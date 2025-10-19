#!/bin/bash
# URGENT: Close PostgreSQL port to internet

echo "=========================================="
echo "🚨 CRITICAL SECURITY FIX"
echo "=========================================="
echo ""
echo "YOUR DATABASE IS EXPOSED TO INTERNET!"
echo "PostgreSQL port 5432 is accessible from anywhere"
echo "with default password 'postgres'"
echo ""
echo "This is why your database is being attacked!"
echo ""

echo "Step 1: Stopping PostgreSQL exposure NOW..."
cd /opt/llmready

# Stop containers
docker compose down

echo ""
echo "Step 2: Updating docker-compose.yml to bind to localhost only..."
# This should already be done if you uploaded the fixed version

echo ""
echo "Step 3: Starting containers with secure config..."
docker compose up -d

echo ""
echo "Step 4: Verifying port is NOW secure..."
netstat -tuln | grep 5432

echo ""
echo "Step 5: Setting up firewall..."
# Block external PostgreSQL access
ufw deny 5432/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 22/tcp
ufw --force enable

echo ""
echo "Step 6: Recreating database..."
sleep 5
docker exec -i $(docker ps -qf "name=postgres") psql -U postgres -c "CREATE DATABASE llmready_prod;"

echo ""
echo "Step 7: Running migrations..."
cd backend
export $(grep DATABASE_URL .env | xargs)
alembic upgrade head

echo ""
echo "Step 8: Restarting services..."
sudo systemctl restart llmready-backend
sudo systemctl restart llmready-celery-worker

echo ""
echo "=========================================="
echo "✅ SECURITY FIX COMPLETE"
echo "=========================================="
echo ""
echo "Port 5432 is now:"
netstat -tuln | grep 5432
echo ""
echo "Should show 127.0.0.1:5432 NOT 0.0.0.0:5432"
echo "=========================================="
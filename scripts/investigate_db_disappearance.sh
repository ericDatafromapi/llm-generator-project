#!/bin/bash
# Investigate why llmready_prod keeps disappearing

echo "=========================================="
echo "🔍 DATABASE DISAPPEARANCE INVESTIGATION"
echo "=========================================="
echo ""

cd /opt/llmready

echo "1️⃣ Checking Docker Compose configuration..."
echo ""
cat docker-compose.yml | grep -A 10 "postgres:"

echo ""
echo "2️⃣ Checking if PostgreSQL data is persisted..."
echo ""
docker inspect $(docker ps -qf "name=postgres") | grep -A 5 "Mounts"

echo ""
echo "3️⃣ Listing all databases..."
echo ""
docker exec -i $(docker ps -qf "name=postgres") psql -U postgres -c "\l"

echo ""
echo "4️⃣ Checking PostgreSQL logs for database drops..."
echo ""
docker logs $(docker ps -qf "name=postgres") 2>&1 | grep -i "drop database\|database.*dropped\|llmready_prod" | tail -20

echo ""
echo "5️⃣ Checking for backup files..."
echo ""
ls -lht /opt/llmready/backups/database/ 2>/dev/null | head -5 || echo "No backups found"

echo ""
echo "=========================================="
echo "📊 ANALYSIS"
echo "=========================================="
echo ""
echo "If PostgreSQL has no persistent volume:"
echo "  → Database is lost on container restart!"
echo "  → Fix: Add volume in docker-compose.yml"
echo ""
echo "If logs show 'DROP DATABASE':"
echo "  → Something is deleting it"
echo "  → Check cron jobs and scripts"
echo ""
echo "If backups exist:"
echo "  → We can restore from backup"
echo "=========================================="
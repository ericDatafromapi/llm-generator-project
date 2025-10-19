#!/bin/bash
# CRITICAL: Investigate what's deleting llmready_prod database

echo "=========================================="
echo "🚨 DATABASE DELETION INVESTIGATION"
echo "=========================================="
echo ""

cd /opt/llmready

echo "1️⃣ Checking if database currently exists..."
echo ""
docker exec -i $(docker ps -qf "name=postgres") psql -U postgres -c "\l" | grep -E "llmready|Name"

echo ""
echo "2️⃣ Checking Docker volume persistence..."
echo ""
docker volume ls | grep postgres
docker volume inspect $(docker volume ls -q | grep postgres) | grep -A 5 "Mountpoint"

echo ""
echo "3️⃣ Checking PostgreSQL container uptime..."
echo ""
docker ps -a | grep postgres
echo ""
echo "Container created:"
docker inspect $(docker ps -qf "name=postgres") | grep -A 2 "Created"

echo ""
echo "4️⃣ Checking PostgreSQL logs for DROP commands..."
echo ""
docker logs $(docker ps -qf "name=postgres") 2>&1 | grep -i "drop database\|database.*dropped" || echo "  No DROP DATABASE commands found"

echo ""
echo "5️⃣ Checking for cron jobs that might affect database..."
echo ""
crontab -l 2>/dev/null | grep -i "postgres\|database\|backup" || echo "  No cron jobs found"

echo ""
echo "6️⃣ Checking systemd timers..."
echo ""
systemctl list-timers --all | grep -i "backup\|database\|postgres" || echo "  No related timers"

echo ""
echo "7️⃣ Checking backup script for dangerous commands..."
echo ""
if [ -f "/opt/llmready/scripts/backup_database.py" ]; then
    grep -n "DROP\|drop\|DELETE.*database\|delete.*database" /opt/llmready/scripts/backup_database.py || echo "  No dangerous commands in backup script"
fi

echo ""
echo "8️⃣ Checking docker-compose.yml current state..."
echo ""
cat docker-compose.yml | grep -A 3 "POSTGRES_DB:"

echo ""
echo "9️⃣ Checking server logs for docker events..."
echo ""
journalctl --since "24 hours ago" | grep -i "docker.*postgres\|postgres.*stop\|postgres.*remove" | tail -20 || echo "  No docker postgres events in last 24h"

echo ""
echo "🔟 Checking if database tables exist RIGHT NOW..."
echo ""
docker exec -i $(docker ps -qf "name=postgres") psql -U postgres -d llmready_prod -c "\dt" 2>&1

echo ""
echo "=========================================="
echo "📊 DIAGNOSIS QUESTIONS"
echo "=========================================="
echo ""
echo "1. Does llmready_prod exist in step 1?"
echo "2. Is the container recently created (step 3)?"
echo "3. Any DROP DATABASE in logs (step 4)?"
echo "4. Any dangerous cron jobs or timers (steps 5-6)?"
echo "5. Does docker-compose.yml show llmready_prod (step 8)?"
echo ""
echo "Share this complete output for analysis."
echo "=========================================="
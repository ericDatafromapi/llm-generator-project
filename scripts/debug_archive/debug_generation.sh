#!/bin/bash
# REAL-TIME DEBUGGING - Shows what happens when you create a generation

echo "=========================================="
echo "🔍 GENERATION DEBUG - Real-time Monitoring"
echo "=========================================="
echo ""

echo "This script will monitor:"
echo "  1. Backend API logs"
echo "  2. Celery worker logs"
echo "  3. Redis queue status"
echo "  4. Database generation records"
echo ""
echo "=========================================="
echo "📊 CURRENT STATE"
echo "=========================================="

# 1. Check services
echo ""
echo "Services Status:"
echo "  Backend: $(systemctl is-active llmready-backend || echo 'STOPPED')"
echo "  Celery Worker: $(systemctl is-active llmready-celery-worker || echo 'STOPPED')"
echo "  Redis: $(docker ps --filter 'name=redis' --format '{{.Status}}' || echo 'NOT RUNNING')"

# 2. Check if worker sees tasks
echo ""
echo "Celery Worker Tasks (last 10 lines):"
sudo journalctl -u llmready-celery-worker -n 10 --no-pager | grep -i "task\|ready" || echo "  No task info in logs"

# 3. Check Redis queues
echo ""
echo "Redis Queue Status:"
if command -v redis-cli &> /dev/null; then
    echo "  Celery queue: $(redis-cli LLEN celery) tasks"
    echo "  Generation queue: $(redis-cli LLEN generation) tasks"
else
    echo "  Using docker exec..."
    docker exec -it $(docker ps -qf "name=redis") redis-cli LLEN celery | xargs echo "  Celery queue:" || echo "  Could not check"
    docker exec -it $(docker ps -qf "name=redis") redis-cli LLEN generation | xargs echo "  Generation queue:" || echo "  Could not check"
fi

# 4. Check recent generations
echo ""
echo "Recent Generations (database):"
sudo -u postgres psql -d llmready_prod -c "SELECT id, status, created_at, error_message FROM generations ORDER BY created_at DESC LIMIT 3;" 2>/dev/null || echo "  Could not query database"

echo ""
echo "=========================================="
echo "👀 NOW WATCHING IN REAL-TIME"
echo "=========================================="
echo ""
echo "In a separate terminal, create a generation from the frontend."
echo ""
echo "Press Ctrl+C to stop monitoring"
echo ""
echo "=========================================="
sleep 2

# Monitor both backend and celery worker in real-time
sudo journalctl -u llmready-backend -u llmready-celery-worker -f --since "now"
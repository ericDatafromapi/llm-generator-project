#!/bin/bash
# ONE SIMPLE SCRIPT TO FIX EVERYTHING

set -e

echo "=========================================="
echo "🔧 FIXING CELERY WORKER - ONE COMMAND"
echo "=========================================="
echo ""

cd /opt/llmready

echo "Step 1: Checking current status..."
echo ""

# Check if worker exists
if ! systemctl list-unit-files | grep -q "llmready-celery-worker"; then
    echo "❌ Service not installed. Installing..."
    sudo cp scripts/llmready-celery-worker.service /etc/systemd/system/
    sudo systemctl daemon-reload
fi

# Stop worker
echo "Step 2: Stopping worker (if running)..."
sudo systemctl stop llmready-celery-worker 2>/dev/null || true

# Pull latest code
echo "Step 3: Pulling latest code..."
git pull origin main || echo "⚠️  Could not pull (may already be up to date)"

# Restart backend to ensure latest code
echo "Step 4: Restarting backend..."
sudo systemctl restart llmready-backend

# Start worker
echo "Step 5: Starting Celery worker..."
sudo systemctl start llmready-celery-worker

# Enable auto-start
echo "Step 6: Enabling auto-start..."
sudo systemctl enable llmready-celery-worker

# Wait for worker to initialize
echo "Step 7: Waiting for worker to initialize..."
sleep 3

echo ""
echo "=========================================="
echo "📊 SERVICE STATUS"
echo "=========================================="

# Check backend
echo "Backend:"
systemctl is-active llmready-backend && echo "  ✅ RUNNING" || echo "  ❌ STOPPED"

# Check worker
echo "Celery Worker:"
systemctl is-active llmready-celery-worker && echo "  ✅ RUNNING" || echo "  ❌ STOPPED"

# Check beat
echo "Celery Beat:"
systemctl is-active llmready-celery-beat 2>/dev/null && echo "  ✅ RUNNING" || echo "  ⚠️  Not running (optional)"

echo ""
echo "=========================================="
echo "📝 WORKER LOGS (Last 15 lines)"
echo "=========================================="
sudo journalctl -u llmready-celery-worker -n 15 --no-pager

echo ""
echo "=========================================="
echo "✅ DONE! Now test from frontend:"
echo "=========================================="
echo "1. Go to your frontend"
echo "2. Create a website"
echo "3. Click 'Generate Files'"
echo "4. Watch logs: sudo journalctl -u llmready-celery-worker -f"
echo ""
echo "You should see: 'Task app.tasks.generation.generate_llm_content[...]'"
echo "=========================================="
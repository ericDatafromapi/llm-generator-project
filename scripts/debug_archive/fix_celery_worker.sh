#!/bin/bash
# Simple script to fix Celery worker service

echo "=========================================="
echo "🔧 Fixing Celery Worker Service"
echo "=========================================="
echo ""

# Check if service is running
echo "1. Checking if Celery worker is running..."
if systemctl is-active --quiet llmready-celery-worker; then
    echo "✅ Celery worker is already running"
    sudo systemctl status llmready-celery-worker --no-pager -l
else
    echo "❌ Celery worker is NOT running"
    echo ""
    echo "2. Starting Celery worker..."
    sudo systemctl start llmready-celery-worker
    sleep 2
    
    if systemctl is-active --quiet llmready-celery-worker; then
        echo "✅ Celery worker started successfully!"
    else
        echo "❌ Failed to start Celery worker"
        echo ""
        echo "Checking logs for errors:"
        sudo journalctl -u llmready-celery-worker -n 30 --no-pager
        exit 1
    fi
fi

echo ""
echo "3. Enabling auto-start on boot..."
sudo systemctl enable llmready-celery-worker

echo ""
echo "4. Verifying worker is ready..."
sleep 2
sudo journalctl -u llmready-celery-worker -n 10 --no-pager | grep -i "ready\|tasks"

echo ""
echo "=========================================="
echo "✅ Celery Worker Status"
echo "=========================================="
systemctl status llmready-celery-worker --no-pager -l

echo ""
echo "=========================================="
echo "📝 Next Steps"
echo "=========================================="
echo "1. Try creating a generation from the frontend"
echo "2. Watch logs in real-time: sudo journalctl -u llmready-celery-worker -f"
echo "3. You should see: 'Task app.tasks.generation.generate_llm_content[...]'"
echo "=========================================="
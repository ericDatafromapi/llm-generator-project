#!/bin/bash
# Check Celery Worker Service Status

echo "=================================================="
echo "🔍 Checking Celery Worker Service"
echo "=================================================="
echo ""

# Check if service exists
echo "1. Checking if llmready-celery-worker service exists..."
if systemctl list-unit-files | grep -q "llmready-celery-worker"; then
    echo "✅ Service file exists"
else
    echo "❌ Service file NOT found"
    echo "   Run: sudo cp scripts/llmready-celery-worker.service /etc/systemd/system/"
    echo "   Run: sudo systemctl daemon-reload"
    exit 1
fi

echo ""
echo "2. Checking service status..."
sudo systemctl status llmready-celery-worker --no-pager -l

echo ""
echo "3. Checking if service is enabled..."
if systemctl is-enabled llmready-celery-worker >/dev/null 2>&1; then
    echo "✅ Service is enabled (starts on boot)"
else
    echo "⚠️  Service is NOT enabled"
    echo "   Run: sudo systemctl enable llmready-celery-worker"
fi

echo ""
echo "4. Checking if service is running..."
if systemctl is-active llmready-celery-worker >/dev/null 2>&1; then
    echo "✅ Service is RUNNING"
else
    echo "❌ Service is NOT RUNNING"
    echo "   Run: sudo systemctl start llmready-celery-worker"
fi

echo ""
echo "5. Checking recent logs..."
echo "Last 20 lines:"
sudo journalctl -u llmready-celery-worker -n 20 --no-pager

echo ""
echo "=================================================="
echo "📊 Summary"
echo "=================================================="
systemctl is-active llmready-celery-worker >/dev/null 2>&1 && echo "✅ Celery worker is ACTIVE" || echo "❌ Celery worker is INACTIVE"
systemctl is-enabled llmready-celery-worker >/dev/null 2>&1 && echo "✅ Auto-start on boot: YES" || echo "⚠️  Auto-start on boot: NO"

echo ""
echo "Quick commands:"
echo "  Start:   sudo systemctl start llmready-celery-worker"
echo "  Stop:    sudo systemctl stop llmready-celery-worker"
echo "  Restart: sudo systemctl restart llmready-celery-worker"
echo "  Logs:    sudo journalctl -u llmready-celery-worker -f"
echo "=================================================="
#!/bin/bash
# FINAL FIX - Add queue configuration to worker service

echo "=========================================="
echo "🔧 ADDING QUEUE CONFIGURATION"
echo "=========================================="
echo ""

# Create the corrected service file
cat > /tmp/llmready-celery-worker.service << 'EOF'
[Unit]
Description=LLMReady Celery Worker
After=network.target llmready-backend.service
Requires=llmready-backend.service

[Service]
Type=simple
User=root
Group=root
WorkingDirectory=/opt/llmready/backend
Environment="PATH=/opt/llmready/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"

# Load environment variables from backend .env
EnvironmentFile=/opt/llmready/backend/.env

# Start Celery worker - LISTEN TO GENERATION AND SCHEDULED QUEUES
ExecStart=/opt/llmready/venv/bin/celery -A app.core.celery_app worker \
    --loglevel=info \
    --concurrency=2 \
    --max-tasks-per-child=1000 \
    -Q generation,scheduled

# Restart on failure
Restart=always
RestartSec=10s

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=celery-worker

[Install]
WantedBy=multi-user.target
EOF

echo "✅ Created corrected service file"
echo ""

# Install it
echo "Installing service file..."
sudo cp /tmp/llmready-celery-worker.service /etc/systemd/system/
sudo systemctl daemon-reload
echo "✅ Service file installed"
echo ""

# Restart worker
echo "Restarting Celery worker..."
sudo systemctl restart llmready-celery-worker
sleep 3
echo "✅ Worker restarted"
echo ""

# Verify queues
echo "=========================================="
echo "📊 VERIFICATION"
echo "=========================================="
echo ""
echo "Worker should now be listening to generation queue:"
echo ""
sudo journalctl -u llmready-celery-worker -n 30 --no-pager | grep -A 5 "queues"

echo ""
echo "=========================================="
echo "✅ DONE! Now try generating from frontend"
echo "=========================================="
#!/bin/bash
# FIX THE QUEUE ISSUE - Worker not listening to generation queue

echo "=========================================="
echo "🔧 FIXING CELERY QUEUE CONFIGURATION"
echo "=========================================="
echo ""
echo "Problem found: Worker is not listening to 'generation' queue"
echo "Your debug showed: 2 tasks stuck in generation queue!"
echo ""

cd /opt/llmready

# 1. Update service file
echo "Step 1: Updating service file..."
sudo cp scripts/llmready-celery-worker.service /etc/systemd/system/
echo "✅ Service file updated"

# 2. Reload systemd
echo ""
echo "Step 2: Reloading systemd..."
sudo systemctl daemon-reload
echo "✅ Systemd reloaded"

# 3. Restart worker
echo ""
echo "Step 3: Restarting Celery worker..."
sudo systemctl restart llmready-celery-worker
sleep 3
echo "✅ Worker restarted"

# 4. Verify worker is listening to correct queues
echo ""
echo "Step 4: Verifying queue configuration..."
echo ""
sudo journalctl -u llmready-celery-worker -n 50 --no-pager | grep -A 10 "queues"

echo ""
echo "=========================================="
echo "✅ FIX COMPLETE"
echo "=========================================="
echo ""
echo "The worker should now be listening to:"
echo "  - generation queue"
echo "  - scheduled queue"
echo ""
echo "Your 2 stuck tasks should start processing now!"
echo ""
echo "Watch them process:"
echo "  sudo journalctl -u llmready-celery-worker -f"
echo ""
echo "You should see:"
echo "  [INFO] Task app.tasks.generation.generate_llm_content[...] received"
echo "  [INFO] Generation <ID> started"
echo "=========================================="
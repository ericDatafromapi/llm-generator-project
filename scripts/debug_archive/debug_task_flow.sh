#!/bin/bash
# DEBUG: See EXACTLY what happens when generation is triggered

echo "=========================================="
echo "🔍 REAL-TIME TASK FLOW DEBUGGER"
echo "=========================================="
echo ""
echo "This will show you EXACTLY where the problem is."
echo ""

cd /opt/llmready/backend

echo "1️⃣ Checking Celery worker configuration..."
echo ""

# Check what queues the worker is listening to
echo "Worker queues (from service file):"
grep "queues=" /etc/systemd/system/llmready-celery-worker.service || echo "No queue config found"

echo ""
echo "2️⃣ Checking Redis connection..."
echo ""

# Test Redis from Python (same way Celery does)
python3 << 'PYTHON_EOF'
import sys
sys.path.insert(0, '/opt/llmready/backend')

from app.core.config import settings
import redis

print(f"REDIS_URL from settings: {settings.REDIS_URL}")

try:
    r = redis.from_url(settings.REDIS_URL)
    r.ping()
    print("✅ Redis connection: SUCCESS")
    
    # Check queue lengths
    celery_len = r.llen('celery')
    generation_len = r.llen('generation')
    print(f"   Celery queue: {celery_len} tasks")
    print(f"   Generation queue: {generation_len} tasks")
    
except Exception as e:
    print(f"❌ Redis connection: FAILED - {e}")
    sys.exit(1)
PYTHON_EOF

echo ""
echo "3️⃣ Checking if worker can import tasks..."
echo ""

python3 << 'PYTHON_EOF'
import sys
sys.path.insert(0, '/opt/llmready/backend')

try:
    from app.core.celery_app import celery_app
    from app.tasks.generation import generate_llm_content
    
    print("✅ Task import: SUCCESS")
    print(f"   Task name: {generate_llm_content.name}")
    print(f"   Task registered: {'app.tasks.generation.generate_llm_content' in celery_app.tasks}")
    
    # Check task configuration
    task = celery_app.tasks.get('app.tasks.generation.generate_llm_content')
    if task:
        print(f"   Task queue: {task.queue if hasattr(task, 'queue') else 'default'}")
    
except Exception as e:
    print(f"❌ Task import: FAILED - {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
PYTHON_EOF

echo ""
echo "4️⃣ Testing task queuing (simulated)..."
echo ""

python3 << 'PYTHON_EOF'
import sys
sys.path.insert(0, '/opt/llmready/backend')

from app.core.celery_app import celery_app
from app.tasks.generation import generate_llm_content
import uuid

# Create a fake UUID for testing
test_id = str(uuid.uuid4())
print(f"Queueing test task with ID: {test_id}")

try:
    # Try to queue the task (don't actually execute, just queue)
    result = generate_llm_content.apply_async(args=[test_id])
    
    print(f"✅ Task queued successfully!")
    print(f"   Task ID: {result.id}")
    print(f"   Task state: {result.state}")
    
    # Check if it appeared in Redis
    import redis
    from app.core.config import settings
    r = redis.from_url(settings.REDIS_URL)
    
    celery_len = r.llen('celery')
    generation_len = r.llen('generation')
    print(f"   After queueing:")
    print(f"     Celery queue: {celery_len} tasks")
    print(f"     Generation queue: {generation_len} tasks")
    
    # Try to revoke the test task
    result.revoke(terminate=True)
    print(f"   Test task revoked (cleanup)")
    
except Exception as e:
    print(f"❌ Task queueing: FAILED - {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
PYTHON_EOF

echo ""
echo "5️⃣ Checking worker logs for errors..."
echo ""
echo "Last 20 lines of worker logs:"
sudo journalctl -u llmready-celery-worker -n 20 --no-pager

echo ""
echo "=========================================="
echo "🎯 DIAGNOSIS COMPLETE"
echo "=========================================="
echo ""
echo "Now watch both logs in real-time:"
echo "  Terminal 1: sudo journalctl -u llmready-backend -f"
echo "  Terminal 2: sudo journalctl -u llmready-celery-worker -f"
echo ""
echo "Then create a generation from the frontend."
echo "You should see:"
echo "  - Backend: POST /api/v1/generations/start"
echo "  - Worker: Task app.tasks.generation.generate_llm_content received"
echo ""
echo "If you DON'T see the worker receiving the task,"
echo "there's a queue/routing problem."
echo "=========================================="
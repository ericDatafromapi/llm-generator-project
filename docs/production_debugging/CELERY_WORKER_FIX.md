# Celery Worker Service Fix

## 🔴 Problem Identified

Your test shows:
- ✅ Tasks ARE registered in code (4 tasks found)
- ✅ Docker works, crawler works
- ❌ **Celery worker SERVICE is not running**

The CELERY: FAIL in the test is because:
1. `redis-cli` command not found (just a monitoring tool, not critical)
2. **The Celery worker service itself is probably not started**

---

## 🔍 Diagnostic Steps

Run this to check the Celery worker service:

```bash
cd /opt/llmready
chmod +x scripts/check_celery_service.sh
./scripts/check_celery_service.sh
```

This will show you:
- ✅ or ❌ If service exists
- ✅ or ❌ If service is running
- ✅ or ❌ If service is enabled (auto-start)
- Recent logs

---

## 🛠️ Fix: Start Celery Worker

### If Service is Not Running:

```bash
# Start the service
sudo systemctl start llmready-celery-worker

# Enable auto-start on boot
sudo systemctl enable llmready-celery-worker

# Verify it's running
sudo systemctl status llmready-celery-worker
```

### If Service Doesn't Exist:

```bash
# Install the service
sudo cp /opt/llmready/scripts/llmready-celery-worker.service /etc/systemd/system/
sudo systemctl daemon-reload

# Start and enable
sudo systemctl start llmready-celery-worker
sudo systemctl enable llmready-celery-worker

# Verify
sudo systemctl status llmready-celery-worker
```

### Check Logs:

```bash
# View logs
sudo journalctl -u llmready-celery-worker -n 50

# Follow logs in real-time
sudo journalctl -u llmready-celery-worker -f
```

---

## ✅ Verification

After starting the service, verify it's working:

### 1. Check Service Status
```bash
sudo systemctl status llmready-celery-worker
# Should show: Active: active (running)
```

### 2. Check Worker Logs
```bash
sudo journalctl -u llmready-celery-worker -n 20
# Should show: "celery@hostname ready"
# Should show: "Registered tasks: [...]"
```

### 3. Test with Real Generation
```bash
# Create a website and generation via UI or API
# Then watch it process:
sudo journalctl -u llmready-celery-worker -f
```

### 4. Check Redis Queue
```bash
# If you want, install redis-cli:
sudo apt-get install redis-tools

# Then check queues:
redis-cli LLEN celery
redis-cli LLEN generation
```

---

## 🎯 Expected Output After Fix

When you run the generation test again:

```bash
python3 scripts/test_generation_workflow.py
```

You should see:
```
=== Testing Celery/Redis Connectivity ===
SUCCESS: Registered Celery tasks: 4
INFO:   - app.tasks.generation.generate_llm_content
INFO:   - app.tasks.scheduled.cleanup_old_generations
INFO:   - app.tasks.scheduled.reset_monthly_quotas
INFO:   - app.tasks.scheduled.sync_stripe_subscriptions
SUCCESS: Redis is responding
INFO: Celery queue length: 0
INFO: Generation queue length: 0

CELERY: ✅ PASS
```

---

## 🚨 Common Issues

### Issue: Service Fails to Start

**Check logs:**
```bash
sudo journalctl -u llmready-celery-worker -n 50
```

**Common causes:**
1. **Wrong working directory** - Check service file has correct path
2. **Missing environment variables** - Check .env file exists
3. **Python/venv issues** - Check virtual environment path is correct
4. **Port conflicts** - Check nothing else is using Redis port

**Fix:**
```bash
# Verify .env file exists
ls -la /opt/llmready/backend/.env

# Verify venv exists
ls -la /opt/llmready/venv/bin/celery

# Check service file
cat /etc/systemd/system/llmready-celery-worker.service

# Restart after fixing
sudo systemctl daemon-reload
sudo systemctl restart llmready-celery-worker
```

### Issue: Service Starts but Crashes

**View detailed logs:**
```bash
sudo journalctl -u llmready-celery-worker -n 100 --no-pager
```

**Look for:**
- Import errors
- Connection errors
- Permission errors

### Issue: Tasks Not Processing

**Check if worker is idle:**
```bash
# View worker status
sudo journalctl -u llmready-celery-worker -f

# Submit a test job via UI
# Should see: "Task app.tasks.generation.generate_llm_content[...]"
```

---

## 📋 Complete Service Setup Checklist

- [ ] Service file exists: `/etc/systemd/system/llmready-celery-worker.service`
- [ ] Service is started: `systemctl is-active llmready-celery-worker` returns "active"
- [ ] Service is enabled: `systemctl is-enabled llmready-celery-worker` returns "enabled"
- [ ] Logs show worker ready: `journalctl -u llmready-celery-worker -n 20`
- [ ] 4 tasks registered: Visible in logs
- [ ] Redis accessible: Test with `docker exec -it $(docker ps -qf "name=redis") redis-cli ping`
- [ ] Can process jobs: Submit test generation and watch logs

---

## 🔧 Quick Commands Reference

```bash
# Check status
sudo systemctl status llmready-celery-worker

# Start
sudo systemctl start llmready-celery-worker

# Stop
sudo systemctl stop llmready-celery-worker

# Restart (after code changes)
sudo systemctl restart llmready-celery-worker

# View logs
sudo journalctl -u llmready-celery-worker -f

# Check what's in queue
docker exec -it $(docker ps -qf "name=redis") redis-cli LLEN generation
```

---

**Last Updated:** 2025-10-16
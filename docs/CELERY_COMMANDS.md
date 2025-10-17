# Development Server Commands Reference

Quick reference for running all LLMReady development and production servers.

## Table of Contents
- [Backend (FastAPI/Uvicorn)](#backend-fastapi-uvicorn)
- [Frontend (React/Vite)](#frontend-react-vite)
- [Celery Workers](#celery-workers)
- [Production Services](#production-services)

---

## Backend (FastAPI/Uvicorn)

### Local Development
```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Production Mode
```bash
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### With Custom Workers
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Alternative: Using Python directly
```bash
cd backend
python -m app.main
```

---

## Frontend (React/Vite)

### Development Server
```bash
cd frontend
npm run dev
```
*Default: http://localhost:5173*

### Production Build
```bash
cd frontend
npm run build
```

### Preview Production Build
```bash
cd frontend
npm run preview
```

### Install Dependencies
```bash
cd frontend
npm install
```

---

## Celery Workers

## Local Development

### Celery Worker (Task Processor)
Simple version for local testing:
```bash
celery -A app.core.celery_app worker --loglevel=info --purge
```

Production-ready version with queues:
```bash
celery -A app.core.celery_app worker \
    --loglevel=info \
    --concurrency=2 \
    --max-tasks-per-child=1000 \
    -Q generation,scheduled
```

### Celery Beat (Task Scheduler)
```bash
celery -A app.core.celery_app beat --loglevel=info
```

## Running Both Processes

You need to run both in separate terminals:

```bash
# Terminal 1 - Worker
cd backend
celery -A app.core.celery_app worker \
    --loglevel=info \
    --concurrency=2 \
    --max-tasks-per-child=1000 \
    -Q generation,scheduled

# Terminal 2 - Beat
cd backend
celery -A app.core.celery_app beat --loglevel=info
```

## Production (Systemd Services)

On the production server, Celery runs as systemd services:

### Check Status
```bash
sudo systemctl status llmready-celery-worker
sudo systemctl status llmready-celery-beat
```

### Restart Services
```bash
sudo systemctl restart llmready-celery-worker
sudo systemctl restart llmready-celery-beat
```

### View Logs
```bash
# Worker logs
sudo journalctl -u llmready-celery-worker -f

# Beat logs
sudo journalctl -u llmready-celery-beat -f
```

## Command Parameters Explained

- `--loglevel=info`: Show informational logs
- `--concurrency=2`: Run 2 worker processes in parallel
- `--max-tasks-per-child=1000`: Restart worker after 1000 tasks (prevents memory leaks)
- `-Q generation,scheduled`: Listen to specific queues
- `--purge`: Clear all pending tasks on startup (useful for development)
- `--pidfile=/tmp/celerybeat.pid`: Store process ID for beat scheduler

## What Each Service Does

### Celery Worker
- Processes background tasks
- Handles website generation tasks
- Processes scheduled tasks (subscriptions, trials, etc.)

### Celery Beat
- Schedules periodic tasks
- Triggers subscription checks
- Manages trial expirations
- Runs maintenance tasks

## Troubleshooting

### Worker not picking up tasks
```bash
# Check if worker is running and listening to correct queues
celery -A app.core.celery_app inspect active_queues
```

### Clear all pending tasks
```bash
celery -A app.core.celery_app purge
```

### Check registered tasks
```bash
celery -A app.core.celery_app inspect registered
```

---

## Production Services

All services run as systemd services on the production server.

### Backend API Service

**Check Status:**
```bash
sudo systemctl status llmready-backend
```

**Restart:**
```bash
sudo systemctl restart llmready-backend
```

**View Logs:**
```bash
sudo journalctl -u llmready-backend -f
```

**Service Location:**
- Configuration: `/etc/systemd/system/llmready-backend.service`
- Command: `uvicorn app.main:app --host 0.0.0.0 --port 8000`

### All Services at Once

**Check all services:**
```bash
sudo systemctl status llmready-backend llmready-celery-worker llmready-celery-beat
```

**Restart all services:**
```bash
sudo systemctl restart llmready-backend llmready-celery-worker llmready-celery-beat
```

---

## Complete Development Setup

To run the entire application locally, you need 4 terminals:

```bash
# Terminal 1 - Backend API
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2 - Celery Worker
cd backend
celery -A app.core.celery_app worker \
    --loglevel=info \
    --concurrency=2 \
    --max-tasks-per-child=1000 \
    -Q generation,scheduled

# Terminal 3 - Celery Beat
cd backend
celery -A app.core.celery_app beat --loglevel=info

# Terminal 4 - Frontend
cd frontend
npm run dev
```

**Access:**
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/api/docs
- Health Check: http://localhost:8000/health

---

## Quick Commands Cheatsheet

| Service | Command |
|---------|---------|
| **Backend Dev** | `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000` |
| **Backend Prod** | `uvicorn app.main:app --host 0.0.0.0 --port 8000` |
| **Celery Worker** | `celery -A app.core.celery_app worker --loglevel=info --concurrency=2 --max-tasks-per-child=1000 -Q generation,scheduled` |
| **Celery Beat** | `celery -A app.core.celery_app beat --loglevel=info` |
| **Frontend Dev** | `npm run dev` |
| **Frontend Build** | `npm run build` |
| **Frontend Preview** | `npm run preview` |

---

## Related Files

### Backend
- Main application: [`backend/app/main.py`](../backend/app/main.py)
- Celery config: [`backend/app/core/celery_app.py`](../backend/app/core/celery_app.py)
- Backend service: [`scripts/llmready-backend.service`](../scripts/llmready-backend.service)

### Frontend
- Package config: [`frontend/package.json`](../frontend/package.json)
- Vite config: [`frontend/vite.config.ts`](../frontend/vite.config.ts)

### Celery Services
- Worker service: [`scripts/llmready-celery-worker.service`](../scripts/llmready-celery-worker.service)
- Beat service: [`scripts/llmready-celery-beat.service`](../scripts/llmready-celery-beat.service)
- Setup script: [`scripts/setup-celery-services.sh`](../scripts/setup-celery-services.sh)
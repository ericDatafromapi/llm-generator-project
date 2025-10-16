# 🔧 Backend Service Setup on Server

Your backend doesn't run in Docker - it runs directly with uvicorn. This guide shows you how to set it up on your production server.

## 🎯 Quick Setup

SSH to your server and run these commands:

```bash
# SSH to server
ssh llmready@your-server-ip

# Navigate to deployment directory
cd /opt/llmready

# Create Python virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install backend dependencies
cd backend
pip install -r requirements.txt

# Create systemd service file
sudo nano /etc/systemd/system/llmready-backend.service
```

Paste this content:

```ini
[Unit]
Description=LLMReady FastAPI Backend
After=network.target docker.service
Requires=docker.service

[Service]
Type=simple
User=llmready
WorkingDirectory=/opt/llmready/backend
Environment="PATH=/opt/llmready/venv/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=/opt/llmready/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Save and exit (`Ctrl+X`, `Y`, `Enter`)

Then:

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable service (start on boot)
sudo systemctl enable llmready-backend

# Start service
sudo systemctl start llmready-backend

# Check status
sudo systemctl status llmready-backend
```

## ✅ Verification

```bash
# Check if backend is running
curl http://localhost:8000/health

# View logs
sudo journalctl -u llmready-backend -f
```

## 🔄 After Setup

Now deployments will work! The CI/CD pipeline will:
1. Start Docker services (postgres & redis)
2. Run database migrations
3. Restart your backend service automatically

## 🚀 Manual Control

```bash
# Start backend
sudo systemctl start llmready-backend

# Stop backend
sudo systemctl stop llmready-backend

# Restart backend
sudo systemctl restart llmready-backend

# View logs
sudo journalctl -u llmready-backend -f

# Check status
sudo systemctl status llmready-backend
```

---

## 📝 Alternative: Manual Run (Not Recommended for Production)

If you don't want to use systemd, you can run manually:

```bash
cd /opt/llmready/backend
source ../venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

But this won't auto-restart and won't start on server reboot.

---

## 🎯 Complete Server Setup Checklist

On your production server, you need:

- [x] Nginx (serves frontend, proxies backend)
- [x] Docker & Docker Compose (runs postgres & redis)
- [ ] **Backend systemd service** ← You need to set this up!
- [x] Deployment directories (/opt/llmready, /var/www/llmready)
- [x] SSH access for GitHub Actions

Once you set up the backend service, your CI/CD will work perfectly! 🎉
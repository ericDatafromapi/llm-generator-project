#!/bin/bash
# Setup automated hourly database backups

echo "=========================================="
echo "🗄️  Setting Up Database Backups"
echo "=========================================="
echo ""

cd /opt/llmready

echo "1️⃣ Installing required Python packages..."
pip install google-cloud-storage
echo "✅ Packages installed"

echo ""
echo "2️⃣ Creating backup directories..."
mkdir -p /opt/llmready/backups/database
mkdir -p /var/log
touch /var/log/llmready-backup.log
chmod 644 /var/log/llmready-backup.log
echo "✅ Directories created"

echo ""
echo "3️⃣ Creating systemd service for backups..."

# Create systemd service
cat > /tmp/llmready-backup.service << 'EOF'
[Unit]
Description=LLMReady Database Backup
After=network.target

[Service]
Type=oneshot
User=root
WorkingDirectory=/opt/llmready
Environment="PATH=/opt/llmready/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
EnvironmentFile=/opt/llmready/backend/.env
ExecStart=/opt/llmready/venv/bin/python3 /opt/llmready/scripts/backup_database.py

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=llmready-backup
EOF

sudo cp /tmp/llmready-backup.service /etc/systemd/system/
echo "✅ Service created"

echo ""
echo "4️⃣ Creating systemd timer for hourly backups..."

# Create systemd timer
cat > /tmp/llmready-backup.timer << 'EOF'
[Unit]
Description=LLMReady Database Backup Timer (Hourly)
Requires=llmready-backup.service

[Timer]
# Run every hour
OnCalendar=hourly
# Run 5 minutes after each hour
OnCalendar=*:05:00
Persistent=true

[Install]
WantedBy=timers.target
EOF

sudo cp /tmp/llmready-backup.timer /etc/systemd/system/
echo "✅ Timer created"

echo ""
echo "5️⃣ Enabling backup timer..."
sudo systemctl daemon-reload
sudo systemctl enable llmready-backup.timer
sudo systemctl start llmready-backup.timer
echo "✅ Timer enabled and started"

echo ""
echo "=========================================="
echo "📊 Backup System Status"
echo "=========================================="
sudo systemctl status llmready-backup.timer --no-pager

echo ""
echo "=========================================="
echo "📝 Next Steps"
echo "=========================================="
echo ""
echo "REQUIRED: Configure Google Cloud Storage"
echo ""
echo "1. Create a GCS bucket:"
echo "   - Go to: https://console.cloud.google.com/storage"
echo "   - Create bucket (e.g., llmready-database-backups)"
echo "   - Choose region close to your server"
echo ""
echo "2. Create service account:"
echo "   - Go to: https://console.cloud.google.com/iam-admin/serviceaccounts"
echo "   - Create service account (e.g., llmready-backup)"
echo "   - Grant 'Storage Object Creator' role"
echo "   - Create JSON key and download"
echo ""
echo "3. Upload credentials to server:"
echo "   scp gcs-key.json user@your-server:/opt/llmready/gcs-credentials.json"
echo ""
echo "4. Add to /opt/llmready/backend/.env:"
echo "   GCS_BACKUP_BUCKET=your-bucket-name"
echo "   GCS_CREDENTIALS_PATH=/opt/llmready/gcs-credentials.json"
echo ""
echo "5. Test the backup:"
echo "   sudo systemctl start llmready-backup.service"
echo "   sudo journalctl -u llmready-backup.service -n 50"
echo ""
echo "=========================================="
echo "⏰ Backup Schedule"
echo "=========================================="
echo "Backups will run: Every hour at :05 (e.g., 14:05, 15:05, etc.)"
echo "Local retention: 7 days"
echo "GCS retention: 30 days"
echo ""
echo "View next backup time:"
echo "  sudo systemctl list-timers llmready-backup.timer"
echo "=========================================="
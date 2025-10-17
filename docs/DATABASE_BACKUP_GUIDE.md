# Database Backup & Recovery Guide

**Purpose:** Automated hourly backups with dual storage (local + Google Cloud Storage)

---

## 🗄️ Backup System Overview

### What Gets Backed Up
- Complete PostgreSQL database (`llmready_prod`)
- All tables: users, subscriptions, generations, websites, etc.
- Format: PostgreSQL custom format (compressed, restorable)

### Backup Locations
1. **Local:** `/opt/llmready/backups/database/` (7 days retention)
2. **Google Cloud Storage:** Bucket (30 days retention)

### Backup Schedule
- **Frequency:** Every hour at :05 (14:05, 15:05, 16:05, etc.)
- **Method:** Systemd timer (runs even after server restart)

---

## 📦 Setup Instructions

### Step 1: Setup Google Cloud Storage (5 minutes)

#### A. Create GCS Bucket

1. Go to: https://console.cloud.google.com/storage
2. Click "CREATE BUCKET"
3. Bucket name: `llmready-database-backups` (must be globally unique)
4. Choose location: Same region as your server for faster transfers
5. Storage class: Standard
6. Click "CREATE"

#### B. Create Service Account

1. Go to: https://console.cloud.google.com/iam-admin/serviceaccounts
2. Click "CREATE SERVICE ACCOUNT"
3. Name: `llmready-backup`
4. Click "CREATE AND CONTINUE"
5. Grant role: **Storage Object Creator**
6. Click "DONE"

#### C. Create and Download Key

1. Click on the service account you just created
2. Go to "KEYS" tab
3. Click "ADD KEY" → "Create new key"
4. Choose "JSON"
5. Download the JSON file (e.g., `llmready-backup-key.json`)

#### D. Upload Credentials to Server

```bash
# From your local machine:
scp llmready-backup-key.json user@your-server:/opt/llmready/gcs-credentials.json

# Set proper permissions
ssh user@your-server "chmod 600 /opt/llmready/gcs-credentials.json"
```

### Step 2: Configure Environment Variables

```bash
# SSH to production server
ssh user@your-server

# Edit .env file
nano /opt/llmready/backend/.env

# Add these lines:
GCS_BACKUP_BUCKET=llmready-database-backups
GCS_CREDENTIALS_PATH=/opt/llmready/gcs-credentials.json

# Save and exit (Ctrl+X, Y, Enter)
```

### Step 3: Run Setup Script

```bash
cd /opt/llmready
chmod +x scripts/setup_backups.sh
sudo ./scripts/setup_backups.sh
```

This will:
- ✅ Install required Python packages
- ✅ Create backup directories
- ✅ Create systemd service and timer
- ✅ Start hourly backups

### Step 4: Test Manual Backup

```bash
# Run a manual backup to test
sudo systemctl start llmready-backup.service

# Check if it worked
sudo journalctl -u llmready-backup.service -n 50

# Check local backup created
ls -lh /opt/llmready/backups/database/

# Check GCS (if configured)
# Go to: https://console.cloud.google.com/storage/browser/llmready-database-backups
```

---

## 🔄 Using the Backup System

### Check Backup Status

```bash
# Check when next backup will run
sudo systemctl list-timers llmready-backup.timer

# View recent backup logs
sudo journalctl -u llmready-backup.service -n 100

# List local backups
ls -lh /opt/llmready/backups/database/
```

### Manual Backup

```bash
# Trigger backup immediately
sudo systemctl start llmready-backup.service

# Watch it run
sudo journalctl -u llmready-backup.service -f
```

### Stop/Start Backups

```bash
# Stop hourly backups
sudo systemctl stop llmready-backup.timer

# Start hourly backups
sudo systemctl start llmready-backup.timer

# Disable (won't run after reboot)
sudo systemctl disable llmready-backup.timer

# Enable (runs after reboot)
sudo systemctl enable llmready-backup.timer
```

---

## 🔄 Restore Database

### List Available Backups

```bash
cd /opt/llmready
python3 scripts/restore_database.py --list
```

Shows all local and GCS backups.

### Restore from Local Backup (Interactive)

```bash
# Interactive selection
python3 scripts/restore_database.py --source local

# Will show list and ask you to choose
# Then confirms before restoring
```

### Restore from GCS Backup (Interactive)

```bash
# Interactive selection from cloud
python3 scripts/restore_database.py --source gcs

# Downloads and restores
```

### Restore Specific File

```bash
# Restore specific local backup
python3 scripts/restore_database.py --source local --file llmready_llmready_prod_20251017_140500.sql.gz

# Restore specific GCS backup
python3 scripts/restore_database.py --source gcs --file llmready_llmready_prod_20251017_140500.sql.gz
```

---

## 📊 Backup File Naming

Format: `llmready_<database>_<YYYYMMDD>_<HHMMSS>.sql.gz`

Example: `llmready_llmready_prod_20251017_140500.sql.gz`
- Database: llmready_prod
- Date: 2025-10-17
- Time: 14:05:00

---

## 🚨 Disaster Recovery Procedure

### If Database is Lost/Corrupted

1. **Stop the backend:**
   ```bash
   sudo systemctl stop llmready-backend
   ```

2. **List and choose backup:**
   ```bash
   python3 scripts/restore_database.py --list
   ```

3. **Restore:**
   ```bash
   python3 scripts/restore_database.py --source gcs
   # Or for local: --source local
   ```

4. **Verify restoration:**
   ```bash
   docker exec -i $(docker ps -qf "name=postgres") psql -U postgres -d llmready_prod -c "SELECT COUNT(*) FROM users;"
   ```

5. **Start backend:**
   ```bash
   sudo systemctl start llmready-backend
   ```

---

## 💾 Backup Storage Costs

### Google Cloud Storage Pricing (approximate)

- **Standard Storage:** ~$0.020 per GB/month
- **Network Egress:** ~$0.12 per GB (downloads)

**Example:** 100 MB database
- Storage (30 backups): ~3 GB = ~$0.06/month
- Downloads (rare): ~$0.01 per restore

**Very affordable for production database safety!**

---

## 🔍 Monitoring

### Check Backup Health

```bash
# Last 5 backup runs
sudo journalctl -u llmready-backup.service -n 200 | grep "Backup Summary" -A 5

# Failed backups
sudo journalctl -u llmready-backup.service --since "7 days ago" | grep ERROR

# Check disk space
df -h /opt/llmready/backups/
```

### Verify Backups Are Running

```bash
# Check timer is active
systemctl is-active llmready-backup.timer

# When is next backup?
systemctl list-timers llmready-backup.timer

# Recent backups
ls -lht /opt/llmready/backups/database/ | head -10
```

---

## 📝 Troubleshooting

### Backup Fails - GCS Errors

**Issue:** "Could not authenticate with GCS"

**Fix:**
```bash
# Check credentials file exists
ls -l /opt/llmready/gcs-credentials.json

# Check .env has correct bucket name
grep GCS_BACKUP_BUCKET /opt/llmready/backend/.env

# Test credentials manually
python3 -c "from google.cloud import storage; from google.oauth2 import service_account; creds = service_account.Credentials.from_service_account_file('/opt/llmready/gcs-credentials.json'); print('✅ Credentials valid')"
```

### Backup Fails - Database Errors

**Issue:** "pg_dump failed"

**Fix:**
```bash
# Check database is running
docker ps | grep postgres

# Test pg_dump manually
docker exec -i $(docker ps -qf "name=postgres") pg_dump -U postgres -d llmready_prod > /tmp/test.sql
```

### Restore Fails

**Issue:** "pg_restore failed"

**Check:**
- Is backup file corrupted? Check file size
- Is database running?
- Do you have enough disk space?

---

## 🎯 Best Practices

1. **Test restores regularly** (monthly) to ensure backups work
2. **Monitor backup logs** for failures
3. **Keep GCS credentials secure** (chmod 600)
4. **Don't delete GCS bucket** without ensuring local backups exist
5. **Before major changes**, take a manual backup:
   ```bash
   sudo systemctl start llmready-backup.service
   ```

---

## 📁 Files Created

- **[`scripts/backup_database.py`](../scripts/backup_database.py)** - Backup script
- **[`scripts/restore_database.py`](../scripts/restore_database.py)** - Restore script  
- **[`scripts/setup_backups.sh`](../scripts/setup_backups.sh)** - Setup script
- **`/etc/systemd/system/llmready-backup.service`** - Backup service
- **`/etc/systemd/system/llmready-backup.timer`** - Hourly timer

---

## 🎉 Summary

**Backup Protection:**
- ✅ Hourly automated backups
- ✅ Local storage (7 days)
- ✅ Cloud storage (30 days)
- ✅ Easy restoration
- ✅ Monitored and logged

**Your production database is now safe!** 🛡️

---

**Last Updated:** 2025-10-17
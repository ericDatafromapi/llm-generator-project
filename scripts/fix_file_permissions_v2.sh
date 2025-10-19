#!/bin/bash
# Fix file permissions for storage directory - Run with sudo

if [ "$EUID" -ne 0 ]; then 
    echo "Please run as root: sudo ./fix_file_permissions_v2.sh"
    exit 1
fi

echo "=========================================="
echo "🔧 Fixing File Storage Permissions"
echo "=========================================="
echo ""

cd /opt/llmready

# Create storage directory structure
echo "Creating storage directories..."
mkdir -p storage/files
echo "✅ Directories created"

# Set ownership to llmready user (backend runs as this user)
echo ""
echo "Setting ownership to llmready user..."
chown -R llmready:llmready storage/
chmod -R 755 storage/
chmod -R 775 storage/files/

echo "✅ Ownership set"

echo ""
echo "Permissions now:"
ls -la storage/

echo ""
echo "=========================================="
echo "✅ Permissions Fixed"
echo "=========================================="
echo ""
echo "Also updating Celery worker to run as llmready (not root)..."

# Update celery worker service to run as llmready
sed -i 's/^User=root$/User=llmready/' /etc/systemd/system/llmready-celery-worker.service
sed -i 's/^Group=root$/Group=llmready/' /etc/systemd/system/llmready-celery-worker.service

systemctl daemon-reload
systemctl restart llmready-celery-worker

echo "✅ Celery worker now runs as llmready user"
echo ""
echo "Verification:"
systemctl show -p User llmready-backend
systemctl show -p User llmready-celery-worker
echo "=========================================="
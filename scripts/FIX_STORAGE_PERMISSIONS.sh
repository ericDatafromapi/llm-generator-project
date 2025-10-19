#!/bin/bash
# Fix storage permissions for Celery worker

if [ "$EUID" -ne 0 ]; then 
    echo "Run as root: sudo ./FIX_STORAGE_PERMISSIONS.sh"
    exit 1
fi

echo "=========================================="
echo "🔧 FIXING STORAGE PERMISSIONS FOR CELERY"
echo "=========================================="
echo ""

cd /opt/llmready

echo "Current storage state:"
ls -la backend/storage/ 2>/dev/null || echo "Doesn't exist"

echo ""
echo "Creating and fixing storage directory..."
mkdir -p backend/storage/files
chown -R llmready:llmready backend/storage/
chmod -R 775 backend/storage/

echo ""
echo "Verifying permissions:"
ls -la backend/storage/
ls -la backend/storage/files/ | head -5

echo ""
echo "Restarting services..."
systemctl restart llmready-celery-worker
systemctl restart llmready-backend

echo ""
echo "=========================================="
echo "✅ STORAGE FIXED"
echo "=========================================="
echo "Permissions:"
stat -c '%A %U:%G' backend/storage/files/

echo ""
echo "Try generating a file now - should work!"
echo "=========================================="
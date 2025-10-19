#!/bin/bash
# Fix file permissions for storage directory

echo "=========================================="
echo "🔧 Fixing File Storage Permissions"
echo "=========================================="
echo ""

cd /opt/llmready

# Get the user running the backend service
BACKEND_USER=$(systemctl show -p User llmready-backend | cut -d= -f2)

echo "Backend service runs as: $BACKEND_USER"
echo ""

# Check current storage permissions
echo "Current permissions:"
ls -la storage/ 2>/dev/null || echo "storage/ doesn't exist"

echo ""
echo "Fixing permissions..."

# Create storage directory if doesn't exist
mkdir -p storage/files

# Option 1: If backend runs as specific user
if [ "$BACKEND_USER" != "root" ] && [ -n "$BACKEND_USER" ]; then
    echo "Setting owner to: $BACKEND_USER"
    chown -R $BACKEND_USER:$BACKEND_USER storage/
    chmod -R 755 storage/
    chmod -R 775 storage/files/  # Files directory needs write permissions
else
    # Option 2: If still running as root (set to www-data or create dedicated user)
    echo "Creating dedicated llmready user..."
    useradd -r -s /bin/false llmready 2>/dev/null || echo "User already exists"
    
    chown -R llmready:llmready storage/
    chmod -R 755 storage/
    chmod -R 775 storage/files/
    
    echo ""
    echo "⚠️  IMPORTANT: Update systemd service to run as llmready user:"
    echo "   Edit /etc/systemd/system/llmready-backend.service"
    echo "   Change: User=root"
    echo "   To:     User=llmready"
fi

echo ""
echo "New permissions:"
ls -la storage/

echo ""
echo "=========================================="
echo "✅ Permissions Fixed"
echo "=========================================="
echo ""
echo "Files in storage/ can now be:"
echo "  ✅ Created by backend"
echo "  ✅ Deleted by backend"
echo "  ✅ Read by backend"
echo "=========================================="
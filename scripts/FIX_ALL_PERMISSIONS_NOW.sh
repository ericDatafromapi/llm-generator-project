#!/bin/bash
# COMPLETE FIX - Run this ONCE to fix all permissions

if [ "$EUID" -ne 0 ]; then 
    echo "Please run as root: sudo ./FIX_ALL_PERMISSIONS_NOW.sh"
    exit 1
fi

DEPLOY_USER=${1:-ebadarou}

echo "=========================================="
echo "🔧 COMPLETE PERMISSION FIX"
echo "=========================================="
echo ""

cd /opt/llmready

echo "1. Fixing ownership of ALL project files..."
chown -R $DEPLOY_USER:$DEPLOY_USER /opt/llmready/
echo "✅ Project ownership fixed"

echo ""
echo "2. Adding $DEPLOY_USER to docker group..."
usermod -aG docker $DEPLOY_USER
echo "✅ Docker group added"

echo ""
echo "3. Creating sudoers file for deployment..."
cat > /etc/sudoers.d/llmready-deploy << EOF
$DEPLOY_USER ALL=(ALL) NOPASSWD: /bin/systemctl
$DEPLOY_USER ALL=(ALL) NOPASSWD: /usr/bin/docker
$DEPLOY_USER ALL=(ALL) NOPASSWD: /usr/local/bin/docker-compose
$DEPLOY_USER ALL=(ALL) NOPASSWD: /usr/bin/docker-compose
$DEPLOY_USER ALL=(ALL) NOPASSWD: /bin/mkdir, /bin/chown, /bin/chmod, /bin/tar, /bin/mv
$DEPLOY_USER ALL=(ALL) NOPASSWD: /usr/sbin/nginx
EOF
chmod 440 /etc/sudoers.d/llmready-deploy
echo "✅ Sudoers configured"

echo ""
echo "4. Fixing storage permissions..."
mkdir -p backend/storage/files
chown -R llmready:llmready backend/storage/
chmod -R 775 backend/storage/
echo "✅ Storage permissions fixed"

echo ""
echo "=========================================="
echo "✅ ALL PERMISSIONS FIXED"
echo "=========================================="
echo ""
echo "Now:"
echo "  ✅ All files owned by $DEPLOY_USER"
echo "  ✅ Can run docker commands"
echo "  ✅ Can restart services"
echo "  ✅ Storage accessible"
echo ""
echo "⚠️  $DEPLOY_USER must logout/login for docker group"
echo "    Or run: newgrp docker"
echo "=========================================="
#!/bin/bash
# Update sudoers for deployment user

if [ "$EUID" -ne 0 ]; then 
    echo "Please run as root: sudo ./update_sudoers.sh"
    exit 1
fi

echo "=========================================="
echo "🔧 Updating Sudoers for Deployment"
echo "=========================================="
echo ""

# Get the deploy user
DEPLOY_USER=${1:-ebadarou}

echo "Configuring sudo access for: $DEPLOY_USER"
echo ""

# Create sudoers file for deployment
cat > /etc/sudoers.d/llmready-deploy << EOF
# LLMReady deployment permissions for $DEPLOY_USER
$DEPLOY_USER ALL=(ALL) NOPASSWD: /bin/systemctl restart llmready-backend
$DEPLOY_USER ALL=(ALL) NOPASSWD: /bin/systemctl restart llmready-celery-worker
$DEPLOY_USER ALL=(ALL) NOPASSWD: /bin/systemctl restart llmready-celery-beat
$DEPLOY_USER ALL=(ALL) NOPASSWD: /bin/systemctl reload nginx
$DEPLOY_USER ALL=(ALL) NOPASSWD: /bin/systemctl daemon-reload
$DEPLOY_USER ALL=(ALL) NOPASSWD: /bin/mkdir
$DEPLOY_USER ALL=(ALL) NOPASSWD: /bin/chown
$DEPLOY_USER ALL=(ALL) NOPASSWD: /bin/chmod
$DEPLOY_USER ALL=(ALL) NOPASSWD: /bin/tar
$DEPLOY_USER ALL=(ALL) NOPASSWD: /bin/mv
$DEPLOY_USER ALL=(ALL) NOPASSWD: /usr/bin/docker
$DEPLOY_USER ALL=(ALL) NOPASSWD: /usr/local/bin/docker-compose
$DEPLOY_USER ALL=(ALL) NOPASSWD: /usr/bin/docker-compose
EOF

chmod 440 /etc/sudoers.d/llmready-deploy

echo "✅ Sudoers file created: /etc/sudoers.d/llmready-deploy"

# Add user to docker group
usermod -aG docker $DEPLOY_USER
echo "✅ User added to docker group"

echo ""
echo "=========================================="
echo "✅ Configuration Complete"
echo "=========================================="
echo ""
echo "User $DEPLOY_USER can now:"
echo "  ✅ Run docker commands"
echo "  ✅ Restart services"
echo "  ✅ Manage files"
echo ""
echo "⚠️  User must logout and login for docker group to take effect"
echo "    Or run: newgrp docker"
echo "=========================================="
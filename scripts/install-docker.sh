#!/bin/bash
# Install Docker on Debian/Ubuntu for LLMReady Generation Tasks

set -e

echo "=========================================="
echo "Installing Docker for LLMReady"
echo "=========================================="

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "Please run as root (use sudo)"
    exit 1
fi

# Update package index
echo "Updating package index..."
apt-get update

# Install prerequisites
echo "Installing prerequisites..."
apt-get install -y \
    ca-certificates \
    curl \
    gnupg \
    lsb-release

# Add Docker's official GPG key
echo "Adding Docker GPG key..."
mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# Set up Docker repository
echo "Setting up Docker repository..."
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian \
  $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null

# Update package index again
apt-get update

# Install Docker Engine
echo "Installing Docker Engine..."
apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Start and enable Docker
echo "Starting Docker service..."
systemctl start docker
systemctl enable docker

# Add current user to docker group (if not root)
if [ -n "$SUDO_USER" ]; then
    echo "Adding $SUDO_USER to docker group..."
    usermod -aG docker $SUDO_USER
fi

# Pull the mdream Docker image
echo "Pulling mdream Docker image..."
docker pull harlanzw/mdream:latest

# Verify installation
echo ""
echo "=========================================="
echo "Docker Installation Complete!"
echo "=========================================="
docker --version
echo ""
echo "Testing mdream container..."
docker run --rm harlanzw/mdream --help

echo ""
echo "✅ Docker is ready for LLMReady generation tasks!"
echo ""
echo "⚠️  IMPORTANT: You may need to restart the Celery worker:"
echo "   sudo systemctl restart llmready-celery-worker"
echo ""
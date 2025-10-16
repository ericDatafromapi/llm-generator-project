#!/bin/bash

# LLMReady Server Setup Script
# Run this script on your production server to set up the environment

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}🔧 LLMReady Server Setup${NC}"
echo -e "${BLUE}========================================${NC}\n"

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${YELLOW}⚠️  This script should be run as root or with sudo${NC}"
    echo -e "${YELLOW}Run: sudo bash server-setup.sh${NC}"
    exit 1
fi

echo -e "${GREEN}📋 Installing system dependencies...${NC}\n"

# Update system
apt-get update
apt-get upgrade -y

# Install required packages
apt-get install -y \
    curl \
    wget \
    git \
    nginx \
    certbot \
    python3-certbot-nginx \
    ufw

# Install Docker
if ! command -v docker &> /dev/null; then
    echo -e "${GREEN}🐳 Installing Docker...${NC}"
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
    systemctl enable docker
    systemctl start docker
else
    echo -e "${GREEN}✅ Docker already installed${NC}"
fi

# Install Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo -e "${GREEN}🐳 Installing Docker Compose...${NC}"
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
else
    echo -e "${GREEN}✅ Docker Compose already installed${NC}"
fi

# Create deployment directory
echo -e "\n${GREEN}📁 Creating deployment directories...${NC}"
mkdir -p /opt/llmready/backups
mkdir -p /var/www/llmready

# Create deployment user
if ! id "llmready" &>/dev/null; then
    echo -e "${GREEN}👤 Creating deployment user...${NC}"
    useradd -m -s /bin/bash llmready
    usermod -aG docker llmready
else
    echo -e "${GREEN}✅ User 'llmready' already exists${NC}"
fi

# Set up SSH for deployment
echo -e "\n${GREEN}🔑 Setting up SSH access...${NC}"
mkdir -p /home/llmready/.ssh
chmod 700 /home/llmready/.ssh

echo -e "${YELLOW}Please paste your GitHub Actions public key:${NC}"
read -r SSH_PUBLIC_KEY

if [ ! -z "$SSH_PUBLIC_KEY" ]; then
    echo "$SSH_PUBLIC_KEY" >> /home/llmready/.ssh/authorized_keys
    chmod 600 /home/llmready/.ssh/authorized_keys
    chown -R llmready:llmready /home/llmready/.ssh
    echo -e "${GREEN}✅ SSH key added${NC}"
else
    echo -e "${YELLOW}⚠️  No SSH key provided. You'll need to add it manually later.${NC}"
fi

# Set up firewall
echo -e "\n${GREEN}🔥 Configuring firewall...${NC}"
ufw --force enable
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow http
ufw allow https
echo -e "${GREEN}✅ Firewall configured${NC}"

# Configure nginx
echo -e "\n${GREEN}🌐 Configuring nginx...${NC}"

# Get domain name
echo -e "${YELLOW}Enter your domain name (e.g., example.com):${NC}"
read -r DOMAIN_NAME

if [ -z "$DOMAIN_NAME" ]; then
    echo -e "${RED}❌ Domain name is required${NC}"
    exit 1
fi

# Create nginx configuration
cat > /etc/nginx/sites-available/llmready << EOF
# Frontend (React)
server {
    listen 80;
    listen [::]:80;
    server_name $DOMAIN_NAME www.$DOMAIN_NAME;
    
    root /var/www/llmready/dist;
    index index.html;
    
    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1000;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/json;
    
    location / {
        try_files \$uri \$uri/ /index.html;
    }
    
    # API proxy
    location /api {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
        proxy_read_timeout 300s;
        proxy_connect_timeout 300s;
    }
    
    # Health check endpoint
    location /health {
        proxy_pass http://localhost:8000/health;
        access_log off;
    }
    
    # Cache static assets
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
EOF

# Enable site
ln -sf /etc/nginx/sites-available/llmready /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Test nginx configuration
nginx -t

# Reload nginx
systemctl reload nginx

echo -e "${GREEN}✅ Nginx configured${NC}"

# Set up SSL with Let's Encrypt
echo -e "\n${YELLOW}Would you like to set up SSL with Let's Encrypt? (y/N)${NC}"
read -r setup_ssl

if [[ "$setup_ssl" =~ ^[Yy]$ ]]; then
    echo -e "${GREEN}🔒 Setting up SSL...${NC}"
    certbot --nginx -d $DOMAIN_NAME -d www.$DOMAIN_NAME --non-interactive --agree-tos --register-unsafely-without-email
    
    # Set up auto-renewal
    (crontab -l 2>/dev/null; echo "0 0 * * * certbot renew --quiet --post-hook 'systemctl reload nginx'") | crontab -
    
    echo -e "${GREEN}✅ SSL configured and auto-renewal set up${NC}"
fi

# Set permissions
chown -R llmready:llmready /opt/llmready
chown -R www-data:www-data /var/www/llmready

echo -e "\n${BLUE}========================================${NC}"
echo -e "${GREEN}✅ Server setup complete!${NC}"
echo -e "${BLUE}========================================${NC}\n"

echo -e "${YELLOW}📝 Next steps:${NC}"
echo -e "1. Create .env file at /opt/llmready/backend/.env with your production settings"
echo -e "2. Add GitHub Actions secrets to your repository:"
echo -e "   - SSH_PRIVATE_KEY: The private key for the user 'llmready'"
echo -e "   - SERVER_HOST: $DOMAIN_NAME or your server IP"
echo -e "   - SERVER_USER: llmready"
echo -e "   - PRODUCTION_DOMAIN: $DOMAIN_NAME"
echo -e "   - PRODUCTION_API_URL: https://$DOMAIN_NAME/api"
echo -e "   - STRIPE_PUBLIC_KEY: Your Stripe publishable key"
echo -e "   - MAIL_* secrets for email notifications"
echo -e "3. Run your first deployment from VSCode: ./scripts/deploy.sh"
echo -e "\n${GREEN}🎉 Your server is ready for deployment!${NC}\n"

# Display server info
echo -e "${BLUE}Server Information:${NC}"
echo -e "Domain: $DOMAIN_NAME"
echo -e "Deployment user: llmready"
echo -e "Backend location: /opt/llmready"
echo -e "Frontend location: /var/www/llmready"
echo -e "Docker: $(docker --version)"
echo -e "Docker Compose: $(docker-compose --version)"
echo -e "Nginx: $(nginx -v 2>&1)"
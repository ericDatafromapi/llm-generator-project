#!/bin/bash

# Setup Celery Systemd Services
# Run this on your production server to enable automatic Celery startup

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}🚀 Setting up Celery Services${NC}"
echo -e "${BLUE}========================================${NC}\n"

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}❌ Please run as root: sudo ./setup-celery-services.sh${NC}"
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 1. Copy service files
echo -e "${BLUE}1️⃣  Copying service files...${NC}"

cp "$SCRIPT_DIR/llmready-celery-worker.service" /etc/systemd/system/
cp "$SCRIPT_DIR/llmready-celery-beat.service" /etc/systemd/system/

echo -e "${GREEN}✅ Service files copied${NC}\n"

# 2. Create log directory
echo -e "${BLUE}2️⃣  Creating log directory...${NC}"

mkdir -p /var/log/llmready
chown root:root /var/log/llmready

echo -e "${GREEN}✅ Log directory created${NC}\n"

# 3. Reload systemd
echo -e "${BLUE}3️⃣  Reloading systemd...${NC}"

systemctl daemon-reload

echo -e "${GREEN}✅ Systemd reloaded${NC}\n"

# 4. Enable services
echo -e "${BLUE}4️⃣  Enabling services...${NC}"

systemctl enable llmready-celery-worker
systemctl enable llmready-celery-beat

echo -e "${GREEN}✅ Services enabled (will start on boot)${NC}\n"

# 5. Start services
echo -e "${BLUE}5️⃣  Starting services...${NC}"

systemctl start llmready-celery-worker
systemctl start llmready-celery-beat

echo -e "${GREEN}✅ Services started${NC}\n"

# 6. Check status
echo -e "${BLUE}6️⃣  Checking status...${NC}\n"

if systemctl is-active --quiet llmready-celery-worker; then
    echo -e "${GREEN}✅ Celery Worker: RUNNING${NC}"
else
    echo -e "${RED}❌ Celery Worker: NOT RUNNING${NC}"
fi

if systemctl is-active --quiet llmready-celery-beat; then
    echo -e "${GREEN}✅ Celery Beat: RUNNING${NC}"
else
    echo -e "${RED}❌ Celery Beat: NOT RUNNING${NC}"
fi

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}✨ Setup Complete!${NC}"
echo -e "${BLUE}========================================${NC}\n"

echo -e "${BLUE}📝 Useful Commands:${NC}"
echo -e "  View worker logs:  ${YELLOW}sudo journalctl -u llmready-celery-worker -f${NC}"
echo -e "  View beat logs:    ${YELLOW}sudo journalctl -u llmready-celery-beat -f${NC}"
echo -e "  Restart worker:    ${YELLOW}sudo systemctl restart llmready-celery-worker${NC}"
echo -e "  Restart beat:      ${YELLOW}sudo systemctl restart llmready-celery-beat${NC}"
echo -e "  Check status:      ${YELLOW}sudo systemctl status llmready-celery-worker${NC}"
echo ""
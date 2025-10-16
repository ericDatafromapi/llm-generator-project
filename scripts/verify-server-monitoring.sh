#!/bin/bash

# Server-Side Monitoring Verification Script
# Run this ON THE SERVER after deployment to verify Sentry is working

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}🔍 Server Monitoring Verification${NC}"
echo -e "${BLUE}========================================${NC}\n"

# Check if running on server (look for /opt/llmready)
if [ ! -d "/opt/llmready" ]; then
    echo -e "${YELLOW}⚠️  /opt/llmready not found${NC}"
    echo -e "${YELLOW}Are you running this on the production server?${NC}"
    echo ""
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
    BASE_DIR="."
else
    BASE_DIR="/opt/llmready"
fi

CHECKS_PASSED=0
CHECKS_FAILED=0

check_pass() {
    echo -e "${GREEN}✅ $1${NC}"
    ((CHECKS_PASSED++))
}

check_fail() {
    echo -e "${RED}❌ $1${NC}"
    ((CHECKS_FAILED++))
}

check_warn() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

echo -e "${BLUE}1️⃣ Checking Backend Deployment...${NC}"

# Check backend directory
if [ -d "$BASE_DIR/backend" ]; then
    check_pass "Backend directory exists"
else
    check_fail "Backend directory NOT found"
    exit 1
fi

cd "$BASE_DIR/backend"

# Check critical files
if [ -f "requirements.txt" ]; then
    check_pass "requirements.txt exists"
else
    check_fail "requirements.txt NOT found"
fi

if [ -f "app/core/logging_config.py" ]; then
    check_pass "logging_config.py exists"
else
    check_fail "logging_config.py NOT found"
fi

if [ -f "app/main.py" ]; then
    check_pass "main.py exists"
else
    check_fail "main.py NOT found"
fi

echo ""
echo -e "${BLUE}2️⃣ Checking Python Environment...${NC}"

# Check if venv exists
if [ -d "$BASE_DIR/venv" ]; then
    check_pass "Virtual environment exists"
    
    # Activate and check packages
    source "$BASE_DIR/venv/bin/activate"
    
    # Check if sentry-sdk is installed
    if python -c "import sentry_sdk" 2>/dev/null; then
        check_pass "sentry-sdk is installed"
        SENTRY_VERSION=$(python -c "import sentry_sdk; print(sentry_sdk.VERSION)" 2>/dev/null || echo "unknown")
        echo -e "${BLUE}   Version: $SENTRY_VERSION${NC}"
    else
        check_fail "sentry-sdk is NOT installed"
        echo -e "${YELLOW}   Run: pip install -r requirements.txt${NC}"
    fi
    
    # Check if python-json-logger is installed
    if python -c "import pythonjsonlogger" 2>/dev/null; then
        check_pass "python-json-logger is installed"
    else
        check_fail "python-json-logger is NOT installed"
        echo -e "${YELLOW}   Run: pip install -r requirements.txt${NC}"
    fi
else
    check_fail "Virtual environment NOT found at $BASE_DIR/venv"
    echo -e "${YELLOW}   The venv should be created by the deployment script${NC}"
fi

echo ""
echo -e "${BLUE}3️⃣ Checking Environment Configuration...${NC}"

# Check .env file
if [ -f ".env" ]; then
    check_pass ".env file exists"
    
    # Check for SENTRY_DSN
    if grep -q "^SENTRY_DSN=" .env; then
        DSN_VALUE=$(grep "^SENTRY_DSN=" .env | cut -d'=' -f2 | tr -d '"' | tr -d "'")
        if [ -n "$DSN_VALUE" ]; then
            check_pass "SENTRY_DSN is configured"
            echo -e "${BLUE}   DSN: ${DSN_VALUE:0:30}...${NC}"
        else
            check_fail "SENTRY_DSN is empty"
        fi
    else
        check_fail "SENTRY_DSN not found in .env"
    fi
    
    # Check for ENVIRONMENT
    if grep -q "^ENVIRONMENT=" .env; then
        ENV_VALUE=$(grep "^ENVIRONMENT=" .env | cut -d'=' -f2 | tr -d '"' | tr -d "'")
        if [ "$ENV_VALUE" = "production" ]; then
            check_pass "ENVIRONMENT=production"
        else
            check_warn "ENVIRONMENT=$ENV_VALUE (should be 'production')"
        fi
    else
        check_warn "ENVIRONMENT not set in .env"
    fi
    
    # Check for sample rate
    if grep -q "^SENTRY_TRACES_SAMPLE_RATE=" .env; then
        RATE_VALUE=$(grep "^SENTRY_TRACES_SAMPLE_RATE=" .env | cut -d'=' -f2)
        check_pass "SENTRY_TRACES_SAMPLE_RATE=$RATE_VALUE"
    else
        check_warn "SENTRY_TRACES_SAMPLE_RATE not set (will use default)"
    fi
else
    check_fail ".env file NOT found"
    echo -e "${YELLOW}   Create .env from .env.production.example${NC}"
fi

echo ""
echo -e "${BLUE}4️⃣ Checking Backend Service...${NC}"

# Check if systemd service exists
if systemctl list-unit-files | grep -q "llmready-backend"; then
    check_pass "Backend systemd service exists"
    
    # Check if service is running
    if systemctl is-active --quiet llmready-backend; then
        check_pass "Backend service is running"
    else
        check_fail "Backend service is NOT running"
        echo -e "${YELLOW}   Start with: sudo systemctl start llmready-backend${NC}"
    fi
    
    # Check if service is enabled
    if systemctl is-enabled --quiet llmready-backend; then
        check_pass "Backend service is enabled (auto-start)"
    else
        check_warn "Backend service is NOT enabled"
        echo -e "${YELLOW}   Enable with: sudo systemctl enable llmready-backend${NC}"
    fi
else
    check_warn "Backend systemd service NOT found"
    echo -e "${YELLOW}   Service might be running in another way${NC}"
fi

echo ""
echo -e "${BLUE}5️⃣ Checking Recent Logs...${NC}"

# Check for Sentry initialization in logs
if systemctl list-unit-files | grep -q "llmready-backend"; then
    echo -e "${BLUE}Checking last 50 lines of logs for Sentry...${NC}"
    
    if sudo journalctl -u llmready-backend -n 50 2>/dev/null | grep -i "sentry" > /tmp/sentry_logs.txt; then
        if grep -q "Sentry initialized" /tmp/sentry_logs.txt; then
            check_pass "Sentry initialization found in logs"
            echo -e "${BLUE}$(grep "Sentry initialized" /tmp/sentry_logs.txt | tail -1)${NC}"
        else
            check_warn "Sentry initialization NOT found in recent logs"
            echo -e "${YELLOW}   This might be normal if service just restarted${NC}"
        fi
        
        # Show any Sentry debug messages
        if grep -q "\[sentry\]" /tmp/sentry_logs.txt; then
            echo -e "${BLUE}   Recent Sentry activity:${NC}"
            grep "\[sentry\]" /tmp/sentry_logs.txt | tail -3 | while read line; do
                echo -e "${BLUE}   $line${NC}"
            done
        fi
        rm /tmp/sentry_logs.txt
    else
        check_warn "No Sentry messages found in logs"
        echo -e "${YELLOW}   This could mean:${NC}"
        echo -e "${YELLOW}   1. Service hasn't restarted yet${NC}"
        echo -e "${YELLOW}   2. Sentry DSN not configured${NC}"
        echo -e "${YELLOW}   3. Service not using systemd${NC}"
    fi
else
    check_warn "Cannot check logs (systemd service not found)"
fi

echo ""
echo -e "${BLUE}6️⃣ Checking Database Connection...${NC}"

# Check if database is accessible
if [ -f ".env" ]; then
    DB_URL=$(grep "^DATABASE_URL=" .env | cut -d'=' -f2 | tr -d '"' | tr -d "'")
    if [ -n "$DB_URL" ]; then
        check_pass "Database URL configured"
    else
        check_warn "Database URL not found"
    fi
fi

# Check Docker containers
if command -v docker &> /dev/null; then
    if docker ps | grep -q "postgres"; then
        check_pass "PostgreSQL container is running"
    else
        check_warn "PostgreSQL container NOT running"
        echo -e "${YELLOW}   Start with: docker compose up -d${NC}"
    fi
    
    if docker ps | grep -q "redis"; then
        check_pass "Redis container is running"
    else
        check_warn "Redis container NOT running"
        echo -e "${YELLOW}   Start with: docker compose up -d${NC}"
    fi
else
    check_warn "Docker not found (might not be using Docker)"
fi

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}📊 Summary${NC}"
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}✅ Passed: ${CHECKS_PASSED}${NC}"
echo -e "${RED}❌ Failed: ${CHECKS_FAILED}${NC}"
echo ""

if [ $CHECKS_FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 Server monitoring setup looks good!${NC}"
    echo ""
    echo -e "${BLUE}📝 Next Steps:${NC}"
    echo -e "1. Test error tracking: curl http://localhost:8000/test-sentry"
    echo -e "2. Check Sentry dashboard for the test error"
    echo -e "3. Monitor logs: sudo journalctl -u llmready-backend -f"
    echo ""
else
    echo -e "${RED}❌ Some issues found!${NC}"
    echo ""
    echo -e "${BLUE}🔧 Quick Fixes:${NC}"
    
    if ! python -c "import sentry_sdk" 2>/dev/null; then
        echo -e "1. Install dependencies:"
        echo -e "   ${YELLOW}cd $BASE_DIR/backend${NC}"
        echo -e "   ${YELLOW}source ../venv/bin/activate${NC}"
        echo -e "   ${YELLOW}pip install -r requirements.txt${NC}"
        echo ""
    fi
    
    if [ ! -f ".env" ] || ! grep -q "^SENTRY_DSN=" .env; then
        echo -e "2. Configure Sentry DSN:"
        echo -e "   ${YELLOW}nano $BASE_DIR/backend/.env${NC}"
        echo -e "   ${YELLOW}Add: SENTRY_DSN=your_production_dsn${NC}"
        echo ""
    fi
    
    if ! systemctl is-active --quiet llmready-backend 2>/dev/null; then
        echo -e "3. Restart backend service:"
        echo -e "   ${YELLOW}sudo systemctl restart llmready-backend${NC}"
        echo ""
    fi
fi

exit $CHECKS_FAILED
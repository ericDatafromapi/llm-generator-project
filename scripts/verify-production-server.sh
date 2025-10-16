#!/bin/bash

# Complete Production Server Health Check
# Verifies ALL services: Backend, Frontend, Database, Redis, Celery, Nginx, Monitoring

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Counters
PASSED=0
FAILED=0
WARNINGS=0

check_pass() {
    echo -e "${GREEN}✅ $1${NC}"
    ((PASSED++))
}

check_fail() {
    echo -e "${RED}❌ $1${NC}"
    ((FAILED++))
}

check_warn() {
    echo -e "${YELLOW}⚠️  $1${NC}"
    ((WARNINGS++))
}

check_info() {
    echo -e "${CYAN}ℹ️  $1${NC}"
}

section() {
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

echo -e "${CYAN}"
echo "╔════════════════════════════════════════════╗"
echo "║  LLMReady Production Server Health Check  ║"
echo "╔════════════════════════════════════════════╗"
echo -e "${NC}"

# Check if running as root for some checks
if [ "$EUID" -ne 0 ]; then 
    check_warn "Not running as root - some checks may be limited"
fi

# ============================================
section "1️⃣  System Information"
# ============================================

check_info "Hostname: $(hostname)"
check_info "OS: $(cat /etc/os-release | grep PRETTY_NAME | cut -d'"' -f2)"
check_info "Kernel: $(uname -r)"
check_info "Uptime: $(uptime -p)"
check_info "Memory: $(free -h | grep Mem | awk '{print $3 "/" $2}')"
check_info "Disk: $(df -h / | tail -1 | awk '{print $3 "/" $2 " (" $5 " used)"}')"

# ============================================
section "2️⃣  Backend Directory Structure"
# ============================================

BASE_DIR="/opt/llmready"

if [ -d "$BASE_DIR" ]; then
    check_pass "Base directory exists: $BASE_DIR"
else
    check_fail "Base directory NOT found: $BASE_DIR"
    echo -e "${RED}Cannot continue without base directory${NC}"
    exit 1
fi

cd "$BASE_DIR"

# Check critical directories and files
CRITICAL_PATHS=(
    "backend/app/main.py"
    "backend/app/core/config.py"
    "backend/app/core/database.py"
    "backend/app/core/security.py"
    "backend/requirements.txt"
    "backend/alembic.ini"
    "docker-compose.yml"
)

for path in "${CRITICAL_PATHS[@]}"; do
    if [ -e "$path" ]; then
        check_pass "Found: $path"
    else
        check_fail "Missing: $path"
    fi
done

# ============================================
section "3️⃣  Python Environment"
# ============================================

if [ -d "venv" ]; then
    check_pass "Virtual environment exists"
    
    # Activate venv
    source venv/bin/activate
    
    # Check Python version
    PYTHON_VERSION=$(python --version 2>&1)
    check_info "Python: $PYTHON_VERSION"
    
    # Check critical packages
    REQUIRED_PACKAGES=(
        "fastapi"
        "uvicorn"
        "sqlalchemy"
        "alembic"
        "stripe"
        "sendgrid"
        "celery"
        "redis"
        "sentry_sdk"
    )
    
    for package in "${REQUIRED_PACKAGES[@]}"; do
        if python -c "import $package" 2>/dev/null; then
            VERSION=$(python -c "import $package; print(getattr($package, '__version__', 'unknown'))" 2>/dev/null || echo "unknown")
            check_pass "$package installed (v$VERSION)"
        else
            check_fail "$package NOT installed"
        fi
    done
else
    check_fail "Virtual environment NOT found"
    check_warn "Run: python3 -m venv venv && source venv/bin/activate && pip install -r backend/requirements.txt"
fi

# ============================================
section "4️⃣  Environment Configuration"
# ============================================

if [ -f "backend/.env" ]; then
    check_pass "Backend .env file exists"
    
    # Check critical environment variables
    REQUIRED_VARS=(
        "DATABASE_URL"
        "REDIS_URL"
        "SECRET_KEY"
        "STRIPE_SECRET_KEY"
        "STRIPE_WEBHOOK_SECRET"
        "SENDGRID_API_KEY"
        "FRONTEND_URL"
    )
    
    for var in "${REQUIRED_VARS[@]}"; do
        if grep -q "^${var}=" backend/.env; then
            VALUE=$(grep "^${var}=" backend/.env | cut -d'=' -f2 | tr -d '"' | tr -d "'")
            if [ -n "$VALUE" ] && [ "$VALUE" != "your_" ] && [ "$VALUE" != "sk_test_" ]; then
                check_pass "$var is configured"
            else
                check_warn "$var is empty or has placeholder value"
            fi
        else
            check_fail "$var NOT found in .env"
        fi
    done
    
    # Check monitoring variables
    if grep -q "^SENTRY_DSN=" backend/.env; then
        check_pass "SENTRY_DSN is configured"
    else
        check_warn "SENTRY_DSN not configured (monitoring disabled)"
    fi
    
    # Check environment setting
    if grep -q "^ENVIRONMENT=production" backend/.env; then
        check_pass "ENVIRONMENT=production"
    else
        check_warn "ENVIRONMENT not set to production"
    fi
else
    check_fail "Backend .env file NOT found"
fi

# ============================================
section "5️⃣  Docker Services"
# ============================================

if command -v docker &> /dev/null; then
    check_pass "Docker is installed"
    
    if command -v docker-compose &> /dev/null || docker compose version &> /dev/null; then
        check_pass "Docker Compose is available"
        
        # Check if containers are running
        if docker ps --format '{{.Names}}' | grep -q "postgres"; then
            check_pass "PostgreSQL container is running"
            
            # Check PostgreSQL health
            if docker exec $(docker ps -qf "name=postgres") pg_isready -U postgres &> /dev/null; then
                check_pass "PostgreSQL is accepting connections"
            else
                check_fail "PostgreSQL is NOT accepting connections"
            fi
        else
            check_fail "PostgreSQL container is NOT running"
            check_warn "Start with: docker compose up -d"
        fi
        
        if docker ps --format '{{.Names}}' | grep -q "redis"; then
            check_pass "Redis container is running"
            
            # Check Redis health
            if docker exec $(docker ps -qf "name=redis") redis-cli ping 2>/dev/null | grep -q "PONG"; then
                check_pass "Redis is responding"
            else
                check_fail "Redis is NOT responding"
            fi
        else
            check_fail "Redis container is NOT running"
            check_warn "Start with: docker compose up -d"
        fi
    else
        check_fail "Docker Compose NOT found"
    fi
else
    check_fail "Docker is NOT installed"
fi

# ============================================
section "6️⃣  Database Status"
# ============================================

if [ -f "backend/.env" ]; then
    DB_URL=$(grep "^DATABASE_URL=" backend/.env | cut -d'=' -f2 | tr -d '"' | tr -d "'")
    
    if [ -n "$DB_URL" ]; then
        check_info "Database URL: ${DB_URL:0:30}..."
        
        # Try to connect and check migrations
        cd backend
        if [ -d "venv" ]; then
            source ../venv/bin/activate
        fi
        
        # Check if alembic is configured
        if python -c "from alembic import config; config.Config('alembic.ini')" 2>/dev/null; then
            check_pass "Alembic is configured"
            
            # Check current migration version
            CURRENT=$(alembic current 2>/dev/null | grep -oP '(?<=\(head\) ).*' || echo "unknown")
            check_info "Current migration: $CURRENT"
            
            # Check if there are pending migrations
            if alembic check 2>&1 | grep -q "up to date"; then
                check_pass "Database migrations are up to date"
            else
                check_warn "Database might need migrations"
                check_info "Run: alembic upgrade head"
            fi
        else
            check_warn "Cannot verify Alembic configuration"
        fi
        
        cd ..
    fi
fi

# ============================================
section "7️⃣  Backend Service (systemd)"
# ============================================

SERVICE_NAME="llmready-backend"

if systemctl list-unit-files | grep -q "$SERVICE_NAME"; then
    check_pass "Systemd service exists: $SERVICE_NAME"
    
    # Check if service is active
    if systemctl is-active --quiet $SERVICE_NAME; then
        check_pass "Backend service is running"
        
        # Get service info
        SINCE=$(systemctl show $SERVICE_NAME --property=ActiveEnterTimestamp --value)
        check_info "Running since: $SINCE"
        
        # Check recent logs for errors
        ERROR_COUNT=$(journalctl -u $SERVICE_NAME -n 100 --no-pager 2>/dev/null | grep -i "error" | wc -l)
        if [ "$ERROR_COUNT" -gt 0 ]; then
            check_warn "Found $ERROR_COUNT errors in recent logs"
        else
            check_pass "No errors in recent logs"
        fi
    else
        check_fail "Backend service is NOT running"
        check_warn "Start with: sudo systemctl start $SERVICE_NAME"
    fi
    
    # Check if service is enabled
    if systemctl is-enabled --quiet $SERVICE_NAME; then
        check_pass "Backend service is enabled (auto-start)"
    else
        check_warn "Backend service is NOT enabled"
        check_info "Enable with: sudo systemctl enable $SERVICE_NAME"
    fi
else
    check_fail "Systemd service NOT found: $SERVICE_NAME"
    check_warn "Service might be running manually or through other means"
fi

# ============================================
section "8️⃣  Celery Workers"
# ============================================

# Check if Celery is running
if pgrep -f "celery.*worker" > /dev/null; then
    check_pass "Celery worker process is running"
    
    CELERY_COUNT=$(pgrep -f "celery.*worker" | wc -l)
    check_info "Running $CELERY_COUNT Celery worker(s)"
else
    check_warn "Celery worker is NOT running"
    check_info "Tasks won't be processed (generations, emails, etc.)"
fi

# Check Celery beat (scheduler)
if pgrep -f "celery.*beat" > /dev/null; then
    check_pass "Celery beat (scheduler) is running"
else
    check_warn "Celery beat is NOT running"
    check_info "Scheduled tasks won't run"
fi

# ============================================
section "9️⃣  Backend API Health"
# ============================================

# Try to reach the backend API
API_PORT="8000"

if curl -sf http://localhost:$API_PORT/health > /tmp/health_check.json 2>/dev/null; then
    check_pass "Backend API is responding on port $API_PORT"
    
    # Parse health check response
    if command -v jq &> /dev/null; then
        STATUS=$(jq -r '.status' /tmp/health_check.json 2>/dev/null || echo "unknown")
        DB_STATUS=$(jq -r '.database' /tmp/health_check.json 2>/dev/null || echo "unknown")
        
        if [ "$STATUS" = "healthy" ]; then
            check_pass "API health status: $STATUS"
        else
            check_warn "API health status: $STATUS"
        fi
        
        if [ "$DB_STATUS" = "connected" ]; then
            check_pass "Database connection: $DB_STATUS"
        else
            check_fail "Database connection: $DB_STATUS"
        fi
    else
        check_info "Install jq for detailed health check: sudo apt install jq"
    fi
    
    rm /tmp/health_check.json
else
    check_fail "Backend API is NOT responding on port $API_PORT"
    check_warn "Check backend logs: sudo journalctl -u $SERVICE_NAME -n 50"
fi

# ============================================
section "🔟 Frontend Deployment"
# ============================================

FRONTEND_DIR="/var/www/llmready"

if [ -d "$FRONTEND_DIR" ]; then
    check_pass "Frontend directory exists: $FRONTEND_DIR"
    
    if [ -d "$FRONTEND_DIR/dist" ]; then
        check_pass "Frontend build (dist/) exists"
        
        # Check index.html
        if [ -f "$FRONTEND_DIR/dist/index.html" ]; then
            check_pass "Frontend index.html exists"
        else
            check_fail "Frontend index.html NOT found"
        fi
        
        # Check file permissions
        OWNER=$(stat -c '%U' "$FRONTEND_DIR/dist" 2>/dev/null || stat -f '%Su' "$FRONTEND_DIR/dist" 2>/dev/null)
        if [ "$OWNER" = "www-data" ] || [ "$OWNER" = "nginx" ]; then
            check_pass "Frontend files owned by web server user"
        else
            check_warn "Frontend files owned by: $OWNER (should be www-data or nginx)"
        fi
    else
        check_fail "Frontend build (dist/) NOT found"
        check_warn "Deploy frontend: npm run build && upload dist/"
    fi
else
    check_fail "Frontend directory NOT found: $FRONTEND_DIR"
fi

# ============================================
section "1️⃣1️⃣  Nginx / Web Server"
# ============================================

if command -v nginx &> /dev/null; then
    check_pass "Nginx is installed"
    
    # Check if nginx is running
    if systemctl is-active --quiet nginx; then
        check_pass "Nginx is running"
    else
        check_fail "Nginx is NOT running"
        check_warn "Start with: sudo systemctl start nginx"
    fi
    
    # Check nginx configuration
    if nginx -t &> /tmp/nginx_test.log; then
        check_pass "Nginx configuration is valid"
    else
        check_fail "Nginx configuration has errors"
        check_info "Check: sudo nginx -t"
    fi
    rm /tmp/nginx_test.log 2>/dev/null
    
    # Check for LLMReady site config
    if [ -f "/etc/nginx/sites-available/llmready" ] || [ -f "/etc/nginx/conf.d/llmready.conf" ]; then
        check_pass "LLMReady nginx configuration found"
    else
        check_warn "LLMReady nginx configuration NOT found"
    fi
else
    check_warn "Nginx is NOT installed (might use Apache or other)"
fi

# ============================================
section "1️⃣2️⃣  SSL/TLS Certificates"
# ============================================

# Check for SSL certificates (common locations)
if [ -f "/etc/letsencrypt/live/*/fullchain.pem" ]; then
    check_pass "Let's Encrypt certificates found"
    
    # Check expiration
    CERT_FILE=$(find /etc/letsencrypt/live -name "fullchain.pem" | head -1)
    if [ -n "$CERT_FILE" ]; then
        EXPIRY=$(openssl x509 -enddate -noout -in "$CERT_FILE" 2>/dev/null | cut -d= -f2)
        check_info "Certificate expires: $EXPIRY"
    fi
else
    check_warn "SSL certificates NOT found (might not be using HTTPS)"
fi

# ============================================
section "1️⃣3️⃣  Network & Firewall"
# ============================================

# Check open ports
check_info "Open ports:"
if command -v ss &> /dev/null; then
    ss -tulpn 2>/dev/null | grep LISTEN | grep -E ":(80|443|8000|5432|6379) " | while read line; do
        PORT=$(echo $line | grep -oP ':\K[0-9]+' | head -1)
        check_info "  Port $PORT is open"
    done
fi

# Check if firewall is active
if command -v ufw &> /dev/null; then
    if ufw status | grep -q "Status: active"; then
        check_pass "UFW firewall is active"
    else
        check_warn "UFW firewall is inactive"
    fi
fi

# ============================================
section "1️⃣4️⃣  Monitoring (Sentry)"
# ============================================

if [ -f "$BASE_DIR/backend/.env" ]; then
    if grep -q "^SENTRY_DSN=" "$BASE_DIR/backend/.env"; then
        DSN=$(grep "^SENTRY_DSN=" "$BASE_DIR/backend/.env" | cut -d'=' -f2 | tr -d '"' | tr -d "'")
        if [ -n "$DSN" ] && [ "$DSN" != "" ]; then
            check_pass "Sentry DSN is configured"
            
            # Check if sentry-sdk is installed
            if python -c "import sentry_sdk" 2>/dev/null; then
                check_pass "Sentry SDK is installed"
            else
                check_fail "Sentry SDK is NOT installed"
            fi
            
            # Check logs for Sentry initialization
            if journalctl -u $SERVICE_NAME -n 100 2>/dev/null | grep -q "Sentry initialized"; then
                check_pass "Sentry initialized in recent logs"
            else
                check_warn "Sentry initialization not found in recent logs"
            fi
        else
            check_warn "Sentry DSN is empty (monitoring disabled)"
        fi
    else
        check_warn "Sentry DSN not configured (monitoring disabled)"
    fi
fi

# ============================================
section "1️⃣5️⃣  Disk Space & Logs"
# ============================================

# Check disk space
DISK_USAGE=$(df -h / | tail -1 | awk '{print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -lt 80 ]; then
    check_pass "Disk usage: ${DISK_USAGE}% (healthy)"
elif [ "$DISK_USAGE" -lt 90 ]; then
    check_warn "Disk usage: ${DISK_USAGE}% (getting high)"
else
    check_fail "Disk usage: ${DISK_USAGE}% (critical!)"
fi

# Check log file sizes
if [ -d "/var/log/llmready" ]; then
    LOG_SIZE=$(du -sh /var/log/llmready 2>/dev/null | cut -f1)
    check_info "Log directory size: $LOG_SIZE"
fi

# ============================================
section "📊 Final Summary"
# ============================================

TOTAL=$((PASSED + FAILED + WARNINGS))

echo ""
echo -e "${GREEN}✅ Passed: $PASSED${NC}"
echo -e "${RED}❌ Failed: $FAILED${NC}"
echo -e "${YELLOW}⚠️  Warnings: $WARNINGS${NC}"
echo -e "${CYAN}📊 Total checks: $TOTAL${NC}"
echo ""

if [ $FAILED -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}╔════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║  🎉 ALL SYSTEMS OPERATIONAL! 🎉       ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════╝${NC}"
    exit 0
elif [ $FAILED -eq 0 ]; then
    echo -e "${YELLOW}╔════════════════════════════════════════╗${NC}"
    echo -e "${YELLOW}║  ⚠️  System OK with minor warnings    ║${NC}"
    echo -e "${YELLOW}╚════════════════════════════════════════╝${NC}"
    exit 0
else
    echo -e "${RED}╔════════════════════════════════════════╗${NC}"
    echo -e "${RED}║  ❌ CRITICAL ISSUES FOUND!            ║${NC}"
    echo -e "${RED}╚════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${YELLOW}Please fix the failed checks above before deploying.${NC}"
    exit 1
fi
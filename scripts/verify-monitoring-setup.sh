#!/bin/bash

# Monitoring Setup Verification Script
# Checks that Sentry monitoring is properly configured before deployment

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Counters
CHECKS_PASSED=0
CHECKS_FAILED=0
WARNINGS=0

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}🔍 Monitoring Setup Verification${NC}"
echo -e "${BLUE}========================================${NC}\n"

# Helper functions
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
    ((WARNINGS++))
}

check_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Check if we're in the right directory
if [ ! -f "backend/requirements.txt" ] || [ ! -f "frontend/package.json" ]; then
    echo -e "${RED}❌ Error: Must run from project root directory${NC}"
    exit 1
fi

echo -e "${BLUE}📦 Checking Backend Dependencies...${NC}"

# Check backend requirements.txt
if grep -q "sentry-sdk\[fastapi\]" backend/requirements.txt; then
    check_pass "Backend: sentry-sdk[fastapi] in requirements.txt"
else
    check_fail "Backend: sentry-sdk[fastapi] NOT in requirements.txt"
fi

if grep -q "python-json-logger" backend/requirements.txt; then
    check_pass "Backend: python-json-logger in requirements.txt"
else
    check_fail "Backend: python-json-logger NOT in requirements.txt"
fi

echo ""
echo -e "${BLUE}📂 Checking Backend Files...${NC}"

# Check backend files exist
if [ -f "backend/app/core/logging_config.py" ]; then
    check_pass "Backend: logging_config.py exists"
    
    # Check content
    if grep -q "def configure_monitoring" backend/app/core/logging_config.py; then
        check_pass "Backend: configure_monitoring() function found"
    else
        check_fail "Backend: configure_monitoring() function NOT found"
    fi
    
    if grep -q "setup_sentry" backend/app/core/logging_config.py; then
        check_pass "Backend: setup_sentry() function found"
    else
        check_fail "Backend: setup_sentry() function NOT found"
    fi
else
    check_fail "Backend: logging_config.py NOT found"
fi

# Check main.py has sentry integration
if grep -q "from app.core.logging_config import configure_monitoring" backend/app/main.py; then
    check_pass "Backend: main.py imports configure_monitoring"
else
    check_fail "Backend: main.py does NOT import configure_monitoring"
fi

if grep -q "configure_monitoring()" backend/app/main.py; then
    check_pass "Backend: main.py calls configure_monitoring()"
else
    check_fail "Backend: main.py does NOT call configure_monitoring()"
fi

if grep -q "import sentry_sdk" backend/app/main.py; then
    check_pass "Backend: main.py imports sentry_sdk"
else
    check_fail "Backend: main.py does NOT import sentry_sdk"
fi

if grep -q "global_exception_handler" backend/app/main.py; then
    check_pass "Backend: Global exception handler configured"
else
    check_fail "Backend: Global exception handler NOT configured"
fi

# Check config.py has sentry settings
if grep -q "SENTRY_DSN" backend/app/core/config.py; then
    check_pass "Backend: config.py has SENTRY_DSN setting"
else
    check_fail "Backend: config.py does NOT have SENTRY_DSN setting"
fi

if grep -q "SENTRY_TRACES_SAMPLE_RATE" backend/app/core/config.py; then
    check_pass "Backend: config.py has SENTRY_TRACES_SAMPLE_RATE setting"
else
    check_fail "Backend: config.py does NOT have SENTRY_TRACES_SAMPLE_RATE setting"
fi

echo ""
echo -e "${BLUE}🌐 Checking Frontend Dependencies...${NC}"

# Check frontend package.json
if grep -q '"@sentry/react"' frontend/package.json; then
    check_pass "Frontend: @sentry/react in package.json"
else
    check_fail "Frontend: @sentry/react NOT in package.json"
fi

if grep -q '"@sentry/vite-plugin"' frontend/package.json; then
    check_pass "Frontend: @sentry/vite-plugin in devDependencies"
else
    check_fail "Frontend: @sentry/vite-plugin NOT in devDependencies"
fi

echo ""
echo -e "${BLUE}📂 Checking Frontend Files...${NC}"

# Check frontend files exist
if [ -f "frontend/src/lib/sentry.ts" ]; then
    check_pass "Frontend: sentry.ts exists"
    
    # Check content
    if grep -q "export function initSentry" frontend/src/lib/sentry.ts; then
        check_pass "Frontend: initSentry() function found"
    else
        check_fail "Frontend: initSentry() function NOT found"
    fi
    
    if grep -q "export function setSentryUser" frontend/src/lib/sentry.ts; then
        check_pass "Frontend: setSentryUser() function found"
    else
        check_fail "Frontend: setSentryUser() function NOT found"
    fi
else
    check_fail "Frontend: sentry.ts NOT found"
fi

# Check main.tsx has sentry integration
if grep -q "import.*sentry" frontend/src/main.tsx; then
    check_pass "Frontend: main.tsx imports Sentry"
else
    check_fail "Frontend: main.tsx does NOT import Sentry"
fi

if grep -q "initSentry()" frontend/src/main.tsx; then
    check_pass "Frontend: main.tsx calls initSentry()"
else
    check_fail "Frontend: main.tsx does NOT call initSentry()"
fi

if grep -q "Sentry.ErrorBoundary" frontend/src/main.tsx; then
    check_pass "Frontend: Error boundary configured"
else
    check_fail "Frontend: Error boundary NOT configured"
fi

# Check authStore has sentry user tracking
if grep -q "setSentryUser" frontend/src/store/authStore.ts; then
    check_pass "Frontend: authStore tracks Sentry user context"
else
    check_warn "Frontend: authStore does NOT track Sentry user context (optional)"
fi

# Check vite.config.ts
if grep -q "sentryVitePlugin" frontend/vite.config.ts; then
    check_pass "Frontend: vite.config.ts has Sentry plugin"
else
    check_fail "Frontend: vite.config.ts does NOT have Sentry plugin"
fi

echo ""
echo -e "${BLUE}📝 Checking Environment Files...${NC}"

# Check backend .env.example
if grep -q "SENTRY_DSN" backend/.env.example; then
    check_pass "Backend: .env.example has SENTRY_DSN"
else
    check_fail "Backend: .env.example does NOT have SENTRY_DSN"
fi

# Check backend .env.production.example
if [ -f "backend/.env.production.example" ]; then
    if grep -q "SENTRY_DSN" backend/.env.production.example; then
        check_pass "Backend: .env.production.example has SENTRY_DSN"
    else
        check_fail "Backend: .env.production.example does NOT have SENTRY_DSN"
    fi
else
    check_warn "Backend: .env.production.example NOT found"
fi

# Check frontend .env.example
if grep -q "VITE_SENTRY_DSN" frontend/.env.example; then
    check_pass "Frontend: .env.example has VITE_SENTRY_DSN"
else
    check_fail "Frontend: .env.example does NOT have VITE_SENTRY_DSN"
fi

# Check frontend .env.production.example
if [ -f "frontend/.env.production.example" ]; then
    if grep -q "VITE_SENTRY_DSN" frontend/.env.production.example; then
        check_pass "Frontend: .env.production.example has VITE_SENTRY_DSN"
    else
        check_fail "Frontend: .env.production.example does NOT have VITE_SENTRY_DSN"
    fi
else
    check_warn "Frontend: .env.production.example NOT found"
fi

echo ""
echo -e "${BLUE}🔧 Checking Local Environment...${NC}"

# Check backend .env
if [ -f "backend/.env" ]; then
    if grep -q "SENTRY_DSN=" backend/.env; then
        DSN_VALUE=$(grep "SENTRY_DSN=" backend/.env | cut -d'=' -f2)
        if [ -n "$DSN_VALUE" ] && [ "$DSN_VALUE" != '""' ] && [ "$DSN_VALUE" != "''" ]; then
            check_pass "Backend: .env has SENTRY_DSN configured"
        else
            check_warn "Backend: .env has SENTRY_DSN but it's empty (optional for dev)"
        fi
    else
        check_warn "Backend: .env does NOT have SENTRY_DSN (optional for dev)"
    fi
else
    check_warn "Backend: .env NOT found (will be created on server)"
fi

# Check frontend .env
if [ -f "frontend/.env" ]; then
    if grep -q "VITE_SENTRY_DSN=" frontend/.env; then
        DSN_VALUE=$(grep "VITE_SENTRY_DSN=" frontend/.env | cut -d'=' -f2)
        if [ -n "$DSN_VALUE" ] && [ "$DSN_VALUE" != '""' ] && [ "$DSN_VALUE" != "''" ]; then
            check_pass "Frontend: .env has VITE_SENTRY_DSN configured"
        else
            check_warn "Frontend: .env has VITE_SENTRY_DSN but it's empty (optional for dev)"
        fi
    else
        check_warn "Frontend: .env does NOT have VITE_SENTRY_DSN (optional for dev)"
    fi
else
    check_warn "Frontend: .env NOT found (create for local testing)"
fi

echo ""
echo -e "${BLUE}🚀 Checking GitHub Actions Workflow...${NC}"

if [ -f ".github/workflows/deploy-production.yml" ]; then
    check_pass "GitHub Actions workflow file exists"
    
    # Check if it has Sentry secrets
    if grep -q "BACKEND_SENTRY_DSN" .github/workflows/deploy-production.yml; then
        check_pass "Workflow: Uses BACKEND_SENTRY_DSN secret"
    else
        check_fail "Workflow: Does NOT use BACKEND_SENTRY_DSN secret"
    fi
    
    if grep -q "FRONTEND_SENTRY_DSN" .github/workflows/deploy-production.yml; then
        check_pass "Workflow: Uses FRONTEND_SENTRY_DSN secret"
    else
        check_fail "Workflow: Does NOT use FRONTEND_SENTRY_DSN secret"
    fi
    
    if grep -q "SENTRY_AUTH_TOKEN" .github/workflows/deploy-production.yml; then
        check_pass "Workflow: Uses SENTRY_AUTH_TOKEN secret"
    else
        check_fail "Workflow: Does NOT use SENTRY_AUTH_TOKEN secret"
    fi
    
    if grep -q "VITE_SENTRY_DSN" .github/workflows/deploy-production.yml; then
        check_pass "Workflow: Configures frontend with Sentry DSN"
    else
        check_fail "Workflow: Does NOT configure frontend with Sentry DSN"
    fi
else
    check_fail "GitHub Actions workflow file NOT found"
fi

echo ""
echo -e "${BLUE}📚 Checking Documentation...${NC}"

if [ -f "DEPLOY_MONITORING.md" ]; then
    check_pass "Deployment guide exists (DEPLOY_MONITORING.md)"
else
    check_warn "DEPLOY_MONITORING.md NOT found"
fi

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}📊 Summary${NC}"
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}✅ Passed: ${CHECKS_PASSED}${NC}"
echo -e "${RED}❌ Failed: ${CHECKS_FAILED}${NC}"
echo -e "${YELLOW}⚠️  Warnings: ${WARNINGS}${NC}"
echo ""

if [ $CHECKS_FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 All critical checks passed!${NC}"
    echo -e "${GREEN}You're ready to deploy monitoring to production.${NC}"
    echo ""
    echo -e "${BLUE}📝 Next Steps:${NC}"
    echo -e "1. Create production Sentry projects (backend + frontend)"
    echo -e "2. Add GitHub secrets (see DEPLOY_MONITORING.md)"
    echo -e "3. Commit and push changes"
    echo -e "4. Run: ./scripts/deploy.sh"
    echo ""
    exit 0
else
    echo -e "${RED}❌ Some critical checks failed!${NC}"
    echo -e "${YELLOW}Please fix the issues above before deploying.${NC}"
    echo ""
    exit 1
fi
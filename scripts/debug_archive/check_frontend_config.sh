#!/bin/bash
# Check frontend configuration in production

echo "=========================================="
echo "🔍 CHECKING FRONTEND CONFIGURATION"
echo "=========================================="
echo ""

# Find where frontend is deployed
FRONTEND_PATHS=(
    "/var/www/llmready"
    "/var/www/html"
    "/opt/llmready/frontend/dist"
    "/usr/share/nginx/html"
)

echo "1. Looking for frontend deployment..."
FRONTEND_DIR=""
for path in "${FRONTEND_PATHS[@]}"; do
    if [ -d "$path" ] && [ -f "$path/index.html" ]; then
        echo "✅ Found frontend at: $path"
        FRONTEND_DIR="$path"
        break
    fi
done

if [ -z "$FRONTEND_DIR" ]; then
    echo "❌ Frontend not found in common locations"
    echo "   Check where your frontend is deployed"
    exit 1
fi

echo ""
echo "2. Checking built JavaScript for API URL..."
echo ""

# Check the built JS files for API_URL
if [ -d "$FRONTEND_DIR/assets" ]; then
    echo "Searching for VITE_API_URL or API_URL in built files..."
    grep -r "VITE_API_URL\|localhost:8000\|http://localhost" "$FRONTEND_DIR/assets" 2>/dev/null | head -5
    
    echo ""
    echo "Checking main JS file..."
    MAIN_JS=$(find "$FRONTEND_DIR/assets" -name "index-*.js" | head -1)
    if [ -f "$MAIN_JS" ]; then
        echo "Main JS: $MAIN_JS"
        # Look for API URL definition
        grep -o "API_URL.*localhost\|baseURL.*localhost\|http://localhost:8000" "$MAIN_JS" | head -3
    fi
fi

echo ""
echo "3. Checking if .env.production exists in frontend source..."
if [ -f "/opt/llmready/frontend/.env.production" ]; then
    echo "✅ /opt/llmready/frontend/.env.production exists"
    echo ""
    cat /opt/llmready/frontend/.env.production
else
    echo "❌ /opt/llmready/frontend/.env.production NOT FOUND"
    echo ""
    echo "This is the problem! Frontend is using default localhost:8000"
    echo ""
    echo "Create it with:"
    echo "  cat > /opt/llmready/frontend/.env.production << 'EOF'"
    echo "  VITE_API_URL=https://api.llmready.ai"
    echo "  EOF"
fi

echo ""
echo "4. Checking nginx/web server configuration..."
if command -v nginx &> /dev/null; then
    echo "✅ Nginx installed"
    nginx -t 2>&1 | head -5
    
    # Find nginx config for frontend
    if [ -f "/etc/nginx/sites-enabled/llmready" ]; then
        echo ""
        echo "LLMReady nginx config:"
        cat /etc/nginx/sites-enabled/llmready
    fi
else
    echo "⚠️  Nginx not found (may be using different server)"
fi

echo ""
echo "=========================================="
echo "📊 DIAGNOSIS"
echo "=========================================="
echo ""
echo "If .env.production doesn't exist or VITE_API_URL is wrong:"
echo "  1. Create /opt/llmready/frontend/.env.production"
echo "  2. Add: VITE_API_URL=https://api.llmready.ai (your actual API URL)"
echo "  3. Rebuild frontend: cd /opt/llmready/frontend && npm run build"
echo "  4. Redeploy the built files"
echo ""
echo "This is why frontend can't reach backend!"
echo "=========================================="
#!/bin/bash
# Test ONE thing: Can the deployed frontend reach the backend?

echo "=========================================="
echo "🔍 STEP 1: Testing Frontend → Backend"
echo "=========================================="
echo ""

# Step 1: Find what API URL the frontend is using
echo "Checking what API URL is in the deployed frontend..."
echo ""

# Common frontend locations
FRONTEND_PATHS=(
    "/var/www/llmready/dist"
    "/var/www/html"
)

for path in "${FRONTEND_PATHS[@]}"; do
    if [ -f "$path/index.html" ]; then
        echo "✅ Found frontend at: $path"
        echo ""
        
        # Find main JS file
        MAIN_JS=$(find "$path/assets" -name "index-*.js" 2>/dev/null | head -1)
        
        if [ -f "$MAIN_JS" ]; then
            echo "Main JS file: $MAIN_JS"
            echo ""
            
            # Extract API URL from the built file
            echo "Searching for API URL in built frontend..."
            API_URL=$(grep -o 'VITE_API_URL[^"]*"[^"]*"' "$MAIN_JS" 2>/dev/null | head -1)
            
            if [ -n "$API_URL" ]; then
                echo "Found: $API_URL"
            else
                # Try different pattern
                API_URL=$(grep -o 'baseURL[^"]*"[^"]*"' "$MAIN_JS" 2>/dev/null | head -1)
                echo "Found baseURL: $API_URL"
            fi
            
            # Also check for localhost
            echo ""
            echo "Checking for localhost references:"
            grep -o "localhost:8000\|localhost\"" "$MAIN_JS" 2>/dev/null | head -3 || echo "  No localhost references found ✅"
            
        fi
        
        break
    fi
done

echo ""
echo "=========================================="
echo "🔍 STEP 2: What URL Does Browser See?"
echo "=========================================="
echo ""
echo "Open your frontend in browser and run this in DevTools Console:"
echo ""
echo "  // Check what API URL the app is using"
echo "  fetch('/assets/index-*.js')"
echo "    .then(r => r.text())"
echo "    .then(text => {"
echo "      const match = text.match(/baseURL[^\"]*\"([^\"]+)\"/)"
echo "      console.log('API URL:', match ? match[1] : 'not found')"
echo "    })"
echo ""
echo "OR simpler - just check Network tab when you click Generate:"
echo "  1. Open DevTools (F12)"
echo "  2. Go to Network tab"
echo "  3. Click 'Generate Files'"
echo "  4. Look at the URL of the POST request"
echo ""
echo "=========================================="
echo "📊 WHAT TO LOOK FOR"
echo "=========================================="
echo ""
echo "The request URL should be:"
echo "  ✅ https://api.llmready.ai/api/v1/generations/start"
echo ""
echo "NOT:"
echo "  ❌ http://localhost:8000/api/v1/generations/start"
echo ""
echo "If it's calling localhost, your PRODUCTION_API_URL secret"
echo "in GitHub is not set or the frontend wasn't rebuilt."
echo "=========================================="
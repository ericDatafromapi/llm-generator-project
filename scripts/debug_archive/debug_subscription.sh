#!/bin/bash
# DEBUG: Stripe Subscription - Step by step debugging

echo "=========================================="
echo "💳 STRIPE SUBSCRIPTION DEBUGGER"
echo "=========================================="
echo ""

cd /opt/llmready/backend

echo "1️⃣ Checking Stripe configuration..."
echo ""

# Check if Stripe keys are set
python3 << 'PYTHON_EOF'
import sys
sys.path.insert(0, '/opt/llmready/backend')

from app.core.config import settings

print("Stripe Configuration:")
print(f"  STRIPE_SECRET_KEY: {settings.STRIPE_SECRET_KEY[:15]}... (starts with {settings.STRIPE_SECRET_KEY[:7]})")
print(f"  STRIPE_WEBHOOK_SECRET: {'✅ SET' if settings.STRIPE_WEBHOOK_SECRET else '❌ NOT SET'}")
print("")

# Test Stripe connection
print("Testing Stripe API connection...")
import stripe
stripe.api_key = settings.STRIPE_SECRET_KEY

try:
    # List products to test connection
    products = stripe.Product.list(limit=1)
    print("✅ Stripe API connection: SUCCESS")
except stripe._error.AuthenticationError as e:
    print(f"❌ Stripe API authentication: FAILED - {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Stripe API error: {e}")
    sys.exit(1)
PYTHON_EOF

echo ""
echo "2️⃣ Checking webhook endpoint accessibility..."
echo ""

# Check if webhook endpoint responds
WEBHOOK_URL="http://localhost:8000/api/v1/webhooks/stripe"
echo "Testing webhook endpoint: $WEBHOOK_URL"
curl -s -o /dev/null -w "HTTP Status: %{http_code}\n" -X POST $WEBHOOK_URL -H "Content-Type: application/json" -d '{"type":"test"}'

echo ""
echo "3️⃣ Checking recent subscription records..."
echo ""

# Check database for subscriptions
sudo -u postgres psql -d llmready_prod << 'SQL_EOF'
SELECT 
    u.email,
    s.plan_type,
    s.status,
    s.stripe_customer_id,
    s.stripe_subscription_id,
    s.updated_at
FROM subscriptions s
JOIN users u ON u.id = s.user_id
ORDER BY s.updated_at DESC
LIMIT 5;
SQL_EOF

echo ""
echo "4️⃣ Checking webhook event log..."
echo ""

# Check if webhook events are being recorded
sudo -u postgres psql -d llmready_prod << 'SQL_EOF'
SELECT id, type, status, created_at
FROM stripe_events
ORDER BY created_at DESC
LIMIT 5;
SQL_EOF

echo ""
echo "=========================================="
echo "📊 READY TO DEBUG"
echo "=========================================="
echo ""
echo "Now do this:"
echo "  1. Open TWO terminals"
echo ""
echo "  Terminal 1 - Backend logs:"
echo "    sudo journalctl -u llmready-backend -f"
echo ""
echo "  Terminal 2 - Watch database:"
echo "    watch -n 1 'sudo -u postgres psql -d llmready_prod -c \"SELECT u.email, s.plan_type, s.status FROM subscriptions s JOIN users u ON u.id = s.user_id ORDER BY s.updated_at DESC LIMIT 3;\"'"
echo ""
echo "  Then subscribe to a plan from the frontend"
echo ""
echo "  Watch for:"
echo "    - POST /api/v1/subscriptions/checkout in Terminal 1"
echo "    - Webhook event in Terminal 1"
echo "    - Plan change in Terminal 2"
echo "=========================================="
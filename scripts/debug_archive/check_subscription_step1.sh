#!/bin/bash
# STEP 1: Check current subscription state

echo "=========================================="
echo "💳 STEP 1: Check Subscription State"
echo "=========================================="
echo ""

cd /opt/llmready/backend

# Check database directly (root can access postgres)
echo "Current subscriptions in database:"
echo ""

psql -U postgres -d llmready_prod << 'SQL_EOF'
SELECT 
    u.email,
    s.plan_type,
    s.status,
    s.stripe_customer_id IS NOT NULL as has_stripe_customer,
    s.stripe_subscription_id IS NOT NULL as has_stripe_subscription,
    s.updated_at
FROM subscriptions s
JOIN users u ON u.id = s.user_id
ORDER BY s.updated_at DESC
LIMIT 5;
SQL_EOF

echo ""
echo "=========================================="
echo "📝 Next Step"
echo "=========================================="
echo ""
echo "Now open your browser DevTools (F12) → Network tab"
echo "Then subscribe to a plan and tell me:"
echo ""
echo "1. What URL does it call? (should be /api/v1/subscriptions/checkout)"
echo "2. What's the status code? (200, 40x, 50x?)"
echo "3. What's the response? (copy the JSON)"
echo ""
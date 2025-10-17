#!/bin/bash
# Check if data is in readme_to_recover database

echo "=========================================="
echo "🔍 Checking readme_to_recover Database"
echo "=========================================="
echo ""

echo "This database might be your actual data. Let's check..."
echo ""

# Check tables in readme_to_recover
echo "Tables in readme_to_recover:"
docker exec -i $(docker ps -qf "name=postgres") psql -U postgres -d readme_to_recover -c "\dt" 2>&1

echo ""
echo "Checking for users table:"
docker exec -i $(docker ps -qf "name=postgres") psql -U postgres -d readme_to_recover -c "SELECT COUNT(*) as user_count FROM users;" 2>&1

echo ""
echo "Checking for subscriptions:"
docker exec -i $(docker ps -qf "name=postgres") psql -U postgres -d readme_to_recover -c "SELECT email, plan_type FROM subscriptions s JOIN users u ON u.id = s.user_id LIMIT 3;" 2>&1

echo ""
echo "=========================================="
echo "📊 Analysis"
echo "=========================================="
echo ""
echo "If you see data above (joy999@yopmail.com, etc.),"
echo "then your DATABASE_URL in .env is pointing to the wrong database!"
echo ""
echo "Check: grep DATABASE_URL /opt/llmready/backend/.env"
echo "=========================================="
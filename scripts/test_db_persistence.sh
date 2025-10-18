#!/bin/bash
# Test if database persists after Docker restart

echo "=========================================="
echo "🧪 DATABASE PERSISTENCE TEST"
echo "=========================================="
echo ""

cd /opt/llmready

echo "Step 1: Checking current database state..."
echo ""
docker exec -i $(docker ps -qf "name=postgres") psql -U postgres -c "\l" | grep llmready

echo ""
echo "Step 2: Counting records in database..."
if docker exec -i $(docker ps -qf "name=postgres") psql -U postgres -d llmready_prod -c "SELECT COUNT(*) as user_count FROM users;" 2>/dev/null; then
    echo "✅ llmready_prod exists and has tables"
    BEFORE_COUNT=$(docker exec -i $(docker ps -qf "name=postgres") psql -U postgres -d llmready_prod -t -c "SELECT COUNT(*) FROM users;")
    echo "Users before restart: $BEFORE_COUNT"
else
    echo "❌ llmready_prod doesn't exist or has no tables"
    exit 1
fi

echo ""
echo "Step 3: Restarting PostgreSQL container..."
echo "⚠️  This will restart the database container!"
read -p "Press Enter to continue..."

docker restart $(docker ps -qf "name=postgres")

echo ""
echo "Step 4: Waiting for PostgreSQL to start..."
sleep 10

echo ""
echo "Step 5: Checking if database still exists..."
docker exec -i $(docker ps -qf "name=postgres") psql -U postgres -c "\l" | grep llmready

echo ""
echo "Step 6: Checking if data persisted..."
if docker exec -i $(docker ps -qf "name=postgres") psql -U postgres -d llmready_prod -c "SELECT COUNT(*) as user_count FROM users;" 2>/dev/null; then
    AFTER_COUNT=$(docker exec -i $(docker ps -qf "name=postgres") psql -U postgres -d llmready_prod -t -c "SELECT COUNT(*) FROM users;")
    echo "Users after restart: $AFTER_COUNT"
    
    if [ "$BEFORE_COUNT" == "$AFTER_COUNT" ]; then
        echo ""
        echo "=========================================="
        echo "✅ SUCCESS - Data Persisted!"
        echo "=========================================="
        echo "Database survived restart with all data intact."
    else
        echo ""
        echo "=========================================="
        echo "⚠️  WARNING - Data Count Changed"
        echo "=========================================="
        echo "Before: $BEFORE_COUNT users"
        echo "After: $AFTER_COUNT users"
    fi
else
    echo ""
    echo "=========================================="
    echo "❌ FAILURE - Database Lost"
    echo "=========================================="
    echo "llmready_prod disappeared after restart!"
    echo ""
    echo "This means POSTGRES_DB in docker-compose.yml is wrong"
    echo "OR the init script isn't working."
fi

echo ""
echo "=========================================="
echo "📊 Current Databases:"
echo "=========================================="
docker exec -i $(docker ps -qf "name=postgres") psql -U postgres -c "\l"
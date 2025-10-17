#!/bin/bash
# STEP 1: Check if database exists

echo "=========================================="
echo "🔍 STEP 1: Database Existence Check"
echo "=========================================="
echo ""

echo "Error says: database 'llmready_prod' does not exist"
echo ""

echo "Checking if PostgreSQL is running..."
echo ""

# Check if postgres container is running
if docker ps | grep -q postgres; then
    echo "✅ PostgreSQL container is running"
    
    echo ""
    echo "Listing all databases:"
    docker exec -i $(docker ps -qf "name=postgres") psql -U postgres -c "\l" | grep llmready || echo "  No llmready databases found"
    
    echo ""
    echo "All databases:"
    docker exec -i $(docker ps -qf "name=postgres") psql -U postgres -c "\l"
    
else
    echo "❌ PostgreSQL container is NOT running"
    echo ""
    echo "Check docker compose:"
    docker ps -a | grep postgres
fi

echo ""
echo "=========================================="
echo "📝 What to do next:"
echo "=========================================="
echo ""
echo "If llmready_prod doesn't exist, we need to create it."
echo "Share the output above and I'll tell you the exact fix."
echo "=========================================="
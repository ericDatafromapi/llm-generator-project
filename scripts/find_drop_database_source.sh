#!/bin/bash
# Find what's executing DROP DATABASE commands

echo "=========================================="
echo "🔍 FINDING DROP DATABASE SOURCE"
echo "=========================================="
echo ""

echo "1️⃣ Checking all scripts for DROP DATABASE..."
echo ""
grep -r "DROP DATABASE\|drop database" /opt/llmready/ --include="*.sh" --include="*.py" 2>/dev/null || echo "  Not found in scripts"

echo ""
echo "2️⃣ Checking systemd services..."
echo ""
for service in $(systemctl list-units --type=service --all | grep llmready | awk '{print $1}'); do
    echo "Checking $service..."
    systemctl cat $service 2>/dev/null | grep -i "drop\|database" || echo "  Clean"
done

echo ""
echo "3️⃣ Checking PostgreSQL container environment..."
echo ""
docker inspect $(docker ps -qf "name=postgres") | grep -A 20 "Env"

echo ""
echo "4️⃣ Checking if there's a init script running..."
echo ""
docker exec -i $(docker ps -qf "name=postgres") ls -la /docker-entrypoint-initdb.d/ 2>/dev/null || echo "  No init scripts"

echo ""
echo "5️⃣ Check PostgreSQL config for any auto-drop settings..."
echo ""
docker exec -i $(docker ps -qf "name=postgres") cat /var/lib/postgresql/data/postgresql.conf 2>/dev/null | grep -i "drop\|delete" || echo "  Nothing suspicious"

echo ""
echo "6️⃣ Looking for backup/restore scripts that might drop..."
echo ""
find /opt/llmready -name "*backup*" -o -name "*restore*" | while read file; do
    if [ -f "$file" ]; then
        echo "Checking: $file"
        grep -n "DROP\|drop.*database" "$file" 2>/dev/null || echo "  Clean"
    fi
done

echo ""
echo "=========================================="
echo "🎯 NEXT STEPS"
echo "=========================================="
echo "Share this output. We need to find what's running"
echo "DROP DATABASE commands at 04:36 and 05:44!"
echo "=========================================="
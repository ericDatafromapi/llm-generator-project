# PostgreSQL Database Access Guide

## Connection Details
- **Host:** localhost
- **Port:** 5432
- **Database:** llmready_dev
- **Username:** postgres
- **Password:** postgres
- **Container:** llmready_postgres

---

## Method 1: Using Docker Exec (Recommended for Quick Access)

### View all tables
```bash
docker exec -it llmready_postgres psql -U postgres -d llmready_dev -c "\dt"
```

### Describe a specific table structure
```bash
docker exec -it llmready_postgres psql -U postgres -d llmready_dev -c "\d users"
docker exec -it llmready_postgres psql -U postgres -d llmready_dev -c "\d websites"
docker exec -it llmready_postgres psql -U postgres -d llmready_dev -c "\d subscriptions"
```

### Interactive psql session
```bash
docker exec -it llmready_postgres psql -U postgres -d llmready_dev
```

Once inside, you can use:
- `\dt` - List all tables
- `\d table_name` - Describe table structure
- `\l` - List all databases
- `\q` - Quit
- Any SQL query (e.g., `SELECT * FROM users;`)

---

## Method 2: Using psql from Your Local Machine

If you have PostgreSQL client installed locally:

```bash
psql -h localhost -p 5432 -U postgres -d llmready_dev
```

When prompted, enter password: `postgres`

---

## Method 3: Using Python (for programmatic access)

Create a simple script to query the database:

```python
import psycopg2

# Connect to database
conn = psycopg2.connect(
    host="localhost",
    port=5432,
    database="llmready_dev",
    user="postgres",
    password="postgres"
)

# Create cursor
cur = conn.cursor()

# List all tables
cur.execute("""
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema = 'public'
""")
print("Tables:", cur.fetchall())

# Query users
cur.execute("SELECT id, email, full_name, is_active FROM users")
users = cur.fetchall()
for user in users:
    print(user)

# Close connection
cur.close()
conn.close()
```

---

## Method 4: Using DBeaver or pgAdmin (GUI Tools)

### DBeaver (Recommended)
1. Download from https://dbeaver.io/
2. Create new connection
3. Enter connection details:
   - Host: localhost
   - Port: 5432
   - Database: llmready_dev
   - Username: postgres
   - Password: postgres

### pgAdmin
1. Download from https://www.pgadmin.org/
2. Add new server with the same credentials

---

## Useful SQL Queries

### Count records in each table
```sql
SELECT 
    'users' as table_name, COUNT(*) as count FROM users
UNION ALL
SELECT 'websites', COUNT(*) FROM websites
UNION ALL
SELECT 'subscriptions', COUNT(*) FROM subscriptions
UNION ALL
SELECT 'generations', COUNT(*) FROM generations;
```

### View all users
```sql
SELECT id, email, full_name, role, is_active, is_verified, created_at 
FROM users 
ORDER BY created_at DESC;
```

### View all websites
```sql
SELECT id, url, user_id, status, created_at 
FROM websites 
ORDER BY created_at DESC;
```

### View user with their websites
```sql
SELECT 
    u.email, 
    u.full_name,
    w.url,
    w.status,
    w.created_at
FROM users u
LEFT JOIN websites w ON u.id = w.user_id
ORDER BY u.created_at DESC;
```

### Check database size
```sql
SELECT 
    pg_database.datname,
    pg_size_pretty(pg_database_size(pg_database.datname)) AS size
FROM pg_database
WHERE datname = 'llmready_dev';
```

---

## Current Database Schema

Your database currently has these tables:

1. **alembic_version** - Tracks database migrations
2. **email_verification_tokens** - Email verification tokens
3. **generations** - LLM generation records
4. **password_reset_tokens** - Password reset tokens
5. **subscriptions** - User subscription data
6. **users** - User accounts
7. **websites** - Website records

---

## Troubleshooting

### Container not running?
```bash
docker-compose up -d postgres
```

### Check container logs
```bash
docker logs llmready_postgres
```

### Check if PostgreSQL is accepting connections
```bash
docker exec -it llmready_postgres pg_isready -U postgres
```

### Restart PostgreSQL container
```bash
docker-compose restart postgres
```

---

## Quick Reference Commands

```bash
# List all tables
docker exec -it llmready_postgres psql -U postgres -d llmready_dev -c "\dt"

# Interactive session
docker exec -it llmready_postgres psql -U postgres -d llmready_dev

# Execute SQL file
docker exec -i llmready_postgres psql -U postgres -d llmready_dev < query.sql

# Backup database
docker exec -t llmready_postgres pg_dump -U postgres llmready_dev > backup.sql

# Restore database
docker exec -i llmready_postgres psql -U postgres -d llmready_dev < backup.sql
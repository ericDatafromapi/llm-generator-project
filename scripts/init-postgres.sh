#!/bin/bash
# PostgreSQL initialization script
# Creates both dev and prod databases for flexibility

set -e

# Function to create database if it doesn't exist
create_db_if_not_exists() {
    local db_name=$1
    psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
        SELECT 'CREATE DATABASE $db_name'
        WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '$db_name')\gexec
EOSQL
    echo "✅ Database $db_name ready"
}

echo "Initializing PostgreSQL databases..."

# Create both databases
create_db_if_not_exists "llmready_dev"
create_db_if_not_exists "llmready_prod"

echo "✅ PostgreSQL initialization complete"
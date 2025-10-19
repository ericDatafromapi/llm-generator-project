#!/bin/bash
# PostgreSQL initialization script - FIXED VERSION
# Creates both dev and prod databases

set -e

echo "Initializing PostgreSQL databases..."

# Create llmready_dev if doesn't exist
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
    SELECT 'CREATE DATABASE llmready_dev'
    WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'llmready_dev')\gexec
EOSQL

# Create llmready_prod if doesn't exist  
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
    SELECT 'CREATE DATABASE llmready_prod'
    WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'llmready_prod')\gexec
EOSQL

echo "✅ PostgreSQL initialization complete - both databases ready"
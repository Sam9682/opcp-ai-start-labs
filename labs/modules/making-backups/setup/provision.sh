#!/bin/bash
# Provision script for Making Backups lab module.
#
# Sets up the environment needed for backup exercises:
# - Ensures PostgreSQL client tools are available
# - Creates a sample database with test data
# - Creates backup directories
# - Installs required Python packages (boto3)
# - Verifies cron service availability

set -e

echo "=== Making Backups Lab - Environment Provisioning ==="

# Configuration
DB_NAME="${LAB_DB_NAME:-ai_store_lab_db}"
DB_USER="${LAB_DB_USER:-postgres}"
DB_HOST="${LAB_DB_HOST:-localhost}"
DB_PORT="${LAB_DB_PORT:-5432}"
BACKUP_DIR="/tmp/backups"
SCHEDULED_BACKUP_DIR="/tmp/backups/scheduled"

# Step 1: Verify PostgreSQL client tools
echo "[1/6] Checking PostgreSQL client tools..."
if ! command -v pg_dump &> /dev/null; then
    echo "ERROR: pg_dump not found. Installing postgresql-client..."
    apt-get update -qq && apt-get install -y -qq postgresql-client
fi

if ! command -v pg_restore &> /dev/null; then
    echo "ERROR: pg_restore not found."
    exit 1
fi

echo "  pg_dump: $(which pg_dump)"
echo "  pg_restore: $(which pg_restore)"
echo "  psql: $(which psql)"

# Step 2: Verify PostgreSQL connectivity
echo "[2/6] Verifying PostgreSQL connectivity..."
if pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" &> /dev/null; then
    echo "  PostgreSQL is ready at ${DB_HOST}:${DB_PORT}"
else
    echo "WARNING: PostgreSQL is not responding at ${DB_HOST}:${DB_PORT}"
    echo "  Exercises requiring database access may fail."
fi

# Step 3: Create sample database with test data
echo "[3/6] Creating sample database '${DB_NAME}' with test data..."
if command -v createdb &> /dev/null; then
    dropdb --if-exists -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" "$DB_NAME" 2>/dev/null || true
    createdb -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" "$DB_NAME" 2>/dev/null || {
        echo "WARNING: Could not create database. Database may already exist or credentials insufficient."
    }

    # Create sample tables and data
    psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -q <<EOF 2>/dev/null || true
CREATE TABLE IF NOT EXISTS applications (
    id SERIAL PRIMARY KEY,
    name VARCHAR(64) NOT NULL,
    description TEXT,
    git_url TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS deployments (
    id SERIAL PRIMARY KEY,
    app_id INTEGER REFERENCES applications(id),
    status VARCHAR(20) DEFAULT 'stopped',
    started_at TIMESTAMP,
    stopped_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS backup_history (
    id SERIAL PRIMARY KEY,
    db_name VARCHAR(64) NOT NULL,
    backup_path TEXT NOT NULL,
    file_size_bytes BIGINT,
    created_at TIMESTAMP DEFAULT NOW(),
    status VARCHAR(20) DEFAULT 'completed'
);

INSERT INTO applications (name, description, git_url)
VALUES
    ('web-store', 'Main web store application', 'https://git.example.com/web-store'),
    ('api-gateway', 'API gateway service', 'https://git.example.com/api-gateway'),
    ('ml-recommender', 'ML recommendation engine', 'https://git.example.com/ml-recommender')
ON CONFLICT DO NOTHING;

INSERT INTO deployments (app_id, status, started_at)
VALUES
    (1, 'running', NOW() - INTERVAL '2 days'),
    (2, 'running', NOW() - INTERVAL '1 day'),
    (3, 'stopped', NULL)
ON CONFLICT DO NOTHING;
EOF
    echo "  Sample database created with test data."
else
    echo "WARNING: createdb not available. Skipping sample database creation."
fi

# Step 4: Create backup directories
echo "[4/6] Creating backup directories..."
mkdir -p "$BACKUP_DIR"
mkdir -p "$SCHEDULED_BACKUP_DIR"
chmod 777 "$BACKUP_DIR"
chmod 777 "$SCHEDULED_BACKUP_DIR"
echo "  Created: $BACKUP_DIR"
echo "  Created: $SCHEDULED_BACKUP_DIR"

# Step 5: Install Python dependencies
echo "[5/6] Checking Python dependencies..."
if command -v pip &> /dev/null; then
    pip install -q boto3 2>/dev/null || echo "WARNING: Failed to install boto3"
else
    echo "WARNING: pip not available. boto3 may not be installed."
fi

# Step 6: Verify cron service
echo "[6/6] Checking cron service..."
if command -v crontab &> /dev/null; then
    echo "  crontab: $(which crontab)"
    # Ensure crond is running (if in container)
    if command -v service &> /dev/null; then
        service cron start 2>/dev/null || true
    fi
else
    echo "WARNING: crontab not available. Scheduling exercises may fail."
fi

echo ""
echo "=== Provisioning Complete ==="
echo "Database: ${DB_NAME} at ${DB_HOST}:${DB_PORT}"
echo "Backup directory: ${BACKUP_DIR}"
echo "Scheduled backups: ${SCHEDULED_BACKUP_DIR}"
echo ""
echo "Set PGPASSWORD environment variable before running exercises:"
echo "  export PGPASSWORD='your_password'"

#!/bin/bash
# Teardown script for Making Backups lab module.
#
# Cleans up resources created during the backup exercises:
# - Removes backup files and directories
# - Drops test databases
# - Removes cron entries created by exercises
# - Drops the sample database

set -e

echo "=== Making Backups Lab - Environment Teardown ==="

# Configuration
DB_NAME="${LAB_DB_NAME:-ai_store_lab_db}"
TEST_DB_NAME="backup_test_db"
DB_USER="${LAB_DB_USER:-postgres}"
DB_HOST="${LAB_DB_HOST:-localhost}"
DB_PORT="${LAB_DB_PORT:-5432}"
BACKUP_DIR="/tmp/backups"

# Step 1: Remove cron entries
echo "[1/4] Removing lab cron entries..."
if command -v crontab &> /dev/null; then
    CURRENT_CRONTAB=$(crontab -l 2>/dev/null || echo "")
    if echo "$CURRENT_CRONTAB" | grep -q "ai-store-backup"; then
        echo "$CURRENT_CRONTAB" | grep -v "ai-store-backup" | crontab - 2>/dev/null || true
        echo "  Removed ai-store-backup cron entries."
    else
        echo "  No lab cron entries found."
    fi
else
    echo "  crontab not available, skipping."
fi

# Step 2: Drop test databases
echo "[2/4] Dropping test databases..."
if command -v dropdb &> /dev/null; then
    dropdb --if-exists -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" "$TEST_DB_NAME" 2>/dev/null || true
    echo "  Dropped: $TEST_DB_NAME"

    dropdb --if-exists -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" "$DB_NAME" 2>/dev/null || true
    echo "  Dropped: $DB_NAME"
else
    echo "  dropdb not available, skipping."
fi

# Step 3: Remove backup files
echo "[3/4] Removing backup files..."
if [ -d "$BACKUP_DIR" ]; then
    rm -rf "$BACKUP_DIR"
    echo "  Removed: $BACKUP_DIR"
else
    echo "  No backup directory found."
fi

# Step 4: Clean up any S3 test objects (informational only)
echo "[4/4] S3 cleanup note..."
echo "  Note: Objects uploaded to S3 during exercises are NOT automatically removed."
echo "  To clean up manually: aws s3 rm s3://ai-store-backups/backups/ --recursive"

echo ""
echo "=== Teardown Complete ==="

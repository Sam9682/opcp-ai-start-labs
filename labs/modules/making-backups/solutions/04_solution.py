"""Reference solution for Exercise 4: Verify Backup Integrity.

This solution demonstrates restoring a backup to a test database
and verifying its integrity.
"""


def get_solution_submission() -> dict:
    """Return the reference submission for this exercise.

    Returns:
        A dict with the correct submission parameters.
    """
    return {
        "backup_path": "/tmp/backups/ai_store_db.dump",
        "test_db_name": "backup_test_db",
        "format": "custom",
        "host": "localhost",
        "port": 5432,
        "username": "postgres",
    }


def get_explanation() -> str:
    """Return a detailed explanation of the solution approach."""
    return """
Solution: Verify Backup Integrity
====================================

1. Create a test database for restoration:
   $ createdb -h localhost -p 5432 -U postgres backup_test_db

2. Restore the backup:
   For custom format:
   $ pg_restore -h localhost -p 5432 -U postgres -d backup_test_db /tmp/backups/ai_store_db.dump

   For plain SQL format:
   $ psql -h localhost -p 5432 -U postgres -d backup_test_db -f /tmp/backups/ai_store_db.sql

3. Verify tables were restored:
   $ psql -h localhost -p 5432 -U postgres -d backup_test_db -c "\\dt"

4. Verify row counts match expectations:
   $ psql -h localhost -p 5432 -U postgres -d backup_test_db \\
       -c "SELECT schemaname, tablename FROM pg_tables WHERE schemaname = 'public';"

5. Clean up the test database:
   $ dropdb -h localhost -p 5432 -U postgres backup_test_db

Key points:
- Always restore to a SEPARATE test database, never to production
- Use --if-exists with dropdb for safety
- pg_restore exit code 0 means success, 1 may indicate non-fatal warnings
- Count tables to confirm the schema was restored
- For full verification, compare row counts with the source database
- Check for permission errors that indicate credential issues

Automated integrity check script:

   #!/bin/bash
   TEST_DB="backup_test_db"
   BACKUP_FILE="$1"

   dropdb --if-exists -U postgres "$TEST_DB"
   createdb -U postgres "$TEST_DB"
   pg_restore -U postgres -d "$TEST_DB" "$BACKUP_FILE"

   TABLE_COUNT=$(psql -U postgres -d "$TEST_DB" -t -c \\
       "SELECT count(*) FROM information_schema.tables WHERE table_schema='public';")

   if [ "$TABLE_COUNT" -gt 0 ]; then
       echo "PASS: Restored $TABLE_COUNT tables"
   else
       echo "FAIL: No tables found after restore"
       exit 1
   fi

   dropdb -U postgres "$TEST_DB"
"""

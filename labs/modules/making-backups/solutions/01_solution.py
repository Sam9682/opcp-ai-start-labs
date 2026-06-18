"""Reference solution for Exercise 1: PostgreSQL Backup with pg_dump.

This solution demonstrates how to create a proper database backup
using pg_dump in custom format.
"""


def get_solution_submission() -> dict:
    """Return the reference submission for this exercise.

    Returns:
        A dict with the correct submission parameters.
    """
    return {
        "db_name": "ai_store_db",
        "backup_path": "/tmp/backups/ai_store_db.dump",
        "format": "custom",
        "host": "localhost",
        "port": 5432,
        "username": "postgres",
    }


def get_explanation() -> str:
    """Return a detailed explanation of the solution approach."""
    return """
Solution: PostgreSQL Backup with pg_dump
=========================================

1. Use pg_dump with the -Fc flag for custom (binary) format:
   $ pg_dump -h localhost -p 5432 -U postgres -Fc -f /tmp/backups/ai_store_db.dump ai_store_db

2. Alternatively, use plain SQL format with -Fp:
   $ pg_dump -h localhost -p 5432 -U postgres -Fp -f /tmp/backups/ai_store_db.sql ai_store_db

Key points:
- Custom format (-Fc) is recommended because:
  - It's compressed by default
  - Supports selective restore (individual tables)
  - Compatible with pg_restore's parallel restore feature
- Plain format (-Fp) produces readable SQL but is larger
- Always verify the backup file is > 0 bytes after creation
- Set PGPASSWORD env var or use ~/.pgpass for authentication

Environment setup:
  export PGPASSWORD='your_password'
"""

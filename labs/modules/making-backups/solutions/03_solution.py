"""Reference solution for Exercise 3: Schedule Automated Backups.

This solution demonstrates setting up a cron job for automated
periodic database backups.
"""


def get_solution_submission() -> dict:
    """Return the reference submission for this exercise.

    Returns:
        A dict with the correct submission parameters.
    """
    return {
        "cron_schedule": "0 2 * * *",
        "backup_script": "/opt/ai-store/scripts/backup_db.sh",
        "backup_dir": "/var/backups/ai-store",
        "db_name": "ai_store_db",
        "cron_comment": "ai-store-backup",
    }


def get_explanation() -> str:
    """Return a detailed explanation of the solution approach."""
    return """
Solution: Schedule Automated Backups
======================================

1. Create a backup script (/opt/ai-store/scripts/backup_db.sh):

   #!/bin/bash
   DB_NAME="$1"
   BACKUP_DIR="$2"
   TIMESTAMP=$(date +%Y%m%d_%H%M%S)
   BACKUP_FILE="${BACKUP_DIR}/${DB_NAME}_${TIMESTAMP}.dump"

   export PGPASSWORD="${PGPASSWORD:-}"

   pg_dump -h localhost -p 5432 -U postgres -Fc -f "$BACKUP_FILE" "$DB_NAME"

   if [ $? -eq 0 ] && [ -s "$BACKUP_FILE" ]; then
       echo "Backup successful: $BACKUP_FILE"
   else
       echo "Backup failed!" >&2
       exit 1
   fi

   # Optional: remove backups older than 7 days
   find "$BACKUP_DIR" -name "*.dump" -mtime +7 -delete

2. Make the script executable:
   $ chmod +x /opt/ai-store/scripts/backup_db.sh

3. Register the cron job:
   $ crontab -e
   # Add: 0 2 * * * /opt/ai-store/scripts/backup_db.sh ai_store_db /var/backups/ai-store # ai-store-backup

Key points:
- '0 2 * * *' runs daily at 2:00 AM
- Include a comment for easy identification of backup cron entries
- Add log rotation or cleanup to prevent disk space exhaustion
- Consider using a lock file to prevent overlapping backup runs
- Verify with: crontab -l | grep ai-store-backup

Common schedules:
- Every hour:    0 * * * *
- Every 6 hours: 0 */6 * * *
- Daily at 2 AM: 0 2 * * *
- Weekly Sunday:  0 2 * * 0
"""

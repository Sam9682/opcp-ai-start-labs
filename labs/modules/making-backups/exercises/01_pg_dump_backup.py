"""Exercise 1: PostgreSQL Backup with pg_dump.

The learner creates a database backup using pg_dump in custom format
or plain SQL format, producing a backup file greater than 0 bytes.

Validates: Requirement 9.1 (pg_dump backup), Requirement 9.2 (file > 0 bytes, restorable format)
"""

import os
import subprocess
from pathlib import Path

from labs.templates.exercise_base import Exercise


class PgDumpBackupExercise(Exercise):
    """Create a PostgreSQL database backup using pg_dump."""

    @property
    def exercise_id(self) -> str:
        return "01_pg_dump_backup"

    @property
    def name(self) -> str:
        return "PostgreSQL Backup with pg_dump"

    @property
    def description(self) -> str:
        return (
            "Create a database backup using pg_dump in custom format or plain SQL format. "
            "The backup file must be greater than 0 bytes and in a restorable format."
        )

    @property
    def timeout_minutes(self) -> int:
        return 15

    def setup(self) -> None:
        """Ensure PostgreSQL is accessible and backup directory exists."""
        backup_dir = Path("/tmp/backups")
        backup_dir.mkdir(parents=True, exist_ok=True)

    def execute(self, submission: dict) -> dict:
        """Execute pg_dump to create a database backup.

        Expected submission keys:
            - db_name (str): Name of the database to back up.
            - backup_path (str): Destination file path for the backup.
            - format (str): Backup format - 'custom' or 'plain'.
            - host (str, optional): PostgreSQL host. Defaults to 'localhost'.
            - port (int, optional): PostgreSQL port. Defaults to 5432.
            - username (str, optional): PostgreSQL username.

        Returns:
            dict with keys:
                - backup_path (str): Path to the created backup file.
                - file_size_bytes (int): Size of the backup file.
                - format (str): Format used ('custom' or 'plain').
                - command (str): The pg_dump command that was executed.
                - returncode (int): Process return code.
                - stderr (str): Any error output.
        """
        db_name = submission.get("db_name", "")
        backup_path = submission.get("backup_path", "/tmp/backups/backup.dump")
        backup_format = submission.get("format", "custom")
        host = submission.get("host", "localhost")
        port = submission.get("port", 5432)
        username = submission.get("username", "postgres")

        # Build pg_dump command
        cmd = ["pg_dump", "-h", str(host), "-p", str(port), "-U", username]

        if backup_format == "custom":
            cmd.extend(["-Fc", "-f", backup_path])
        elif backup_format == "plain":
            cmd.extend(["-Fp", "-f", backup_path])
        else:
            return {
                "backup_path": backup_path,
                "file_size_bytes": 0,
                "format": backup_format,
                "command": " ".join(cmd),
                "returncode": 1,
                "stderr": f"Invalid format '{backup_format}'. Use 'custom' or 'plain'.",
            }

        cmd.append(db_name)

        # Execute pg_dump
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,
                env={**os.environ, "PGPASSWORD": os.environ.get("PGPASSWORD", "")},
            )
            file_size = Path(backup_path).stat().st_size if Path(backup_path).exists() else 0
        except subprocess.TimeoutExpired:
            return {
                "backup_path": backup_path,
                "file_size_bytes": 0,
                "format": backup_format,
                "command": " ".join(cmd),
                "returncode": -1,
                "stderr": "pg_dump timed out after 300 seconds.",
            }
        except FileNotFoundError:
            return {
                "backup_path": backup_path,
                "file_size_bytes": 0,
                "format": backup_format,
                "command": " ".join(cmd),
                "returncode": -1,
                "stderr": "pg_dump command not found. Ensure PostgreSQL client tools are installed.",
            }

        return {
            "backup_path": backup_path,
            "file_size_bytes": file_size,
            "format": backup_format,
            "command": " ".join(cmd),
            "returncode": result.returncode,
            "stderr": result.stderr,
        }

    def validate(self, result: dict) -> list[dict]:
        """Validate the pg_dump backup result.

        Checks:
        1. pg_dump exited with code 0
        2. Backup file exists and is greater than 0 bytes
        3. Backup format is valid (custom or plain)
        """
        checks = []

        # Check 1: pg_dump exit code
        returncode = result.get("returncode", -1)
        checks.append({
            "name": "pg_dump_exit_code",
            "passed": returncode == 0,
            "feedback": (
                "pg_dump completed successfully."
                if returncode == 0
                else f"pg_dump failed with exit code {returncode}: {result.get('stderr', '')}"
            ),
            "expected": "0",
            "actual": str(returncode),
        })

        # Check 2: Backup file size > 0 bytes
        file_size = result.get("file_size_bytes", 0)
        checks.append({
            "name": "backup_file_size",
            "passed": file_size > 0,
            "feedback": (
                f"Backup file created successfully ({file_size} bytes)."
                if file_size > 0
                else "Backup file is empty or does not exist."
            ),
            "expected": "> 0 bytes",
            "actual": f"{file_size} bytes",
        })

        # Check 3: Valid backup format
        backup_format = result.get("format", "")
        valid_formats = ("custom", "plain")
        checks.append({
            "name": "backup_format_valid",
            "passed": backup_format in valid_formats,
            "feedback": (
                f"Backup format '{backup_format}' is valid and restorable."
                if backup_format in valid_formats
                else f"Invalid backup format '{backup_format}'. Use 'custom' or 'plain'."
            ),
            "expected": "custom or plain",
            "actual": backup_format,
        })

        return checks

    def teardown(self) -> None:
        """Clean up is handled by the integrity verification exercise."""
        pass

    def get_hints(self) -> list[str]:
        return [
            "Use 'pg_dump -Fc' for custom format (recommended for pg_restore).",
            "Use 'pg_dump -Fp' for plain SQL format (readable but larger).",
            "Make sure the PGPASSWORD environment variable is set or use a .pgpass file.",
            "The backup file path should be writable by the current user.",
        ]

    def get_instructions(self) -> str:
        return (
            "Create a PostgreSQL database backup using pg_dump.\n\n"
            "Submit with:\n"
            "  - db_name: The name of the database to back up\n"
            "  - backup_path: Where to save the backup file\n"
            "  - format: 'custom' (binary, use pg_restore) or 'plain' (SQL text, use psql)\n"
            "  - host: PostgreSQL host (default: localhost)\n"
            "  - port: PostgreSQL port (default: 5432)\n"
            "  - username: PostgreSQL username (default: postgres)\n\n"
            "The backup file must be greater than 0 bytes to pass validation."
        )

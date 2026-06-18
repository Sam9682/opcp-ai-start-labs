"""Exercise 4: Verify Backup Integrity.

The learner restores a backup to a test database to confirm the backup
is complete, restorable, and contains expected data.

Validates: Requirement 9.1 (integrity verification), Requirement 9.2 (restorable format)
"""

import os
import subprocess
from pathlib import Path

from labs.templates.exercise_base import Exercise


class VerifyIntegrityExercise(Exercise):
    """Restore a backup to a test database to verify integrity."""

    @property
    def exercise_id(self) -> str:
        return "04_verify_integrity"

    @property
    def name(self) -> str:
        return "Verify Backup Integrity"

    @property
    def description(self) -> str:
        return (
            "Restore a database backup to a test database to verify it is "
            "complete, uncorrupted, and contains the expected data."
        )

    @property
    def timeout_minutes(self) -> int:
        return 20

    @property
    def prerequisites(self) -> list[str]:
        return ["01_pg_dump_backup"]

    def setup(self) -> None:
        """Ensure a test database target is available."""
        pass

    def execute(self, submission: dict) -> dict:
        """Restore a backup file to a test database and verify integrity.

        Expected submission keys:
            - backup_path (str): Path to the backup file to restore.
            - test_db_name (str): Name of the test database for restoration.
            - format (str): Backup format - 'custom' or 'plain'.
            - host (str, optional): PostgreSQL host. Defaults to 'localhost'.
            - port (int, optional): PostgreSQL port. Defaults to 5432.
            - username (str, optional): PostgreSQL username.

        Returns:
            dict with keys:
                - restored (bool): Whether the restore completed without errors.
                - backup_path (str): Path to the backup file.
                - test_db_name (str): Test database name.
                - format (str): Backup format used.
                - restore_command (str): The restore command executed.
                - returncode (int): Process return code.
                - stdout (str): Restore output.
                - stderr (str): Any error output.
                - table_count (int): Number of tables in restored database.
                - permission_error (str): Specific permission issue if applicable.
        """
        backup_path = submission.get("backup_path", "")
        test_db_name = submission.get("test_db_name", "backup_test_db")
        backup_format = submission.get("format", "custom")
        host = submission.get("host", "localhost")
        port = submission.get("port", 5432)
        username = submission.get("username", "postgres")

        # Validate backup file
        if not Path(backup_path).exists():
            return {
                "restored": False,
                "backup_path": backup_path,
                "test_db_name": test_db_name,
                "format": backup_format,
                "restore_command": "",
                "returncode": -1,
                "stdout": "",
                "stderr": f"Backup file not found: {backup_path}",
                "table_count": 0,
                "permission_error": "",
            }

        file_size = Path(backup_path).stat().st_size
        if file_size == 0:
            return {
                "restored": False,
                "backup_path": backup_path,
                "test_db_name": test_db_name,
                "format": backup_format,
                "restore_command": "",
                "returncode": -1,
                "stdout": "",
                "stderr": "Backup file is empty (0 bytes).",
                "table_count": 0,
                "permission_error": "",
            }

        pg_env = {**os.environ, "PGPASSWORD": os.environ.get("PGPASSWORD", "")}
        conn_args = ["-h", str(host), "-p", str(port), "-U", username]

        # Create test database (drop if exists)
        try:
            subprocess.run(
                ["dropdb", "--if-exists"] + conn_args + [test_db_name],
                capture_output=True,
                text=True,
                timeout=30,
                env=pg_env,
            )
            create_result = subprocess.run(
                ["createdb"] + conn_args + [test_db_name],
                capture_output=True,
                text=True,
                timeout=30,
                env=pg_env,
            )
            if create_result.returncode != 0:
                # Check for permission errors
                stderr = create_result.stderr
                permission_error = ""
                if "permission denied" in stderr.lower() or "FATAL" in stderr:
                    permission_error = (
                        f"Permission denied creating test database. "
                        f"Required: CREATE DATABASE privilege for user '{username}'."
                    )
                return {
                    "restored": False,
                    "backup_path": backup_path,
                    "test_db_name": test_db_name,
                    "format": backup_format,
                    "restore_command": f"createdb {' '.join(conn_args)} {test_db_name}",
                    "returncode": create_result.returncode,
                    "stdout": create_result.stdout,
                    "stderr": stderr,
                    "table_count": 0,
                    "permission_error": permission_error,
                }
        except FileNotFoundError:
            return {
                "restored": False,
                "backup_path": backup_path,
                "test_db_name": test_db_name,
                "format": backup_format,
                "restore_command": "",
                "returncode": -1,
                "stdout": "",
                "stderr": "PostgreSQL client tools (createdb/dropdb) not found.",
                "table_count": 0,
                "permission_error": "",
            }
        except subprocess.TimeoutExpired:
            return {
                "restored": False,
                "backup_path": backup_path,
                "test_db_name": test_db_name,
                "format": backup_format,
                "restore_command": "",
                "returncode": -1,
                "stdout": "",
                "stderr": "Database creation timed out.",
                "table_count": 0,
                "permission_error": "",
            }

        # Restore the backup
        if backup_format == "custom":
            restore_cmd = ["pg_restore"] + conn_args + ["-d", test_db_name, backup_path]
        elif backup_format == "plain":
            restore_cmd = ["psql"] + conn_args + ["-d", test_db_name, "-f", backup_path]
        else:
            return {
                "restored": False,
                "backup_path": backup_path,
                "test_db_name": test_db_name,
                "format": backup_format,
                "restore_command": "",
                "returncode": -1,
                "stdout": "",
                "stderr": f"Invalid format '{backup_format}'. Use 'custom' or 'plain'.",
                "table_count": 0,
                "permission_error": "",
            }

        try:
            restore_result = subprocess.run(
                restore_cmd,
                capture_output=True,
                text=True,
                timeout=300,
                env=pg_env,
            )
        except subprocess.TimeoutExpired:
            return {
                "restored": False,
                "backup_path": backup_path,
                "test_db_name": test_db_name,
                "format": backup_format,
                "restore_command": " ".join(restore_cmd),
                "returncode": -1,
                "stdout": "",
                "stderr": "Restore operation timed out after 300 seconds.",
                "table_count": 0,
                "permission_error": "",
            }
        except FileNotFoundError:
            return {
                "restored": False,
                "backup_path": backup_path,
                "test_db_name": test_db_name,
                "format": backup_format,
                "restore_command": " ".join(restore_cmd),
                "returncode": -1,
                "stdout": "",
                "stderr": "pg_restore/psql command not found.",
                "table_count": 0,
                "permission_error": "",
            }

        # Check permission errors in restore output
        permission_error = ""
        if "permission denied" in restore_result.stderr.lower():
            permission_error = (
                f"Permission denied during restore. "
                f"Required: appropriate privileges for user '{username}' on database '{test_db_name}'."
            )

        # Count tables in restored database
        table_count = 0
        try:
            count_cmd = [
                "psql"
            ] + conn_args + [
                "-d", test_db_name,
                "-t", "-c",
                "SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public';",
            ]
            count_result = subprocess.run(
                count_cmd,
                capture_output=True,
                text=True,
                timeout=10,
                env=pg_env,
            )
            if count_result.returncode == 0:
                table_count = int(count_result.stdout.strip())
        except (subprocess.TimeoutExpired, ValueError, FileNotFoundError):
            pass

        # pg_restore returns 0 on success, or possibly warnings
        restored = restore_result.returncode == 0
        # For pg_restore, exit code 1 with only warnings is still acceptable
        if not restored and backup_format == "custom":
            # pg_restore may exit with 1 for non-fatal warnings
            if "error" not in restore_result.stderr.lower():
                restored = True

        return {
            "restored": restored,
            "backup_path": backup_path,
            "test_db_name": test_db_name,
            "format": backup_format,
            "restore_command": " ".join(restore_cmd),
            "returncode": restore_result.returncode,
            "stdout": restore_result.stdout,
            "stderr": restore_result.stderr,
            "table_count": table_count,
            "permission_error": permission_error,
        }

    def validate(self, result: dict) -> list[dict]:
        """Validate backup integrity through restoration.

        Checks:
        1. Restore completed without critical errors
        2. At least one table exists in the restored database
        3. No permission errors encountered
        """
        checks = []

        # Check 1: Restore success
        restored = result.get("restored", False)
        checks.append({
            "name": "restore_success",
            "passed": restored,
            "feedback": (
                "Backup restored to test database without errors."
                if restored
                else f"Restore failed: {result.get('stderr', 'Unknown error')}"
            ),
            "expected": "restored=True (exit code 0)",
            "actual": f"restored={restored} (exit code {result.get('returncode', -1)})",
        })

        # Check 2: Tables present in restored database
        table_count = result.get("table_count", 0)
        checks.append({
            "name": "tables_present",
            "passed": table_count > 0,
            "feedback": (
                f"Restored database contains {table_count} table(s)."
                if table_count > 0
                else "No tables found in restored database. Backup may be empty or corrupted."
            ),
            "expected": "> 0 tables",
            "actual": f"{table_count} tables",
        })

        # Check 3: No permission errors
        permission_error = result.get("permission_error", "")
        checks.append({
            "name": "no_permission_errors",
            "passed": not permission_error,
            "feedback": (
                "No permission issues encountered during restore."
                if not permission_error
                else permission_error
            ),
            "expected": "no permission errors",
            "actual": permission_error if permission_error else "none",
        })

        return checks

    def teardown(self) -> None:
        """Drop the test database."""
        test_db_name = "backup_test_db"
        try:
            subprocess.run(
                ["dropdb", "--if-exists", "-h", "localhost", "-p", "5432",
                 "-U", "postgres", test_db_name],
                capture_output=True,
                text=True,
                timeout=30,
                env={**os.environ, "PGPASSWORD": os.environ.get("PGPASSWORD", "")},
            )
        except Exception:
            pass

    def get_hints(self) -> list[str]:
        return [
            "For custom format backups, use pg_restore to restore.",
            "For plain SQL backups, use psql -f to restore.",
            "The test database must be created before restoration.",
            "Use 'createdb' to create a new test database for restoration.",
            "Check that the PostgreSQL user has CREATE DATABASE privileges.",
        ]

    def get_instructions(self) -> str:
        return (
            "Verify your backup by restoring it to a test database.\n\n"
            "Submit with:\n"
            "  - backup_path: Path to the backup file to restore\n"
            "  - test_db_name: Name for the test database (default: 'backup_test_db')\n"
            "  - format: Backup format - 'custom' (use pg_restore) or 'plain' (use psql)\n"
            "  - host: PostgreSQL host (default: localhost)\n"
            "  - port: PostgreSQL port (default: 5432)\n"
            "  - username: PostgreSQL username (default: postgres)\n\n"
            "The validator will confirm the restore completes without errors and "
            "the restored database contains at least one table."
        )

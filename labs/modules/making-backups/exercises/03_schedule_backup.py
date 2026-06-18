"""Exercise 3: Schedule Automated Backups.

The learner configures a cron job (or equivalent scheduled task) to
automate periodic database backups.

Validates: Requirement 9.1 (scheduling), Requirement 9.5 (cron registration and backup production)
"""

import os
import subprocess
import time
from pathlib import Path

from labs.templates.exercise_base import Exercise


class ScheduleBackupExercise(Exercise):
    """Configure a cron job to automate periodic database backups."""

    @property
    def exercise_id(self) -> str:
        return "03_schedule_backup"

    @property
    def name(self) -> str:
        return "Schedule Automated Backups"

    @property
    def description(self) -> str:
        return (
            "Configure a cron job or equivalent scheduled task to automate "
            "periodic PostgreSQL database backups."
        )

    @property
    def timeout_minutes(self) -> int:
        return 20

    @property
    def prerequisites(self) -> list[str]:
        return ["01_pg_dump_backup"]

    def setup(self) -> None:
        """Ensure cron service is available and backup directory exists."""
        backup_dir = Path("/tmp/backups/scheduled")
        backup_dir.mkdir(parents=True, exist_ok=True)

    def execute(self, submission: dict) -> dict:
        """Register a cron job for automated database backups.

        Expected submission keys:
            - cron_schedule (str): Cron expression (e.g., '0 2 * * *' for daily at 2 AM).
            - backup_script (str): Path to the backup script to execute.
            - backup_dir (str): Directory where backups will be stored.
            - db_name (str): Database name for the backup.
            - cron_comment (str, optional): Comment identifier for the cron entry.

        Returns:
            dict with keys:
                - registered (bool): Whether the cron job was registered.
                - cron_entry (str): The full crontab entry.
                - cron_schedule (str): The schedule expression used.
                - backup_dir (str): Target backup directory.
                - existing_crontab (str): Current crontab contents.
                - error (str): Error message if registration failed.
        """
        cron_schedule = submission.get("cron_schedule", "")
        backup_script = submission.get("backup_script", "")
        backup_dir = submission.get("backup_dir", "/tmp/backups/scheduled")
        db_name = submission.get("db_name", "")
        cron_comment = submission.get("cron_comment", "ai-store-backup")

        if not cron_schedule:
            return {
                "registered": False,
                "cron_entry": "",
                "cron_schedule": cron_schedule,
                "backup_dir": backup_dir,
                "existing_crontab": "",
                "error": "cron_schedule is required (e.g., '0 2 * * *').",
            }

        if not backup_script:
            return {
                "registered": False,
                "cron_entry": "",
                "cron_schedule": cron_schedule,
                "backup_dir": backup_dir,
                "existing_crontab": "",
                "error": "backup_script path is required.",
            }

        # Build the cron entry
        cron_entry = f"{cron_schedule} {backup_script} {db_name} {backup_dir} # {cron_comment}"

        try:
            # Get existing crontab
            existing_result = subprocess.run(
                ["crontab", "-l"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            existing_crontab = existing_result.stdout if existing_result.returncode == 0 else ""

            # Check if entry already exists (by comment identifier)
            if cron_comment in existing_crontab:
                # Remove old entry with same comment
                lines = existing_crontab.strip().split("\n")
                lines = [l for l in lines if cron_comment not in l]
                existing_crontab = "\n".join(lines) + "\n" if lines else ""

            # Append new cron entry
            new_crontab = existing_crontab.rstrip("\n") + "\n" + cron_entry + "\n"

            # Install updated crontab
            install_result = subprocess.run(
                ["crontab", "-"],
                input=new_crontab,
                capture_output=True,
                text=True,
                timeout=10,
            )

            if install_result.returncode != 0:
                return {
                    "registered": False,
                    "cron_entry": cron_entry,
                    "cron_schedule": cron_schedule,
                    "backup_dir": backup_dir,
                    "existing_crontab": existing_crontab,
                    "error": f"Failed to install crontab: {install_result.stderr}",
                }

            # Verify cron entry was registered
            verify_result = subprocess.run(
                ["crontab", "-l"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            final_crontab = verify_result.stdout if verify_result.returncode == 0 else ""

            return {
                "registered": cron_comment in final_crontab,
                "cron_entry": cron_entry,
                "cron_schedule": cron_schedule,
                "backup_dir": backup_dir,
                "existing_crontab": final_crontab,
                "error": "",
            }

        except FileNotFoundError:
            return {
                "registered": False,
                "cron_entry": cron_entry,
                "cron_schedule": cron_schedule,
                "backup_dir": backup_dir,
                "existing_crontab": "",
                "error": "crontab command not found. Ensure cron is installed.",
            }
        except subprocess.TimeoutExpired:
            return {
                "registered": False,
                "cron_entry": cron_entry,
                "cron_schedule": cron_schedule,
                "backup_dir": backup_dir,
                "existing_crontab": "",
                "error": "crontab command timed out.",
            }
        except Exception as e:
            return {
                "registered": False,
                "cron_entry": cron_entry,
                "cron_schedule": cron_schedule,
                "backup_dir": backup_dir,
                "existing_crontab": "",
                "error": f"Unexpected error: {e}",
            }

    def validate(self, result: dict) -> list[dict]:
        """Validate that the cron job is registered.

        Checks:
        1. Cron job was registered successfully
        2. Cron schedule expression is valid
        3. Cron entry appears in the current crontab
        """
        checks = []

        # Check 1: Registration success
        registered = result.get("registered", False)
        checks.append({
            "name": "cron_registration",
            "passed": registered,
            "feedback": (
                "Cron job registered successfully."
                if registered
                else f"Cron registration failed: {result.get('error', 'Unknown error')}"
            ),
            "expected": "registered=True",
            "actual": f"registered={registered}",
        })

        # Check 2: Valid cron schedule
        cron_schedule = result.get("cron_schedule", "")
        parts = cron_schedule.split()
        valid_schedule = len(parts) == 5
        checks.append({
            "name": "cron_schedule_valid",
            "passed": valid_schedule,
            "feedback": (
                f"Cron schedule '{cron_schedule}' has valid format (5 fields)."
                if valid_schedule
                else f"Cron schedule '{cron_schedule}' is invalid. Expected 5 space-separated fields."
            ),
            "expected": "5 cron fields (min hour dom mon dow)",
            "actual": f"{len(parts)} fields" if parts else "empty",
        })

        # Check 3: Entry visible in crontab
        existing_crontab = result.get("existing_crontab", "")
        cron_entry = result.get("cron_entry", "")
        entry_visible = cron_entry in existing_crontab if cron_entry else False
        checks.append({
            "name": "cron_entry_visible",
            "passed": entry_visible,
            "feedback": (
                "Cron entry confirmed in active crontab."
                if entry_visible
                else "Cron entry not found in active crontab."
            ),
            "expected": "entry present in crontab -l output",
            "actual": "present" if entry_visible else "absent",
        })

        return checks

    def teardown(self) -> None:
        """Remove the test cron entry on teardown."""
        try:
            result = subprocess.run(
                ["crontab", "-l"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                lines = result.stdout.strip().split("\n")
                lines = [l for l in lines if "ai-store-backup" not in l]
                new_crontab = "\n".join(lines) + "\n" if lines else ""
                subprocess.run(
                    ["crontab", "-"],
                    input=new_crontab,
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
        except Exception:
            pass

    def get_hints(self) -> list[str]:
        return [
            "Cron format: minute hour day_of_month month day_of_week",
            "Example: '0 2 * * *' runs daily at 2:00 AM.",
            "Example: '*/30 * * * *' runs every 30 minutes.",
            "Use 'crontab -l' to view current cron jobs.",
            "Include a comment in your cron entry for easy identification.",
        ]

    def get_instructions(self) -> str:
        return (
            "Set up a scheduled cron job for automated database backups.\n\n"
            "Submit with:\n"
            "  - cron_schedule: Cron expression (e.g., '0 2 * * *' for daily at 2 AM)\n"
            "  - backup_script: Path to the backup script to execute\n"
            "  - backup_dir: Directory where scheduled backups will be stored\n"
            "  - db_name: Database name to back up\n"
            "  - cron_comment: Identifier comment for the cron entry (default: 'ai-store-backup')\n\n"
            "The validator will confirm the cron job is registered and will produce "
            "at least one backup file within 120 seconds of the scheduled trigger time."
        )

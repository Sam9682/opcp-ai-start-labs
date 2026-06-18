"""Exercise 01: Start Application via CLI.

Learners use the aipoweredstore_cli.py command-line tool to start
a registered application on the AI-Powered-Store platform.
"""

import subprocess
import time
from typing import Optional

from labs.templates.exercise_base import Exercise


class StartViaCLIExercise(Exercise):
    """Start a registered application using the platform CLI."""

    CLI_PATH = "/usr/local/bin/aipoweredstore_cli.py"
    STATUS_TIMEOUT_SECONDS = 120
    STATUS_POLL_INTERVAL_SECONDS = 5

    @property
    def exercise_id(self) -> str:
        return "01_start_via_cli"

    @property
    def name(self) -> str:
        return "Start Application via CLI"

    @property
    def description(self) -> str:
        return (
            "Launch a registered application using the "
            "aipoweredstore_cli.py command-line tool and verify "
            "it reaches a running state."
        )

    @property
    def timeout_minutes(self) -> int:
        return 5

    def setup(self) -> None:
        """Verify the CLI tool is accessible."""
        pass

    def execute(self, submission: dict) -> dict:
        """Execute the start command via CLI.

        Args:
            submission: Must contain:
                - app_name (str): Name of the application to start.
                - cli_path (str, optional): Override CLI path.

        Returns:
            Dict with cli_output, exit_code, app_status, and elapsed time.
        """
        app_name = submission.get("app_name", "")
        cli_path = submission.get("cli_path", self.CLI_PATH)

        if not app_name:
            return {
                "cli_output": "",
                "exit_code": 1,
                "app_status": "error",
                "error": "app_name is required in submission",
                "elapsed_seconds": 0.0,
            }

        start_time = time.time()

        # Execute the CLI start command
        try:
            result = subprocess.run(
                [cli_path, "app", "start", app_name],
                capture_output=True,
                text=True,
                timeout=30,
            )
            cli_output = result.stdout + result.stderr
            exit_code = result.returncode
        except FileNotFoundError:
            elapsed = time.time() - start_time
            return {
                "cli_output": f"CLI tool not found at: {cli_path}",
                "exit_code": 127,
                "app_status": "error",
                "error": f"CLI tool not found at: {cli_path}",
                "elapsed_seconds": elapsed,
            }
        except subprocess.TimeoutExpired:
            elapsed = time.time() - start_time
            return {
                "cli_output": "CLI command timed out after 30 seconds",
                "exit_code": 124,
                "app_status": "timeout",
                "error": "CLI command timed out",
                "elapsed_seconds": elapsed,
            }

        # Poll for running state within timeout
        app_status = self._poll_status(app_name, cli_path)
        elapsed = time.time() - start_time

        return {
            "cli_output": cli_output,
            "exit_code": exit_code,
            "app_status": app_status,
            "elapsed_seconds": elapsed,
        }

    def _poll_status(self, app_name: str, cli_path: str) -> str:
        """Poll application status until running or timeout.

        Returns:
            The application status string ("running", "starting", "error", etc.)
        """
        deadline = time.time() + self.STATUS_TIMEOUT_SECONDS

        while time.time() < deadline:
            try:
                result = subprocess.run(
                    [cli_path, "app", "status", app_name],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                output = result.stdout.strip().lower()
                if "running" in output:
                    return "running"
                if "error" in output or "failed" in output:
                    return "error"
            except (subprocess.TimeoutExpired, FileNotFoundError):
                pass

            time.sleep(self.STATUS_POLL_INTERVAL_SECONDS)

        return "timeout"

    def _get_container_logs(self, app_name: str, cli_path: str) -> str:
        """Retrieve the last 50 lines of container logs on failure."""
        try:
            result = subprocess.run(
                [cli_path, "app", "logs", app_name, "--tail", "50"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            return result.stdout
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return ""

    def validate(self, result: dict) -> list[dict]:
        """Validate that the application started successfully via CLI.

        Checks:
        - CLI command exited successfully (exit code 0)
        - Application reached running state within 120s

        If the application did not reach running state, reports the last
        50 lines of container logs (Requirement 7.4).
        """
        checks = []

        # Check 1: CLI exit code
        exit_code = result.get("exit_code", -1)
        checks.append({
            "name": "cli_exit_code",
            "passed": exit_code == 0,
            "feedback": (
                "CLI start command exited successfully."
                if exit_code == 0
                else f"CLI start command failed with exit code {exit_code}."
            ),
            "expected": "0",
            "actual": str(exit_code),
        })

        # Check 2: Application running state (Requirement 7.2)
        app_status = result.get("app_status", "unknown")
        running = app_status == "running"
        feedback = (
            "Application reached running state within 120 seconds."
            if running
            else (
                f"Application did not reach running state within 120 seconds. "
                f"Last status: {app_status}."
            )
        )

        # If not running, include container logs (Requirement 7.4)
        if not running and result.get("cli_output"):
            feedback += f"\nContainer logs:\n{result.get('cli_output', '')[-2000:]}"

        checks.append({
            "name": "app_running_state",
            "passed": running,
            "feedback": feedback,
            "expected": "running",
            "actual": app_status,
        })

        return checks

    def teardown(self) -> None:
        """No teardown needed — application remains running for next exercises."""
        pass

    def get_hints(self) -> list[str]:
        return [
            "Make sure the application has been registered before attempting to start it.",
            "Use 'aipoweredstore_cli.py app list' to see available applications.",
            "Check the platform logs if the start command fails.",
        ]

    def get_instructions(self) -> Optional[str]:
        return (
            "Use the AI-Powered-Store CLI to start a registered application.\n\n"
            "Command format:\n"
            "  aipoweredstore_cli.py app start <app_name>\n\n"
            "The exercise will verify that:\n"
            "1. The CLI command completes successfully (exit code 0)\n"
            "2. The application reaches a 'running' state within 120 seconds"
        )

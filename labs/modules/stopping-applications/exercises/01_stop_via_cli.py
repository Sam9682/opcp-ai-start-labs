"""Exercise 1: Stop Application via CLI.

Stop a running application using the aipoweredstore_cli.py command-line tool.
Validates that the application is running before stopping, verifies process
termination and port refusal within 5 seconds, and handles 30-second timeout
with a force-stop suggestion.
"""

import socket
import subprocess
import time
from typing import Optional

from labs.templates.exercise_base import Exercise


STOP_TIMEOUT_SECONDS = 30
VERIFICATION_TIMEOUT_SECONDS = 5


class StopViaCLIExercise(Exercise):
    """Stop a running application using the platform CLI."""

    @property
    def exercise_id(self) -> str:
        return "01_stop_via_cli"

    @property
    def name(self) -> str:
        return "Stop Application via CLI"

    @property
    def description(self) -> str:
        return (
            "Stop a running application using the aipoweredstore_cli.py "
            "command-line tool and verify graceful shutdown."
        )

    @property
    def timeout_minutes(self) -> int:
        return 10

    @property
    def prerequisites(self) -> list[str]:
        return []

    def setup(self) -> None:
        """Verify that the target application is running before proceeding."""
        pass

    def execute(self, submission: dict) -> dict:
        """Execute the stop command via CLI.

        Args:
            submission: Must contain:
                - app_name (str): Name of the application to stop
                - cli_path (str, optional): Path to CLI tool
                  (defaults to /usr/local/bin/aipoweredstore_cli.py)
                - host (str, optional): Application host (defaults to localhost)
                - port (int, optional): Application port to verify refusal

        Returns:
            Dict with execution results including process status and
            port connectivity check.
        """
        app_name = submission.get("app_name", "")
        cli_path = submission.get(
            "cli_path", "/usr/local/bin/aipoweredstore_cli.py"
        )
        host = submission.get("host", "localhost")
        port = submission.get("port")

        result = {
            "app_name": app_name,
            "pre_check_running": False,
            "stop_command_executed": False,
            "stop_exit_code": None,
            "stop_stdout": "",
            "stop_stderr": "",
            "process_terminated": False,
            "port_refuses_connections": False,
            "timed_out": False,
            "verification_time_seconds": 0.0,
            "force_stop_suggested": False,
        }

        # Pre-check: confirm application is running
        pre_check = _check_app_running(cli_path, app_name)
        result["pre_check_running"] = pre_check

        if not pre_check:
            result["stop_stderr"] = (
                f"Application '{app_name}' is not running. "
                "Cannot proceed with stop exercise."
            )
            return result

        # Execute stop command with timeout
        stop_result = _execute_stop_cli(cli_path, app_name)
        result["stop_command_executed"] = True
        result["stop_exit_code"] = stop_result["exit_code"]
        result["stop_stdout"] = stop_result["stdout"]
        result["stop_stderr"] = stop_result["stderr"]
        result["timed_out"] = stop_result["timed_out"]

        if stop_result["timed_out"]:
            result["force_stop_suggested"] = True
            return result

        # Verify process termination and port refusal within 5s
        verification = _verify_termination(cli_path, app_name, host, port)
        result["process_terminated"] = verification["process_terminated"]
        result["port_refuses_connections"] = verification["port_refuses"]
        result["verification_time_seconds"] = verification["elapsed_seconds"]

        return result

    def validate(self, result: dict) -> list[dict]:
        """Validate the stop operation results.

        Checks:
        1. Application was running before stop
        2. Stop command executed successfully
        3. Process terminated within 5 seconds
        4. Port refuses connections within 5 seconds
        5. If timed out, force-stop suggestion is provided
        """
        checks = []

        # Check 1: Pre-check running
        checks.append({
            "name": "app_running_before_stop",
            "passed": result.get("pre_check_running", False),
            "feedback": (
                "Application must be running before stop exercise."
                if not result.get("pre_check_running")
                else "Application confirmed running before stop."
            ),
            "expected": "running",
            "actual": (
                "running" if result.get("pre_check_running") else "not running"
            ),
        })

        # If app wasn't running, other checks are not applicable
        if not result.get("pre_check_running"):
            return checks

        # Check for timeout scenario
        if result.get("timed_out"):
            checks.append({
                "name": "stop_timeout_handled",
                "passed": result.get("force_stop_suggested", False),
                "feedback": (
                    "Stop operation timed out after 30 seconds. "
                    "Force-stop suggested as recovery option."
                ),
                "expected": "force_stop_suggested=True",
                "actual": (
                    f"force_stop_suggested="
                    f"{result.get('force_stop_suggested')}"
                ),
            })
            return checks

        # Check 2: Stop command exit code
        exit_code = result.get("stop_exit_code")
        checks.append({
            "name": "stop_command_success",
            "passed": exit_code == 0,
            "feedback": (
                "Stop command completed with zero exit code."
                if exit_code == 0
                else f"Stop command exited with code {exit_code}."
            ),
            "expected": "exit_code=0",
            "actual": f"exit_code={exit_code}",
        })

        # Check 3: Process terminated
        checks.append({
            "name": "process_terminated",
            "passed": result.get("process_terminated", False),
            "feedback": (
                "Application process terminated within 5 seconds."
                if result.get("process_terminated")
                else "Application process did not terminate within 5 seconds."
            ),
            "expected": "terminated=True",
            "actual": f"terminated={result.get('process_terminated')}",
        })

        # Check 4: Port refuses connections
        checks.append({
            "name": "port_refuses_connections",
            "passed": result.get("port_refuses_connections", False),
            "feedback": (
                "Application port refuses new connections."
                if result.get("port_refuses_connections")
                else "Application port still accepts connections."
            ),
            "expected": "refuses_connections=True",
            "actual": (
                f"refuses_connections="
                f"{result.get('port_refuses_connections')}"
            ),
        })

        return checks

    def teardown(self) -> None:
        """No teardown required for stop exercises."""
        pass

    def get_hints(self) -> list[str]:
        return [
            "Use 'aipoweredstore_cli.py stop <app_name>' to stop an application.",
            "The application must be in a running state before you can stop it.",
            "If the stop command times out after 30 seconds, try force-stop.",
        ]

    def get_instructions(self) -> Optional[str]:
        return (
            "In this exercise, you will stop a running application using "
            "the AI-Powered-Store CLI tool.\n\n"
            "Steps:\n"
            "1. Verify the target application is currently running\n"
            "2. Execute the stop command: "
            "`aipoweredstore_cli.py stop <app_name>`\n"
            "3. Verify the application process has terminated\n"
            "4. Confirm the application's port refuses new connections\n\n"
            "The stop operation should complete gracefully within 30 seconds. "
            "If it times out, you will be advised to use force-stop."
        )


def _check_app_running(cli_path: str, app_name: str) -> bool:
    """Check if an application is currently running via CLI status command.

    Args:
        cli_path: Path to the CLI tool.
        app_name: Name of the application to check.

    Returns:
        True if the application is running, False otherwise.
    """
    try:
        proc = subprocess.run(
            [cli_path, "status", app_name],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return "running" in proc.stdout.lower()
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return False


def _execute_stop_cli(cli_path: str, app_name: str) -> dict:
    """Execute the CLI stop command with a 30-second timeout.

    Args:
        cli_path: Path to the CLI tool.
        app_name: Name of the application to stop.

    Returns:
        Dict with exit_code, stdout, stderr, and timed_out fields.
    """
    try:
        proc = subprocess.run(
            [cli_path, "stop", app_name],
            capture_output=True,
            text=True,
            timeout=STOP_TIMEOUT_SECONDS,
        )
        return {
            "exit_code": proc.returncode,
            "stdout": proc.stdout,
            "stderr": proc.stderr,
            "timed_out": False,
        }
    except subprocess.TimeoutExpired:
        return {
            "exit_code": None,
            "stdout": "",
            "stderr": (
                f"Stop command timed out after {STOP_TIMEOUT_SECONDS} seconds. "
                f"Consider using force-stop: "
                f"'{cli_path} force-stop {app_name}'"
            ),
            "timed_out": True,
        }
    except (FileNotFoundError, OSError) as e:
        return {
            "exit_code": -1,
            "stdout": "",
            "stderr": f"Failed to execute CLI: {e}",
            "timed_out": False,
        }


def _verify_termination(
    cli_path: str, app_name: str, host: str, port: Optional[int]
) -> dict:
    """Verify process termination and port refusal within 5 seconds.

    Args:
        cli_path: Path to the CLI tool.
        app_name: Name of the application.
        host: Application host.
        port: Application port to check (None skips port check).

    Returns:
        Dict with process_terminated, port_refuses, and elapsed_seconds.
    """
    start_time = time.time()
    deadline = start_time + VERIFICATION_TIMEOUT_SECONDS
    process_terminated = False
    port_refuses = False

    while time.time() < deadline:
        # Check process status
        if not process_terminated:
            try:
                proc = subprocess.run(
                    [cli_path, "status", app_name],
                    capture_output=True,
                    text=True,
                    timeout=2,
                )
                if "stopped" in proc.stdout.lower() or proc.returncode != 0:
                    process_terminated = True
            except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
                process_terminated = True

        # Check port connectivity
        if port is not None and not port_refuses:
            port_refuses = _port_refuses_connection(host, port)

        # If both conditions met, we're done
        if process_terminated and (port is None or port_refuses):
            break

        time.sleep(0.5)

    # If no port specified, consider it passing
    if port is None:
        port_refuses = True

    elapsed = time.time() - start_time
    return {
        "process_terminated": process_terminated,
        "port_refuses": port_refuses,
        "elapsed_seconds": round(elapsed, 2),
    }


def _port_refuses_connection(host: str, port: int) -> bool:
    """Check if a port refuses TCP connections.

    Args:
        host: Target host.
        port: Target port.

    Returns:
        True if the port refuses connections, False if it accepts.
    """
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex((host, port))
        sock.close()
        # Non-zero means connection refused/failed
        return result != 0
    except (socket.error, OSError):
        # Connection error means port is refusing
        return True

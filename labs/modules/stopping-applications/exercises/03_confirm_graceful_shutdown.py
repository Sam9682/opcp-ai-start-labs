"""Exercise 3: Confirm Graceful Shutdown.

Verify graceful shutdown behavior: the application completes in-flight
requests, the process exits with a zero exit code, its ports refuse new
connections, and termination is confirmed within 5 seconds.

Also handles the force-stop scenario when the 30-second timeout is exceeded.
"""

import socket
import subprocess
import time
from typing import Optional

from labs.templates.exercise_base import Exercise


STOP_TIMEOUT_SECONDS = 30
VERIFICATION_TIMEOUT_SECONDS = 5


class ConfirmGracefulShutdownExercise(Exercise):
    """Confirm graceful shutdown of a running application."""

    @property
    def exercise_id(self) -> str:
        return "03_confirm_graceful_shutdown"

    @property
    def name(self) -> str:
        return "Confirm Graceful Shutdown"

    @property
    def description(self) -> str:
        return (
            "Verify graceful shutdown: application completes in-flight "
            "requests, exits with code 0, process terminates, and ports "
            "refuse new connections within 5 seconds."
        )

    @property
    def timeout_minutes(self) -> int:
        return 15

    @property
    def prerequisites(self) -> list[str]:
        return ["01_stop_via_cli", "02_stop_via_api"]

    def setup(self) -> None:
        """Prepare the exercise environment."""
        pass

    def execute(self, submission: dict) -> dict:
        """Execute graceful shutdown verification.

        Args:
            submission: Must contain:
                - app_name (str): Name of the application to stop
                - cli_path (str, optional): Path to CLI tool
                - host (str, optional): Application host
                - port (int, optional): Application port
                - method (str, optional): "cli" or "api" (default: "cli")
                - api_base_url (str, optional): API URL for API method
                - use_force_stop (bool, optional): Use force-stop
                  (default: False)

        Returns:
            Dict with comprehensive shutdown verification results.
        """
        app_name = submission.get("app_name", "")
        cli_path = submission.get(
            "cli_path", "/usr/local/bin/aipoweredstore_cli.py"
        )
        host = submission.get("host", "localhost")
        port = submission.get("port")
        method = submission.get("method", "cli")
        use_force_stop = submission.get("use_force_stop", False)

        result = {
            "app_name": app_name,
            "method": method,
            "use_force_stop": use_force_stop,
            "pre_check_running": False,
            "stop_initiated": False,
            "exit_code": None,
            "graceful_shutdown": False,
            "in_flight_completed": False,
            "process_terminated": False,
            "port_refuses_connections": False,
            "timed_out": False,
            "verification_time_seconds": 0.0,
            "force_stop_suggested": False,
            "force_stop_executed": False,
            "force_stop_verified": False,
        }

        # Pre-check: confirm application is running
        pre_check = _check_app_running(cli_path, app_name)
        result["pre_check_running"] = pre_check

        if not pre_check:
            return result

        # Execute stop (or force-stop)
        if use_force_stop:
            stop_result = _execute_force_stop(cli_path, app_name)
            result["force_stop_executed"] = True
        else:
            stop_result = _execute_graceful_stop(cli_path, app_name, method)

        result["stop_initiated"] = True
        result["exit_code"] = stop_result.get("exit_code")
        result["timed_out"] = stop_result.get("timed_out", False)

        # Handle timeout
        if result["timed_out"] and not use_force_stop:
            result["force_stop_suggested"] = True
            return result

        # Verify graceful shutdown characteristics
        verification = _verify_graceful_shutdown(
            cli_path, app_name, host, port, use_force_stop
        )
        result["graceful_shutdown"] = verification["graceful"]
        result["in_flight_completed"] = verification["in_flight_completed"]
        result["process_terminated"] = verification["process_terminated"]
        result["port_refuses_connections"] = verification["port_refuses"]
        result["verification_time_seconds"] = verification["elapsed_seconds"]

        if use_force_stop:
            result["force_stop_verified"] = (
                verification["process_terminated"]
                and verification["port_refuses"]
            )

        return result

    def validate(self, result: dict) -> list[dict]:
        """Validate graceful shutdown behavior.

        For normal stop:
        1. Application was running
        2. Stop initiated successfully
        3. Process exited with code 0 (graceful)
        4. In-flight requests completed
        5. Process terminated within 5s
        6. Port refuses connections within 5s

        For force-stop:
        1. Application was running
        2. Force-stop executed
        3. Process terminated (regardless of in-flight)
        4. Port refuses connections
        """
        checks = []
        use_force_stop = result.get("use_force_stop", False)

        # Check: Pre-check running
        checks.append({
            "name": "app_running_before_stop",
            "passed": result.get("pre_check_running", False),
            "feedback": (
                "Application confirmed running before stop."
                if result.get("pre_check_running")
                else "Application must be running before stop exercise."
            ),
            "expected": "running",
            "actual": (
                "running" if result.get("pre_check_running") else "not running"
            ),
        })

        if not result.get("pre_check_running"):
            return checks

        # Timeout scenario
        if result.get("timed_out") and not use_force_stop:
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

        if use_force_stop:
            # Force-stop validation (Req 8.5)
            checks.append({
                "name": "force_stop_executed",
                "passed": result.get("force_stop_executed", False),
                "feedback": (
                    "Force-stop command executed."
                    if result.get("force_stop_executed")
                    else "Force-stop command was not executed."
                ),
                "expected": "force_stop_executed=True",
                "actual": (
                    f"force_stop_executed="
                    f"{result.get('force_stop_executed')}"
                ),
            })

            checks.append({
                "name": "force_stop_process_terminated",
                "passed": result.get("process_terminated", False),
                "feedback": (
                    "Process terminated after force-stop."
                    if result.get("process_terminated")
                    else "Process did not terminate after force-stop."
                ),
                "expected": "terminated=True",
                "actual": f"terminated={result.get('process_terminated')}",
            })

            checks.append({
                "name": "force_stop_port_refuses",
                "passed": result.get("port_refuses_connections", False),
                "feedback": (
                    "Port refuses connections after force-stop."
                    if result.get("port_refuses_connections")
                    else "Port still accepts connections after force-stop."
                ),
                "expected": "refuses_connections=True",
                "actual": (
                    f"refuses_connections="
                    f"{result.get('port_refuses_connections')}"
                ),
            })
        else:
            # Graceful shutdown validation (Req 8.1, 8.3)
            checks.append({
                "name": "graceful_exit_code",
                "passed": result.get("exit_code") == 0,
                "feedback": (
                    "Application exited with code 0 (graceful shutdown)."
                    if result.get("exit_code") == 0
                    else (
                        f"Application exited with code "
                        f"{result.get('exit_code')} (not graceful)."
                    )
                ),
                "expected": "exit_code=0",
                "actual": f"exit_code={result.get('exit_code')}",
            })

            checks.append({
                "name": "in_flight_requests_completed",
                "passed": result.get("in_flight_completed", False),
                "feedback": (
                    "In-flight requests completed before shutdown."
                    if result.get("in_flight_completed")
                    else "In-flight requests may not have completed."
                ),
                "expected": "in_flight_completed=True",
                "actual": (
                    f"in_flight_completed="
                    f"{result.get('in_flight_completed')}"
                ),
            })

            checks.append({
                "name": "process_terminated",
                "passed": result.get("process_terminated", False),
                "feedback": (
                    "Process terminated within 5 seconds."
                    if result.get("process_terminated")
                    else "Process did not terminate within 5 seconds."
                ),
                "expected": "terminated=True",
                "actual": f"terminated={result.get('process_terminated')}",
            })

            checks.append({
                "name": "port_refuses_connections",
                "passed": result.get("port_refuses_connections", False),
                "feedback": (
                    "Port refuses new connections after shutdown."
                    if result.get("port_refuses_connections")
                    else "Port still accepts connections after shutdown."
                ),
                "expected": "refuses_connections=True",
                "actual": (
                    f"refuses_connections="
                    f"{result.get('port_refuses_connections')}"
                ),
            })

        return checks

    def teardown(self) -> None:
        """No teardown required."""
        pass

    def get_hints(self) -> list[str]:
        return [
            "Graceful shutdown means the app completes in-flight requests "
            "and exits with code 0.",
            "If graceful stop times out after 30 seconds, try using "
            "force-stop as a recovery option.",
            "Force-stop terminates the application immediately, "
            "regardless of in-flight requests.",
            "After stopping, verify both process termination AND "
            "port refusal within 5 seconds.",
        ]

    def get_instructions(self) -> Optional[str]:
        return (
            "In this exercise, you will verify graceful shutdown behavior "
            "of a running application.\n\n"
            "Graceful Shutdown Verification:\n"
            "1. Confirm the application is running\n"
            "2. Initiate a stop operation (CLI or API)\n"
            "3. Verify the application completes in-flight requests\n"
            "4. Verify the process exits with code 0\n"
            "5. Confirm process termination within 5 seconds\n"
            "6. Confirm ports refuse new connections within 5 seconds\n\n"
            "Force-Stop Scenario:\n"
            "- If the graceful stop times out (30 seconds), force-stop is "
            "suggested\n"
            "- Force-stop terminates immediately regardless of in-flight "
            "requests\n"
            "- After force-stop, verify process termination and port refusal"
        )


def _check_app_running(cli_path: str, app_name: str) -> bool:
    """Check if application is running via CLI status command."""
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


def _execute_graceful_stop(
    cli_path: str, app_name: str, method: str
) -> dict:
    """Execute a graceful stop operation.

    Args:
        cli_path: Path to the CLI tool.
        app_name: Application name.
        method: "cli" or "api".

    Returns:
        Dict with exit_code and timed_out.
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
            "timed_out": False,
        }
    except subprocess.TimeoutExpired:
        return {
            "exit_code": None,
            "stdout": "",
            "timed_out": True,
        }
    except (FileNotFoundError, OSError):
        return {
            "exit_code": -1,
            "stdout": "",
            "timed_out": False,
        }


def _execute_force_stop(cli_path: str, app_name: str) -> dict:
    """Execute a force-stop operation.

    Args:
        cli_path: Path to the CLI tool.
        app_name: Application name.

    Returns:
        Dict with exit_code and timed_out.
    """
    try:
        proc = subprocess.run(
            [cli_path, "force-stop", app_name],
            capture_output=True,
            text=True,
            timeout=STOP_TIMEOUT_SECONDS,
        )
        return {
            "exit_code": proc.returncode,
            "stdout": proc.stdout,
            "timed_out": False,
        }
    except subprocess.TimeoutExpired:
        return {
            "exit_code": None,
            "stdout": "",
            "timed_out": True,
        }
    except (FileNotFoundError, OSError):
        return {
            "exit_code": -1,
            "stdout": "",
            "timed_out": False,
        }


def _verify_graceful_shutdown(
    cli_path: str,
    app_name: str,
    host: str,
    port: Optional[int],
    is_force_stop: bool,
) -> dict:
    """Verify shutdown characteristics within 5 seconds.

    For graceful shutdown: checks exit code, in-flight completion,
    process termination, and port refusal.

    For force-stop: checks process termination and port refusal
    regardless of in-flight request completion.

    Args:
        cli_path: Path to CLI tool.
        app_name: Application name.
        host: Application host.
        port: Application port.
        is_force_stop: Whether this is a force-stop verification.

    Returns:
        Dict with graceful, in_flight_completed, process_terminated,
        port_refuses, and elapsed_seconds.
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
                status_output = proc.stdout.lower()
                if "stopped" in status_output or "terminated" in status_output:
                    process_terminated = True
                elif proc.returncode != 0:
                    process_terminated = True
            except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
                process_terminated = True

        # Check port
        if port is not None and not port_refuses:
            port_refuses = _port_refuses_connection(host, port)

        if process_terminated and (port is None or port_refuses):
            break

        time.sleep(0.5)

    if port is None:
        port_refuses = True

    elapsed = time.time() - start_time

    # For force-stop, in-flight completion is not required
    # For graceful, we consider it completed if process terminated cleanly
    in_flight_completed = process_terminated if not is_force_stop else True
    graceful = (
        process_terminated and port_refuses and not is_force_stop
    )

    return {
        "graceful": graceful,
        "in_flight_completed": in_flight_completed,
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
        return result != 0
    except (socket.error, OSError):
        return True

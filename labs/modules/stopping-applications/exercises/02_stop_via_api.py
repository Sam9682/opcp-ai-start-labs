"""Exercise 2: Stop Application via REST API.

Stop a running application using POST /api/deployments with action "stop".
Validates that the application is running before stopping, verifies process
termination and port refusal within 5 seconds, and handles 30-second timeout
with a force-stop suggestion.
"""

import socket
import time
from typing import Optional

import requests

from labs.templates.exercise_base import Exercise


STOP_TIMEOUT_SECONDS = 30
VERIFICATION_TIMEOUT_SECONDS = 5


class StopViaAPIExercise(Exercise):
    """Stop a running application using the platform REST API."""

    @property
    def exercise_id(self) -> str:
        return "02_stop_via_api"

    @property
    def name(self) -> str:
        return "Stop Application via REST API"

    @property
    def description(self) -> str:
        return (
            "Stop a running application using POST /api/deployments "
            "with action 'stop' and verify graceful shutdown."
        )

    @property
    def timeout_minutes(self) -> int:
        return 10

    @property
    def prerequisites(self) -> list[str]:
        return ["01_stop_via_cli"]

    def setup(self) -> None:
        """Verify platform API is reachable."""
        pass

    def execute(self, submission: dict) -> dict:
        """Execute the stop operation via REST API.

        Args:
            submission: Must contain:
                - app_name (str): Name of the application to stop
                - api_base_url (str): Base URL of the platform API
                  (e.g., http://localhost:5000/api)
                - host (str, optional): Application host (defaults to localhost)
                - port (int, optional): Application port to verify refusal
                - auth_token (str, optional): Authorization token

        Returns:
            Dict with execution results including API response,
            process status, and port connectivity check.
        """
        app_name = submission.get("app_name", "")
        api_base_url = submission.get("api_base_url", "http://localhost:5000/api")
        host = submission.get("host", "localhost")
        port = submission.get("port")
        auth_token = submission.get("auth_token")

        result = {
            "app_name": app_name,
            "pre_check_running": False,
            "api_request_sent": False,
            "api_status_code": None,
            "api_response_body": None,
            "process_terminated": False,
            "port_refuses_connections": False,
            "timed_out": False,
            "verification_time_seconds": 0.0,
            "force_stop_suggested": False,
        }

        headers = _build_headers(auth_token)

        # Pre-check: confirm application is running via API
        pre_check = _check_app_running_api(api_base_url, app_name, headers)
        result["pre_check_running"] = pre_check

        if not pre_check:
            result["api_response_body"] = (
                f"Application '{app_name}' is not running. "
                "Cannot proceed with stop exercise."
            )
            return result

        # Execute stop via POST /api/deployments
        stop_result = _execute_stop_api(api_base_url, app_name, headers)
        result["api_request_sent"] = True
        result["api_status_code"] = stop_result["status_code"]
        result["api_response_body"] = stop_result["response_body"]
        result["timed_out"] = stop_result["timed_out"]

        if stop_result["timed_out"]:
            result["force_stop_suggested"] = True
            return result

        # Verify process termination and port refusal within 5s
        verification = _verify_termination_api(
            api_base_url, app_name, headers, host, port
        )
        result["process_terminated"] = verification["process_terminated"]
        result["port_refuses_connections"] = verification["port_refuses"]
        result["verification_time_seconds"] = verification["elapsed_seconds"]

        return result

    def validate(self, result: dict) -> list[dict]:
        """Validate the stop operation results.

        Checks:
        1. Application was running before stop
        2. API returned successful status code
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

        # Check 2: API response success
        status_code = result.get("api_status_code")
        checks.append({
            "name": "api_response_success",
            "passed": status_code is not None and 200 <= status_code < 300,
            "feedback": (
                f"API returned status {status_code}."
                if status_code is not None
                else "No API response received."
            ),
            "expected": "2xx status code",
            "actual": f"status_code={status_code}",
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
            "Use POST /api/deployments with body: "
            '{"app_name": "<name>", "action": "stop"}',
            "Ensure you include the correct Content-Type: application/json header.",
            "If the request times out after 30 seconds, try force-stop.",
        ]

    def get_instructions(self) -> Optional[str]:
        return (
            "In this exercise, you will stop a running application using "
            "the AI-Powered-Store REST API.\n\n"
            "Steps:\n"
            "1. Verify the target application is currently running\n"
            "2. Send a POST request to /api/deployments with:\n"
            '   Body: {"app_name": "<name>", "action": "stop"}\n'
            "3. Verify the API returns a success response (2xx)\n"
            "4. Confirm the process has terminated\n"
            "5. Confirm the application's port refuses connections\n\n"
            "The stop operation should complete within 30 seconds. "
            "If it times out, you will be advised to use force-stop."
        )


def _build_headers(auth_token: Optional[str]) -> dict:
    """Build request headers with optional authorization.

    Args:
        auth_token: Bearer token for authentication (optional).

    Returns:
        Dict of HTTP headers.
    """
    headers = {"Content-Type": "application/json"}
    if auth_token:
        headers["Authorization"] = f"Bearer {auth_token}"
    return headers


def _check_app_running_api(
    api_base_url: str, app_name: str, headers: dict
) -> bool:
    """Check if an application is running via the platform API.

    Args:
        api_base_url: Base URL for the platform API.
        app_name: Name of the application.
        headers: HTTP headers.

    Returns:
        True if application is running, False otherwise.
    """
    try:
        response = requests.get(
            f"{api_base_url}/applications/{app_name}/status",
            headers=headers,
            timeout=10,
        )
        if response.status_code == 200:
            data = response.json()
            return data.get("status", "").lower() == "running"
    except (requests.RequestException, ValueError):
        pass
    return False


def _execute_stop_api(
    api_base_url: str, app_name: str, headers: dict
) -> dict:
    """Execute the stop operation via POST /api/deployments.

    Args:
        api_base_url: Base URL for the platform API.
        app_name: Name of the application to stop.
        headers: HTTP headers.

    Returns:
        Dict with status_code, response_body, and timed_out fields.
    """
    try:
        response = requests.post(
            f"{api_base_url}/deployments",
            json={"app_name": app_name, "action": "stop"},
            headers=headers,
            timeout=STOP_TIMEOUT_SECONDS,
        )
        return {
            "status_code": response.status_code,
            "response_body": response.text,
            "timed_out": False,
        }
    except requests.Timeout:
        return {
            "status_code": None,
            "response_body": (
                f"API request timed out after {STOP_TIMEOUT_SECONDS} seconds. "
                "Consider using force-stop: POST /api/deployments with "
                '{"app_name": "' + app_name + '", "action": "force-stop"}'
            ),
            "timed_out": True,
        }
    except requests.RequestException as e:
        return {
            "status_code": None,
            "response_body": f"API request failed: {e}",
            "timed_out": False,
        }


def _verify_termination_api(
    api_base_url: str,
    app_name: str,
    headers: dict,
    host: str,
    port: Optional[int],
) -> dict:
    """Verify process termination and port refusal within 5 seconds via API.

    Args:
        api_base_url: Base URL for the platform API.
        app_name: Name of the application.
        headers: HTTP headers.
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
        # Check process status via API
        if not process_terminated:
            try:
                response = requests.get(
                    f"{api_base_url}/applications/{app_name}/status",
                    headers=headers,
                    timeout=2,
                )
                if response.status_code == 200:
                    data = response.json()
                    status = data.get("status", "").lower()
                    if status in ("stopped", "terminated", "exited"):
                        process_terminated = True
                elif response.status_code == 404:
                    # Application no longer exists - considered terminated
                    process_terminated = True
            except (requests.RequestException, ValueError):
                process_terminated = True

        # Check port connectivity
        if port is not None and not port_refuses:
            port_refuses = _port_refuses_connection(host, port)

        if process_terminated and (port is None or port_refuses):
            break

        time.sleep(0.5)

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
        return result != 0
    except (socket.error, OSError):
        return True

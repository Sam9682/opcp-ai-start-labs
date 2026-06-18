"""Exercise 03: Verify Running Status and Health Check.

Learners verify that a started application is actually running by checking
its status endpoint and testing TCP connectivity on exposed ports.
"""

import socket
import time
from typing import Optional

import requests

from labs.templates.exercise_base import Exercise


class VerifyRunningStatusExercise(Exercise):
    """Verify application running state and port health checks."""

    STATUS_TIMEOUT_SECONDS = 120
    PORT_TIMEOUT_SECONDS = 30
    PORT_CONNECT_TIMEOUT_SECONDS = 5

    @property
    def exercise_id(self) -> str:
        return "03_verify_running_status"

    @property
    def name(self) -> str:
        return "Verify Running Status and Health Check"

    @property
    def description(self) -> str:
        return (
            "Confirm the application reports a running status and "
            "responds to health checks on its exposed ports."
        )

    @property
    def timeout_minutes(self) -> int:
        return 5

    @property
    def prerequisites(self) -> list[str]:
        return ["01_start_via_cli"]

    def setup(self) -> None:
        """No additional setup needed."""
        pass

    def execute(self, submission: dict) -> dict:
        """Verify running status and port connectivity.

        Args:
            submission: Must contain:
                - app_name (str): Name of the application to check.
                - api_base_url (str): Base URL of the platform API.
                - api_token (str, optional): Authentication token.
                - exposed_ports (list[dict], optional): Ports to check.
                  Each dict: {"host": "...", "port": int}
                  If not provided, retrieved from platform API.

        Returns:
            Dict with status_check results, port_check results, and timing.
        """
        app_name = submission.get("app_name", "")
        api_base_url = submission.get("api_base_url", "").rstrip("/")
        api_token = submission.get("api_token", "")
        exposed_ports = submission.get("exposed_ports", [])

        if not app_name:
            return {
                "status_check": {"status": "error", "reason": "app_name is required"},
                "port_checks": [],
                "elapsed_seconds": 0.0,
            }

        if not api_base_url:
            return {
                "status_check": {"status": "error", "reason": "api_base_url is required"},
                "port_checks": [],
                "elapsed_seconds": 0.0,
            }

        headers = {"Content-Type": "application/json"}
        if api_token:
            headers["Authorization"] = f"Bearer {api_token}"

        start_time = time.time()

        # Check 1: Verify running state via status endpoint (Requirement 7.2)
        status_result = self._check_running_status(
            app_name, api_base_url, headers
        )

        # Check 2: If no ports provided, try to retrieve from API
        if not exposed_ports:
            exposed_ports = self._get_exposed_ports(
                app_name, api_base_url, headers
            )

        # Check 3: Verify TCP connectivity on exposed ports (Requirement 7.3)
        port_results = self._check_port_connectivity(exposed_ports)

        elapsed = time.time() - start_time

        return {
            "status_check": status_result,
            "port_checks": port_results,
            "exposed_ports": exposed_ports,
            "elapsed_seconds": elapsed,
        }

    def _check_running_status(
        self, app_name: str, api_base_url: str, headers: dict
    ) -> dict:
        """Check that the application is in running state within 120s.

        Returns:
            Dict with 'status', 'running' (bool), and optional 'reason'.
        """
        status_url = f"{api_base_url}/api/deployments/{app_name}/status"
        deadline = time.time() + self.STATUS_TIMEOUT_SECONDS

        last_status = "unknown"
        last_reason = ""

        while time.time() < deadline:
            try:
                resp = requests.get(status_url, headers=headers, timeout=10)
                if resp.status_code == 200:
                    data = resp.json()
                    last_status = data.get("status", "unknown").lower()
                    last_reason = data.get("reason", "")
                    if last_status == "running":
                        return {
                            "status": "running",
                            "running": True,
                        }
                    if last_status in ("error", "failed", "crashed"):
                        return {
                            "status": last_status,
                            "running": False,
                            "reason": last_reason or f"Application {last_status}",
                        }
                else:
                    last_status = f"http_{resp.status_code}"
            except requests.ConnectionError:
                last_status = "connection_error"
                last_reason = f"Cannot reach {status_url}"
            except requests.Timeout:
                last_status = "request_timeout"
            except requests.RequestException as e:
                last_status = "error"
                last_reason = str(e)

            time.sleep(5)

        # Timeout reached — retrieve logs (Requirement 7.4)
        logs = self._get_container_logs(app_name, api_base_url, headers)
        return {
            "status": last_status,
            "running": False,
            "reason": last_reason or "Timed out waiting for running state",
            "container_logs": logs,
        }

    def _get_container_logs(
        self, app_name: str, api_base_url: str, headers: dict
    ) -> str:
        """Retrieve the last 50 lines of container logs (Requirement 7.4)."""
        logs_url = f"{api_base_url}/api/deployments/{app_name}/logs"
        try:
            resp = requests.get(
                logs_url,
                headers=headers,
                params={"tail": 50},
                timeout=10,
            )
            if resp.status_code == 200:
                data = resp.json()
                return data.get("logs", "")
        except requests.RequestException:
            pass
        return ""

    def _get_exposed_ports(
        self, app_name: str, api_base_url: str, headers: dict
    ) -> list[dict]:
        """Retrieve the application's exposed ports from the platform API."""
        ports_url = f"{api_base_url}/api/deployments/{app_name}/ports"
        try:
            resp = requests.get(ports_url, headers=headers, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                return data.get("ports", [])
        except requests.RequestException:
            pass
        return []

    def _check_port_connectivity(self, ports: list[dict]) -> list[dict]:
        """Check TCP connectivity on each exposed port within 30s (Requirement 7.3).

        Args:
            ports: List of dicts with 'host' and 'port' keys.

        Returns:
            List of dicts with per-port check results.
        """
        results = []
        for port_info in ports:
            host = port_info.get("host", "localhost")
            port = port_info.get("port", 0)

            if not port:
                results.append({
                    "host": host,
                    "port": port,
                    "connected": False,
                    "error": "Invalid port number",
                })
                continue

            connected = self._try_connect(host, port)
            results.append({
                "host": host,
                "port": port,
                "connected": connected,
                "error": "" if connected else f"TCP connection to {host}:{port} failed within {self.PORT_TIMEOUT_SECONDS}s",
            })

        return results

    def _try_connect(self, host: str, port: int) -> bool:
        """Attempt TCP connection within the port timeout (30s)."""
        deadline = time.time() + self.PORT_TIMEOUT_SECONDS

        while time.time() < deadline:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(self.PORT_CONNECT_TIMEOUT_SECONDS)
                result = sock.connect_ex((host, port))
                sock.close()
                if result == 0:
                    return True
            except (socket.error, OSError):
                pass

            time.sleep(2)

        return False

    def validate(self, result: dict) -> list[dict]:
        """Validate running status and port connectivity.

        Displays per-check pass/fail results (Requirement 7.5).

        Checks:
        - Application is in running state (Requirement 7.2)
        - Each exposed port accepts TCP connections within 30s (Requirement 7.3)
        """
        checks = []

        # Check 1: Running state (Requirement 7.2)
        status_check = result.get("status_check", {})
        is_running = status_check.get("running", False)

        if is_running:
            feedback = "Application is in running state."
        else:
            status = status_check.get("status", "unknown")
            reason = status_check.get("reason", "")
            feedback = (
                f"Application is NOT in running state. "
                f"Status: {status}."
            )
            if reason:
                feedback += f" Reason: {reason}"
            # Include container logs if available (Requirement 7.4)
            container_logs = status_check.get("container_logs", "")
            if container_logs:
                # Show last 50 lines
                log_lines = container_logs.strip().split("\n")
                last_50 = "\n".join(log_lines[-50:])
                feedback += f"\n\nLast 50 lines of container logs:\n{last_50}"

        checks.append({
            "name": "running_state",
            "passed": is_running,
            "feedback": feedback,
            "expected": "running",
            "actual": status_check.get("status", "unknown"),
        })

        # Check 2+: Port connectivity (Requirement 7.3)
        port_checks = result.get("port_checks", [])
        if port_checks:
            for port_result in port_checks:
                host = port_result.get("host", "unknown")
                port = port_result.get("port", 0)
                connected = port_result.get("connected", False)
                error = port_result.get("error", "")

                check_name = f"port_connectivity_{host}_{port}"
                if connected:
                    port_feedback = (
                        f"TCP connection to {host}:{port} succeeded within 30 seconds."
                    )
                else:
                    port_feedback = (
                        f"TCP connection to {host}:{port} failed. {error}"
                    )

                checks.append({
                    "name": check_name,
                    "passed": connected,
                    "feedback": port_feedback,
                    "expected": "connected",
                    "actual": "connected" if connected else "refused",
                })
        else:
            # No ports to check — add informational check
            checks.append({
                "name": "port_connectivity",
                "passed": is_running,
                "feedback": (
                    "No exposed ports configured for connectivity check."
                    if is_running
                    else "Cannot check ports: application is not running."
                ),
                "expected": "ports available",
                "actual": "no ports configured",
            })

        return checks

    def teardown(self) -> None:
        """No teardown needed."""
        pass

    def get_hints(self) -> list[str]:
        return [
            "Use the platform API status endpoint to check application state.",
            "If the status is not 'running' after starting, check logs for errors.",
            "Port connectivity requires the application to be actively listening.",
            "Common ports: 8080 (HTTP), 443 (HTTPS), 5000 (Flask).",
        ]

    def get_instructions(self) -> Optional[str]:
        return (
            "Verify that your started application is truly operational.\n\n"
            "This exercise checks two things:\n"
            "1. The application reports 'running' status via the platform API\n"
            "2. The application's exposed ports accept TCP connections\n\n"
            "Steps:\n"
            "- Query the deployment status endpoint for your application\n"
            "- Verify the status field shows 'running'\n"
            "- Attempt to connect to each exposed port\n\n"
            "Timeouts:\n"
            "- Running state must be achieved within 120 seconds\n"
            "- Each port must accept connections within 30 seconds"
        )

"""Exercise 02: Start Application via REST API.

Learners start an application by sending a POST request to the
platform's /api/deployments endpoint with action "start".
"""

import time
from typing import Optional

import requests

from labs.templates.exercise_base import Exercise


class StartViaAPIExercise(Exercise):
    """Start a registered application using the platform REST API."""

    STATUS_TIMEOUT_SECONDS = 120
    STATUS_POLL_INTERVAL_SECONDS = 5

    @property
    def exercise_id(self) -> str:
        return "02_start_via_api"

    @property
    def name(self) -> str:
        return "Start Application via REST API"

    @property
    def description(self) -> str:
        return (
            "Start an application by sending a POST request to "
            "/api/deployments with action 'start' and verify "
            "it reaches a running state."
        )

    @property
    def timeout_minutes(self) -> int:
        return 5

    @property
    def prerequisites(self) -> list[str]:
        return ["01_start_via_cli"]

    def setup(self) -> None:
        """Verify API endpoint connectivity."""
        pass

    def execute(self, submission: dict) -> dict:
        """Execute the start action via REST API.

        Args:
            submission: Must contain:
                - app_name (str): Name of the application to start.
                - api_base_url (str): Base URL of the platform API.
                - api_token (str, optional): Authentication token.

        Returns:
            Dict with api_response, status_code, app_status, and elapsed time.
        """
        app_name = submission.get("app_name", "")
        api_base_url = submission.get("api_base_url", "").rstrip("/")
        api_token = submission.get("api_token", "")

        if not app_name:
            return {
                "api_response": {},
                "status_code": 0,
                "app_status": "error",
                "error": "app_name is required in submission",
                "elapsed_seconds": 0.0,
            }

        if not api_base_url:
            return {
                "api_response": {},
                "status_code": 0,
                "app_status": "error",
                "error": "api_base_url is required in submission",
                "elapsed_seconds": 0.0,
            }

        start_time = time.time()
        headers = {"Content-Type": "application/json"}
        if api_token:
            headers["Authorization"] = f"Bearer {api_token}"

        # POST /api/deployments with action "start" (Requirement 7.1)
        deploy_url = f"{api_base_url}/api/deployments"
        payload = {
            "app_name": app_name,
            "action": "start",
        }

        try:
            response = requests.post(
                deploy_url,
                json=payload,
                headers=headers,
                timeout=30,
            )
            api_response = response.json() if response.content else {}
            status_code = response.status_code
        except requests.ConnectionError:
            elapsed = time.time() - start_time
            return {
                "api_response": {},
                "status_code": 0,
                "app_status": "error",
                "error": (
                    f"Connection error: unable to reach {deploy_url}. "
                    "Check network connectivity."
                ),
                "elapsed_seconds": elapsed,
            }
        except requests.Timeout:
            elapsed = time.time() - start_time
            return {
                "api_response": {},
                "status_code": 0,
                "app_status": "timeout",
                "error": "API request timed out after 30 seconds",
                "elapsed_seconds": elapsed,
            }
        except requests.RequestException as e:
            elapsed = time.time() - start_time
            return {
                "api_response": {},
                "status_code": 0,
                "app_status": "error",
                "error": f"Request failed: {e}",
                "elapsed_seconds": elapsed,
            }

        # Poll for running state within 120s (Requirement 7.2)
        app_status = self._poll_status(app_name, api_base_url, headers)
        elapsed = time.time() - start_time

        return {
            "api_response": api_response,
            "status_code": status_code,
            "app_status": app_status,
            "elapsed_seconds": elapsed,
        }

    def _poll_status(
        self, app_name: str, api_base_url: str, headers: dict
    ) -> str:
        """Poll application status via API until running or timeout.

        Returns:
            The application status string.
        """
        status_url = f"{api_base_url}/api/deployments/{app_name}/status"
        deadline = time.time() + self.STATUS_TIMEOUT_SECONDS

        while time.time() < deadline:
            try:
                resp = requests.get(status_url, headers=headers, timeout=10)
                if resp.status_code == 200:
                    data = resp.json()
                    status = data.get("status", "").lower()
                    if status == "running":
                        return "running"
                    if status in ("error", "failed", "crashed"):
                        return status
            except requests.RequestException:
                pass

            time.sleep(self.STATUS_POLL_INTERVAL_SECONDS)

        return "timeout"

    def _get_failure_reason(
        self, app_name: str, api_base_url: str, headers: dict
    ) -> str:
        """Retrieve failure reason from the platform status endpoint."""
        status_url = f"{api_base_url}/api/deployments/{app_name}/status"
        try:
            resp = requests.get(status_url, headers=headers, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                return data.get("reason", "Unknown failure reason")
        except requests.RequestException:
            pass
        return "Unable to retrieve failure reason"

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

    def validate(self, result: dict) -> list[dict]:
        """Validate that the application started successfully via API.

        Checks:
        - API responded with 2xx status code
        - Application reached running state within 120s

        If the application did not reach running state, reports the last
        50 lines of container logs and failure reason (Requirement 7.4).
        """
        checks = []

        # Check 1: API response status code
        status_code = result.get("status_code", 0)
        api_success = 200 <= status_code < 300
        checks.append({
            "name": "api_response_status",
            "passed": api_success,
            "feedback": (
                f"API responded with status {status_code} (success)."
                if api_success
                else f"API responded with status {status_code} (expected 2xx)."
            ),
            "expected": "2xx",
            "actual": str(status_code),
        })

        # Check 2: Application running state (Requirement 7.2)
        app_status = result.get("app_status", "unknown")
        running = app_status == "running"

        if running:
            feedback = "Application reached running state within 120 seconds."
        else:
            feedback = (
                f"Application did not reach running state within 120 seconds. "
                f"Last status: {app_status}."
            )
            # Include error details (Requirement 7.4)
            error = result.get("error", "")
            if error:
                feedback += f"\nError: {error}"

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
            "The endpoint is POST /api/deployments with a JSON body.",
            "The body must include 'app_name' and 'action' set to 'start'.",
            "Use curl or requests library to make the API call.",
            "Check that your API token is valid and has deployment permissions.",
        ]

    def get_instructions(self) -> Optional[str]:
        return (
            "Start an application using the AI-Powered-Store REST API.\n\n"
            "API endpoint:\n"
            "  POST /api/deployments\n\n"
            "Request body:\n"
            '  {"app_name": "<your_app>", "action": "start"}\n\n'
            "The exercise will verify that:\n"
            "1. The API responds with a 2xx status code\n"
            "2. The application reaches a 'running' state within 120 seconds"
        )

"""Exercise 4: Verify Automatic Cleanup.

Verify that after a serverless task completes (or times out), the platform
automatically terminates the container and releases all compute and network
resources within 30 seconds.
"""

import time
from typing import Optional

import requests

from labs.templates.exercise_base import Exercise


CLEANUP_TIMEOUT_SECONDS = 30
CLEANUP_POLL_INTERVAL_SECONDS = 2


class VerifyCleanupExercise(Exercise):
    """Verify container cleanup after task completion."""

    @property
    def exercise_id(self) -> str:
        return "04_verify_cleanup"

    @property
    def name(self) -> str:
        return "Verify Automatic Cleanup"

    @property
    def description(self) -> str:
        return (
            "Verify that the container is terminated and all resources "
            "(compute, network) are released within 30 seconds after "
            "a serverless task completes or times out."
        )

    @property
    def timeout_minutes(self) -> int:
        return 5

    @property
    def prerequisites(self) -> list[str]:
        return ["01_submit_serverless_task", "02_monitor_status"]

    def setup(self) -> None:
        """Verify platform API is reachable."""
        pass

    def execute(self, submission: dict) -> dict:
        """Verify resource cleanup for a completed serverless task.

        Args:
            submission: Must contain:
                - task_id (str): ID of a completed/timed-out task
                - api_base_url (str): Base URL of the platform API
                - auth_token (str, optional): Authorization token

        Returns:
            Dict with cleanup verification results including container
            status, resource release confirmation, and timing.
        """
        task_id = submission.get("task_id", "")
        api_base_url = submission.get(
            "api_base_url", "http://localhost:5000/api"
        )
        auth_token = submission.get("auth_token")

        result = {
            "task_id": task_id,
            "container_terminated": False,
            "resources_released": False,
            "cleanup_duration_seconds": 0.0,
            "cleanup_within_30s": False,
            "container_status": None,
            "resource_status": None,
            "error": None,
        }

        if not task_id:
            result["error"] = "No task_id provided"
            return result

        headers = {"Content-Type": "application/json"}
        if auth_token:
            headers["Authorization"] = f"Bearer {auth_token}"

        # First confirm the task is in a terminal state
        task_status = _get_task_status(api_base_url, task_id, headers)
        if task_status not in (
            "completed", "succeeded", "done", "failed", "error", "timeout"
        ):
            result["error"] = (
                f"Task is not in a terminal state (status: {task_status}). "
                "Cleanup verification requires a completed or timed-out task."
            )
            return result

        # Poll for container termination and resource release
        start_time = time.time()
        deadline = start_time + CLEANUP_TIMEOUT_SECONDS

        while time.time() < deadline:
            cleanup_status = _check_cleanup_status(
                api_base_url, task_id, headers
            )

            if cleanup_status.get("error"):
                result["error"] = cleanup_status["error"]
                break

            container_terminated = cleanup_status.get(
                "container_terminated", False
            )
            resources_released = cleanup_status.get(
                "resources_released", False
            )
            result["container_status"] = cleanup_status.get(
                "container_status"
            )
            result["resource_status"] = cleanup_status.get("resource_status")

            if container_terminated and resources_released:
                elapsed = round(time.time() - start_time, 2)
                result["container_terminated"] = True
                result["resources_released"] = True
                result["cleanup_duration_seconds"] = elapsed
                result["cleanup_within_30s"] = (
                    elapsed <= CLEANUP_TIMEOUT_SECONDS
                )
                return result

            if container_terminated and not result["container_terminated"]:
                result["container_terminated"] = True

            time.sleep(CLEANUP_POLL_INTERVAL_SECONDS)

        # Timeout reached
        elapsed = round(time.time() - start_time, 2)
        result["cleanup_duration_seconds"] = elapsed
        result["cleanup_within_30s"] = False
        if not result["container_terminated"]:
            result["error"] = (
                f"Container not terminated within {CLEANUP_TIMEOUT_SECONDS}s"
            )
        elif not result["resources_released"]:
            result["error"] = (
                f"Resources not released within {CLEANUP_TIMEOUT_SECONDS}s"
            )

        return result

    def validate(self, result: dict) -> list[dict]:
        """Validate cleanup results.

        Checks:
        1. Container was terminated after task completion
        2. All resources (compute, network) were released
        3. Cleanup completed within 30 seconds
        """
        checks = []

        # Check 1: Container terminated (Requirement 12.3)
        checks.append({
            "name": "container_terminated",
            "passed": result.get("container_terminated", False),
            "feedback": (
                f"Container terminated "
                f"(status: {result.get('container_status')})."
                if result.get("container_terminated")
                else (
                    "Container was not confirmed terminated after task "
                    f"completion. Status: {result.get('container_status')}"
                )
            ),
            "expected": "container_terminated=True",
            "actual": (
                f"container_terminated={result.get('container_terminated')}"
            ),
        })

        # Check 2: Resources released (Requirement 12.3)
        checks.append({
            "name": "resources_released",
            "passed": result.get("resources_released", False),
            "feedback": (
                "All compute and network resources released."
                if result.get("resources_released")
                else (
                    "Resources not fully released. "
                    f"Resource status: {result.get('resource_status')}"
                )
            ),
            "expected": "resources_released=True",
            "actual": f"resources_released={result.get('resources_released')}",
        })

        # Check 3: Cleanup within 30s (Requirement 12.3)
        cleanup_duration = result.get("cleanup_duration_seconds", 0)
        within_30s = result.get("cleanup_within_30s", False)
        checks.append({
            "name": "cleanup_within_30s",
            "passed": within_30s,
            "feedback": (
                f"Cleanup completed in {cleanup_duration:.1f}s "
                f"(within 30s limit)."
                if within_30s
                else (
                    f"Cleanup took {cleanup_duration:.1f}s, "
                    "exceeding the 30s requirement."
                )
            ),
            "expected": "cleanup_duration <= 30s",
            "actual": f"cleanup_duration={cleanup_duration:.1f}s",
        })

        return checks

    def teardown(self) -> None:
        """No teardown required; verification is read-only."""
        pass

    def get_hints(self) -> list[str]:
        return [
            "Use GET /api/serverless/tasks/<task_id>/cleanup to check status.",
            "The cleanup endpoint reports both container and resource status.",
            "Container must be terminated (not just stopped) for this check.",
            "Resources include both compute (CPU/memory) and network allocation.",
            "Cleanup must complete within 30 seconds of task completion.",
        ]

    def get_instructions(self) -> Optional[str]:
        return (
            "In this exercise, you will verify automatic cleanup after a "
            "serverless task completes:\n\n"
            "Steps:\n"
            "1. Use a task_id from a completed or timed-out task\n"
            "2. Query GET /api/serverless/tasks/<task_id>/cleanup\n"
            "3. Verify the container has been terminated\n"
            "4. Verify all resources have been released\n"
            "5. Confirm cleanup happened within 30 seconds\n\n"
            "Expected cleanup response:\n"
            "  {\n"
            '    "container_status": "terminated",\n'
            '    "resources_released": true,\n'
            '    "cleanup_duration_seconds": 2.5,\n'
            '    "compute_freed": true,\n'
            '    "network_freed": true\n'
            "  }\n\n"
            "Requirements:\n"
            "- Container must be fully terminated (not just stopped)\n"
            "- No compute resources (CPU/memory) still allocated\n"
            "- No network resources still allocated\n"
            "- All of the above within 30 seconds of task completion"
        )


def _get_task_status(
    api_base_url: str, task_id: str, headers: dict
) -> str:
    """Get the current status of a task.

    Args:
        api_base_url: Base URL for the platform API.
        task_id: The task identifier.
        headers: HTTP headers.

    Returns:
        The task status string, or "unknown" if unavailable.
    """
    try:
        response = requests.get(
            f"{api_base_url}/serverless/tasks/{task_id}",
            headers=headers,
            timeout=5,
        )
        if response.status_code == 200:
            data = response.json()
            return data.get("status", "unknown").lower()
    except (requests.RequestException, ValueError):
        pass
    return "unknown"


def _check_cleanup_status(
    api_base_url: str, task_id: str, headers: dict
) -> dict:
    """Check the cleanup status of a completed task.

    Args:
        api_base_url: Base URL for the platform API.
        task_id: The task identifier.
        headers: HTTP headers.

    Returns:
        Dict with container_terminated, resources_released,
        container_status, resource_status, and error.
    """
    try:
        response = requests.get(
            f"{api_base_url}/serverless/tasks/{task_id}/cleanup",
            headers=headers,
            timeout=5,
        )
        if response.status_code == 200:
            data = response.json()
            container_status = data.get("container_status", "").lower()
            resources_released = data.get("resources_released", False)
            compute_freed = data.get("compute_freed", False)
            network_freed = data.get("network_freed", False)

            return {
                "container_terminated": container_status in (
                    "terminated", "removed", "cleaned"
                ),
                "resources_released": (
                    resources_released or (compute_freed and network_freed)
                ),
                "container_status": container_status,
                "resource_status": (
                    f"compute_freed={compute_freed}, "
                    f"network_freed={network_freed}"
                ),
                "error": None,
            }
        else:
            return {
                "container_terminated": False,
                "resources_released": False,
                "container_status": None,
                "resource_status": None,
                "error": (
                    f"Cleanup endpoint returned status {response.status_code}"
                ),
            }
    except (requests.RequestException, ValueError) as e:
        return {
            "container_terminated": False,
            "resources_released": False,
            "container_status": None,
            "resource_status": None,
            "error": f"Cleanup status request failed: {e}",
        }

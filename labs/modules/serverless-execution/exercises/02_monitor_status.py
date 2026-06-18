"""Exercise 2: Monitor Execution Status.

Monitor the execution status of a running serverless task. Polls the
platform API for status updates and validates that timeout handling
works correctly when a task exceeds its time limit.
"""

import time
from typing import Optional

import requests

from labs.templates.exercise_base import Exercise


POLL_INTERVAL_SECONDS = 2
TIMEOUT_HANDLING_WINDOW_SECONDS = 30


class MonitorStatusExercise(Exercise):
    """Monitor execution status of a running serverless task."""

    @property
    def exercise_id(self) -> str:
        return "02_monitor_status"

    @property
    def name(self) -> str:
        return "Monitor Execution Status"

    @property
    def description(self) -> str:
        return (
            "Monitor the execution status of a running serverless task. "
            "Verify that status transitions are reported correctly and "
            "that timeout handling terminates the container within 30 seconds "
            "when the time limit is exceeded."
        )

    @property
    def timeout_minutes(self) -> int:
        return 5

    @property
    def prerequisites(self) -> list[str]:
        return ["01_submit_serverless_task"]

    def setup(self) -> None:
        """Verify platform API is reachable."""
        pass

    def execute(self, submission: dict) -> dict:
        """Monitor a serverless task's execution status.

        Args:
            submission: Must contain:
                - task_id (str): ID of a previously submitted task to monitor
                - api_base_url (str): Base URL of the platform API
                - auth_token (str, optional): Authorization token
                - monitor_timeout_seconds (int, optional): How long to
                  monitor before giving up (defaults to 60)

        Returns:
            Dict with monitoring results including status transitions,
            final status, and timeout handling information.
        """
        task_id = submission.get("task_id", "")
        api_base_url = submission.get(
            "api_base_url", "http://localhost:5000/api"
        )
        auth_token = submission.get("auth_token")
        monitor_timeout = submission.get("monitor_timeout_seconds", 60)

        result = {
            "task_id": task_id,
            "status_transitions": [],
            "final_status": None,
            "monitoring_duration_seconds": 0.0,
            "timed_out": False,
            "timeout_indication_displayed": False,
            "termination_confirmed_within_30s": False,
            "error": None,
        }

        if not task_id:
            result["error"] = "No task_id provided"
            return result

        headers = {"Content-Type": "application/json"}
        if auth_token:
            headers["Authorization"] = f"Bearer {auth_token}"

        start_time = time.time()
        deadline = start_time + monitor_timeout
        previous_status = None

        while time.time() < deadline:
            try:
                response = requests.get(
                    f"{api_base_url}/serverless/tasks/{task_id}",
                    headers=headers,
                    timeout=5,
                )

                if response.status_code == 200:
                    data = response.json()
                    current_status = data.get("status", "unknown").lower()

                    # Record status transition
                    if current_status != previous_status:
                        elapsed = round(time.time() - start_time, 2)
                        result["status_transitions"].append({
                            "status": current_status,
                            "timestamp_offset_seconds": elapsed,
                        })
                        previous_status = current_status

                    # Check for terminal states
                    if current_status in (
                        "completed", "succeeded", "done", "failed", "error"
                    ):
                        result["final_status"] = current_status
                        result["monitoring_duration_seconds"] = round(
                            time.time() - start_time, 2
                        )
                        return result

                    # Check for timeout state
                    if current_status == "timeout":
                        result["timed_out"] = True
                        result["timeout_indication_displayed"] = True
                        result["final_status"] = "timeout"

                        # Verify termination within 30s
                        termination_start = time.time()
                        termination_confirmed = _verify_termination(
                            api_base_url, task_id, headers
                        )
                        termination_elapsed = time.time() - termination_start
                        result["termination_confirmed_within_30s"] = (
                            termination_confirmed
                            and termination_elapsed <= TIMEOUT_HANDLING_WINDOW_SECONDS
                        )
                        result["monitoring_duration_seconds"] = round(
                            time.time() - start_time, 2
                        )
                        return result

                elif response.status_code == 404:
                    result["error"] = f"Task {task_id} not found"
                    result["final_status"] = "not_found"
                    result["monitoring_duration_seconds"] = round(
                        time.time() - start_time, 2
                    )
                    return result

            except (requests.RequestException, ValueError) as e:
                result["error"] = f"Monitoring request failed: {e}"

            time.sleep(POLL_INTERVAL_SECONDS)

        # Monitor timeout reached
        result["monitoring_duration_seconds"] = round(
            time.time() - start_time, 2
        )
        result["final_status"] = previous_status or "unknown"
        result["timed_out"] = True
        result["error"] = (
            f"Monitoring timed out after {monitor_timeout}s. "
            f"Last known status: {previous_status}"
        )
        return result

    def validate(self, result: dict) -> list[dict]:
        """Validate monitoring results.

        Checks:
        1. Status transitions were recorded
        2. Final status reached a terminal state
        3. If timeout occurred, timeout indication was displayed
        4. If timeout occurred, termination confirmed within 30s
        """
        checks = []

        # Check 1: Status transitions recorded
        transitions = result.get("status_transitions", [])
        checks.append({
            "name": "status_transitions_recorded",
            "passed": len(transitions) > 0,
            "feedback": (
                f"Recorded {len(transitions)} status transition(s): "
                f"{[t['status'] for t in transitions]}"
                if transitions
                else "No status transitions were recorded."
            ),
            "expected": "at least 1 status transition",
            "actual": f"{len(transitions)} transitions",
        })

        # Check 2: Final status is terminal
        final_status = result.get("final_status")
        terminal_states = {
            "completed", "succeeded", "done", "failed", "error", "timeout"
        }
        is_terminal = final_status in terminal_states
        checks.append({
            "name": "final_status_terminal",
            "passed": is_terminal,
            "feedback": (
                f"Task reached terminal status: {final_status}"
                if is_terminal
                else (
                    f"Task did not reach a terminal status. "
                    f"Final status: {final_status}"
                )
            ),
            "expected": f"one of {sorted(terminal_states)}",
            "actual": str(final_status),
        })

        # Check 3: Timeout indication (Requirement 12.4)
        if result.get("timed_out"):
            checks.append({
                "name": "timeout_indication_displayed",
                "passed": result.get("timeout_indication_displayed", False),
                "feedback": (
                    "Timeout indication displayed correctly."
                    if result.get("timeout_indication_displayed")
                    else "Time limit exceeded but no timeout indication was displayed."
                ),
                "expected": "timeout_indication_displayed=True",
                "actual": (
                    f"timeout_indication_displayed="
                    f"{result.get('timeout_indication_displayed')}"
                ),
            })

            # Check 4: Termination within 30s (Requirement 12.4)
            checks.append({
                "name": "termination_confirmed_within_30s",
                "passed": result.get("termination_confirmed_within_30s", False),
                "feedback": (
                    "Container termination confirmed within 30 seconds."
                    if result.get("termination_confirmed_within_30s")
                    else (
                        "Container was not confirmed terminated within "
                        "30 seconds after timeout."
                    )
                ),
                "expected": "termination_confirmed_within_30s=True",
                "actual": (
                    f"termination_confirmed_within_30s="
                    f"{result.get('termination_confirmed_within_30s')}"
                ),
            })

        return checks

    def teardown(self) -> None:
        """No teardown required; monitoring is read-only."""
        pass

    def get_hints(self) -> list[str]:
        return [
            "Use GET /api/serverless/tasks/<task_id> to check task status.",
            "Poll every 2 seconds to observe status transitions.",
            "A task goes through: pending → running → completed/failed/timeout.",
            "If the task times out, verify the container is terminated within 30s.",
            "Use the task_id from Exercise 01 to monitor a real task.",
        ]

    def get_instructions(self) -> Optional[str]:
        return (
            "In this exercise, you will monitor a running serverless task:\n\n"
            "Steps:\n"
            "1. Use the task_id from a previously submitted task\n"
            "2. Poll GET /api/serverless/tasks/<task_id> every 2 seconds\n"
            "3. Observe the status transitions (pending → running → done)\n"
            "4. If the task exceeds its time limit:\n"
            "   - A timeout indication should be displayed\n"
            "   - The container must be terminated within 30 seconds\n\n"
            "Expected status values:\n"
            "  - pending: Task queued for execution\n"
            "  - running: Container is executing\n"
            "  - completed: Task finished successfully\n"
            "  - failed: Task encountered an error\n"
            "  - timeout: Task exceeded its time limit"
        )


def _verify_termination(
    api_base_url: str, task_id: str, headers: dict
) -> bool:
    """Verify that a timed-out task's container has been terminated.

    Polls the task status for up to 30 seconds to confirm the container
    is terminated after a timeout.

    Args:
        api_base_url: Base URL for the platform API.
        task_id: The task identifier.
        headers: HTTP headers.

    Returns:
        True if container termination is confirmed within 30 seconds.
    """
    start = time.time()
    while time.time() - start < TIMEOUT_HANDLING_WINDOW_SECONDS:
        try:
            response = requests.get(
                f"{api_base_url}/serverless/tasks/{task_id}",
                headers=headers,
                timeout=5,
            )
            if response.status_code == 200:
                data = response.json()
                container_status = data.get("container_status", "").lower()
                if container_status in ("terminated", "removed", "cleaned"):
                    return True
        except (requests.RequestException, ValueError):
            pass
        time.sleep(2)
    return False

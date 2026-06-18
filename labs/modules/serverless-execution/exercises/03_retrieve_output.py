"""Exercise 3: Retrieve Execution Output.

Retrieve the output of a completed serverless task. Handles the case
where output is requested before the task has finished executing,
returning an "in progress" message with current status.
"""

import time
from typing import Optional

import requests

from labs.templates.exercise_base import Exercise


class RetrieveOutputExercise(Exercise):
    """Retrieve the output of a completed serverless task."""

    @property
    def exercise_id(self) -> str:
        return "03_retrieve_output"

    @property
    def name(self) -> str:
        return "Retrieve Execution Output"

    @property
    def description(self) -> str:
        return (
            "Retrieve the output of a completed serverless task. If output "
            "is retrieved before the task completes, an 'in progress' message "
            "with the current status is displayed."
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
        """Retrieve the output of a serverless task.

        Args:
            submission: Must contain:
                - task_id (str): ID of the task to retrieve output from
                - api_base_url (str): Base URL of the platform API
                - auth_token (str, optional): Authorization token
                - attempt_premature_retrieval (bool, optional): If True,
                  attempt retrieval immediately (possibly before completion)
                  to test the "in progress" handling. Defaults to False.

        Returns:
            Dict with retrieval results including output content,
            in-progress handling, and completion status.
        """
        task_id = submission.get("task_id", "")
        api_base_url = submission.get(
            "api_base_url", "http://localhost:5000/api"
        )
        auth_token = submission.get("auth_token")
        attempt_premature = submission.get("attempt_premature_retrieval", False)

        result = {
            "task_id": task_id,
            "output_retrieved": False,
            "output_content": None,
            "premature_retrieval_attempted": attempt_premature,
            "in_progress_message_received": False,
            "in_progress_status": None,
            "task_completed": False,
            "retrieval_after_completion": False,
            "error": None,
        }

        if not task_id:
            result["error"] = "No task_id provided"
            return result

        headers = {"Content-Type": "application/json"}
        if auth_token:
            headers["Authorization"] = f"Bearer {auth_token}"

        # If requested, attempt premature retrieval to test Req 12.5
        if attempt_premature:
            premature_result = _attempt_output_retrieval(
                api_base_url, task_id, headers
            )
            if not premature_result["completed"]:
                result["in_progress_message_received"] = (
                    premature_result["in_progress_message"] is not None
                )
                result["in_progress_status"] = premature_result.get(
                    "current_status"
                )
            else:
                # Task already completed at the time of premature attempt
                result["task_completed"] = True
                result["output_retrieved"] = True
                result["output_content"] = premature_result["output"]
                result["retrieval_after_completion"] = True
                return result

        # Wait for task completion, then retrieve output
        completion_result = _wait_and_retrieve(
            api_base_url, task_id, headers, timeout_seconds=60
        )
        result["task_completed"] = completion_result["completed"]
        result["output_retrieved"] = completion_result["output_retrieved"]
        result["output_content"] = completion_result["output"]

        if completion_result["completed"] and completion_result["output_retrieved"]:
            result["retrieval_after_completion"] = True

        if completion_result.get("error"):
            result["error"] = completion_result["error"]

        return result

    def validate(self, result: dict) -> list[dict]:
        """Validate output retrieval results.

        Checks:
        1. Output was successfully retrieved after completion
        2. If premature retrieval was attempted, "in progress" message was shown
        3. Output content is non-empty for completed tasks
        """
        checks = []

        # Check 1: Output retrieved successfully
        checks.append({
            "name": "output_retrieved",
            "passed": result.get("output_retrieved", False),
            "feedback": (
                "Task output retrieved successfully."
                if result.get("output_retrieved")
                else (
                    f"Failed to retrieve output: "
                    f"{result.get('error', 'unknown error')}"
                )
            ),
            "expected": "output_retrieved=True",
            "actual": f"output_retrieved={result.get('output_retrieved')}",
        })

        # Check 2: In-progress handling (Requirement 12.5)
        if result.get("premature_retrieval_attempted"):
            checks.append({
                "name": "in_progress_message_displayed",
                "passed": result.get("in_progress_message_received", False),
                "feedback": (
                    "In-progress message displayed with current status "
                    f"'{result.get('in_progress_status')}' when output "
                    "was requested before completion."
                    if result.get("in_progress_message_received")
                    else (
                        "No 'in progress' message was received when output "
                        "was requested before task completion."
                    )
                ),
                "expected": "in_progress_message with current status",
                "actual": (
                    f"in_progress_message_received="
                    f"{result.get('in_progress_message_received')}, "
                    f"status={result.get('in_progress_status')}"
                ),
            })

        # Check 3: Output content is non-empty
        output = result.get("output_content")
        has_output = output is not None and len(str(output).strip()) > 0
        checks.append({
            "name": "output_content_non_empty",
            "passed": has_output,
            "feedback": (
                f"Output content received ({len(str(output))} characters)."
                if has_output
                else "Output content is empty or None."
            ),
            "expected": "non-empty output content",
            "actual": (
                f"output length={len(str(output))}"
                if output is not None
                else "output=None"
            ),
        })

        return checks

    def teardown(self) -> None:
        """No teardown required; output retrieval is read-only."""
        pass

    def get_hints(self) -> list[str]:
        return [
            "Use GET /api/serverless/tasks/<task_id>/output to retrieve output.",
            "If the task is still running, you'll receive an 'in progress' response.",
            "The in-progress response includes the current task status.",
            "Wait for the task to complete before expecting full output.",
            "Output includes both stdout and stderr from the container.",
        ]

    def get_instructions(self) -> Optional[str]:
        return (
            "In this exercise, you will retrieve the output of a serverless "
            "task:\n\n"
            "Steps:\n"
            "1. Use a task_id from a previously submitted task\n"
            "2. (Optional) Try retrieving output before the task completes\n"
            "   - You should receive an 'in progress' message with status\n"
            "3. Wait for the task to reach 'completed' status\n"
            "4. Retrieve the final output via GET /api/serverless/tasks/"
            "<task_id>/output\n"
            "5. Verify the output contains the expected content\n\n"
            "Behavior when task is still running:\n"
            "  - HTTP 202 response with body:\n"
            "    {\n"
            '      "status": "in_progress",\n'
            '      "message": "Task is still executing",\n'
            '      "current_status": "running"\n'
            "    }\n\n"
            "Behavior when task is completed:\n"
            "  - HTTP 200 response with body:\n"
            "    {\n"
            '      "status": "completed",\n'
            '      "output": "<stdout content>",\n'
            '      "stderr": "<stderr content>"\n'
            "    }"
        )


def _attempt_output_retrieval(
    api_base_url: str, task_id: str, headers: dict
) -> dict:
    """Attempt to retrieve task output (may be premature).

    Args:
        api_base_url: Base URL for the platform API.
        task_id: The task identifier.
        headers: HTTP headers.

    Returns:
        Dict with completed, output, in_progress_message, and current_status.
    """
    try:
        response = requests.get(
            f"{api_base_url}/serverless/tasks/{task_id}/output",
            headers=headers,
            timeout=5,
        )

        if response.status_code == 200:
            data = response.json()
            return {
                "completed": True,
                "output": data.get("output", ""),
                "in_progress_message": None,
                "current_status": "completed",
            }
        elif response.status_code == 202:
            # Task still in progress (Requirement 12.5)
            data = response.json()
            return {
                "completed": False,
                "output": None,
                "in_progress_message": data.get(
                    "message", "Task is still executing"
                ),
                "current_status": data.get("current_status", "running"),
            }
        else:
            return {
                "completed": False,
                "output": None,
                "in_progress_message": None,
                "current_status": None,
            }
    except (requests.RequestException, ValueError):
        return {
            "completed": False,
            "output": None,
            "in_progress_message": None,
            "current_status": None,
        }


def _wait_and_retrieve(
    api_base_url: str, task_id: str, headers: dict, timeout_seconds: int
) -> dict:
    """Wait for task completion then retrieve output.

    Args:
        api_base_url: Base URL for the platform API.
        task_id: The task identifier.
        headers: HTTP headers.
        timeout_seconds: Maximum time to wait for completion.

    Returns:
        Dict with completed, output_retrieved, output, and error.
    """
    start_time = time.time()
    deadline = start_time + timeout_seconds

    # Wait for completion
    while time.time() < deadline:
        try:
            response = requests.get(
                f"{api_base_url}/serverless/tasks/{task_id}",
                headers=headers,
                timeout=5,
            )
            if response.status_code == 200:
                data = response.json()
                status = data.get("status", "").lower()
                if status in ("completed", "succeeded", "done"):
                    break
                elif status in ("failed", "error", "timeout"):
                    return {
                        "completed": False,
                        "output_retrieved": False,
                        "output": data.get("output"),
                        "error": f"Task ended with status: {status}",
                    }
        except (requests.RequestException, ValueError):
            pass
        time.sleep(2)
    else:
        return {
            "completed": False,
            "output_retrieved": False,
            "output": None,
            "error": f"Task did not complete within {timeout_seconds}s",
        }

    # Retrieve output after completion
    try:
        response = requests.get(
            f"{api_base_url}/serverless/tasks/{task_id}/output",
            headers=headers,
            timeout=5,
        )
        if response.status_code == 200:
            data = response.json()
            return {
                "completed": True,
                "output_retrieved": True,
                "output": data.get("output", ""),
                "error": None,
            }
        else:
            return {
                "completed": True,
                "output_retrieved": False,
                "output": None,
                "error": (
                    f"Output retrieval failed with status {response.status_code}"
                ),
            }
    except (requests.RequestException, ValueError) as e:
        return {
            "completed": True,
            "output_retrieved": False,
            "output": None,
            "error": f"Output retrieval request failed: {e}",
        }

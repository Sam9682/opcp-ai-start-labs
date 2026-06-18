"""Reference solution for Exercise 3: Retrieve Execution Output.

Demonstrates the correct approach to retrieving the output of a
completed serverless task, including handling the case where output
is requested before the task has finished (Requirement 12.5).
"""


def get_solution() -> dict:
    """Return the reference solution submission for output retrieval.

    Returns:
        A dict representing a valid submission that passes all checks.
    """
    return {
        "task_id": "<task_id_from_exercise_01>",
        "api_base_url": "http://localhost:5000/api",
        "auth_token": "your-api-token",
        "attempt_premature_retrieval": True,
    }


def get_curl_command(task_id: str = "<task_id>") -> str:
    """Return the reference curl command for retrieving task output.

    Args:
        task_id: The task identifier.

    Returns:
        The full curl command string to retrieve output.
    """
    return (
        f"curl -X GET http://localhost:5000/api/serverless/tasks/{task_id}/output "
        "-H 'Authorization: Bearer your-api-token'"
    )


def get_in_progress_response_example() -> dict:
    """Return an example response when task is still running.

    Returns:
        Dict representing the HTTP 202 response body.
    """
    return {
        "status": "in_progress",
        "message": "Task is still executing",
        "current_status": "running",
    }


def get_completed_response_example() -> dict:
    """Return an example response when task output is available.

    Returns:
        Dict representing the HTTP 200 response body.
    """
    return {
        "status": "completed",
        "output": "Hello Serverless\n",
        "stderr": "",
    }


def get_verification_steps() -> list[str]:
    """Return step-by-step verification instructions.

    Returns:
        List of steps to verify output retrieval behavior.
    """
    return [
        "1. Use a task_id from a previously submitted task",
        "2. (Optional) Immediately request output before task completes:",
        "   - GET /api/serverless/tasks/<task_id>/output",
        "   - Expect HTTP 202 with 'in progress' message and current status",
        "3. Wait for the task to reach 'completed' status",
        "4. Request output after completion:",
        "   - GET /api/serverless/tasks/<task_id>/output",
        "   - Expect HTTP 200 with 'output' field containing stdout",
        "5. Verify output content is non-empty",
    ]


def get_premature_retrieval_explanation() -> str:
    """Explain the in-progress handling behavior (Requirement 12.5).

    Returns:
        Human-readable explanation of premature retrieval handling.
    """
    return (
        "When output is requested before a task completes:\n"
        "  - The API returns HTTP 202 (Accepted, not yet ready)\n"
        "  - Response body includes:\n"
        "    - status: 'in_progress'\n"
        "    - message: Human-readable explanation\n"
        "    - current_status: Current task execution status\n\n"
        "This allows the learner to know the task is still running\n"
        "and provides the current execution phase for context."
    )

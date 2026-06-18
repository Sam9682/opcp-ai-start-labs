"""Reference solution for Exercise 2: Monitor Execution Status.

Demonstrates the correct approach to monitoring a running serverless
task's status transitions and verifying timeout handling when the
container exceeds its time limit.
"""


def get_solution() -> dict:
    """Return the reference solution submission for monitoring status.

    Returns:
        A dict representing a valid submission that passes all checks.
    """
    return {
        "task_id": "<task_id_from_exercise_01>",
        "api_base_url": "http://localhost:5000/api",
        "auth_token": "your-api-token",
        "monitor_timeout_seconds": 60,
    }


def get_curl_command(task_id: str = "<task_id>") -> str:
    """Return the reference curl command for checking task status.

    Args:
        task_id: The task identifier to monitor.

    Returns:
        The full curl command string to query task status.
    """
    return (
        f"curl -X GET http://localhost:5000/api/serverless/tasks/{task_id} "
        "-H 'Authorization: Bearer your-api-token'"
    )


def get_expected_status_transitions() -> list[str]:
    """Return the expected status transition sequence.

    Returns:
        Ordered list of status values a task passes through.
    """
    return [
        "pending   - Task queued for execution",
        "running   - Container is actively executing the command",
        "completed - Task finished successfully (or 'failed'/'timeout')",
    ]


def get_timeout_handling_steps() -> list[str]:
    """Return steps for verifying timeout handling.

    Returns:
        List of steps explaining timeout verification behavior.
    """
    return [
        "1. Submit a task with a short timeout (e.g., timeout_seconds=5)",
        "2. Use a command that runs longer than the timeout (e.g., 'sleep 30')",
        "3. Monitor the task status via GET /api/serverless/tasks/<task_id>",
        "4. Observe the status change to 'timeout'",
        "5. Verify a timeout indication is displayed to the learner",
        "6. Confirm the container is terminated within 30 seconds:",
        "   - container_status should become 'terminated' or 'removed'",
        "   - Termination must occur within 30s of the timeout event",
    ]


def get_verification_steps() -> list[str]:
    """Return step-by-step verification instructions.

    Returns:
        List of steps to verify monitoring behavior.
    """
    return [
        "1. Use the task_id from Exercise 01 (or submit a new task)",
        "2. Poll GET /api/serverless/tasks/<task_id> every 2 seconds",
        "3. Record each distinct status value observed (transitions)",
        "4. Verify at least one transition was recorded",
        "5. Confirm the task reaches a terminal state:",
        "   completed, succeeded, done, failed, error, or timeout",
        "6. If timeout occurs, verify container termination within 30s",
    ]

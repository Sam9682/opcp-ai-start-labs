"""Reference solution for Exercise 4: Verify Automatic Cleanup.

Demonstrates the correct approach to verifying that a completed (or
timed-out) serverless container is automatically terminated and all
compute and network resources are released within 30 seconds.
"""


def get_solution() -> dict:
    """Return the reference solution submission for cleanup verification.

    Returns:
        A dict representing a valid submission that passes all checks.
    """
    return {
        "task_id": "<task_id_from_exercise_01>",
        "api_base_url": "http://localhost:5000/api",
        "auth_token": "your-api-token",
    }


def get_curl_command(task_id: str = "<task_id>") -> str:
    """Return the reference curl command for checking cleanup status.

    Args:
        task_id: The task identifier.

    Returns:
        The full curl command string to query cleanup status.
    """
    return (
        f"curl -X GET http://localhost:5000/api/serverless/tasks/{task_id}/cleanup "
        "-H 'Authorization: Bearer your-api-token'"
    )


def get_expected_cleanup_response() -> dict:
    """Return an example successful cleanup response.

    Returns:
        Dict representing the expected API response after cleanup.
    """
    return {
        "container_status": "terminated",
        "resources_released": True,
        "cleanup_duration_seconds": 2.5,
        "compute_freed": True,
        "network_freed": True,
    }


def get_verification_steps() -> list[str]:
    """Return step-by-step verification instructions.

    Returns:
        List of steps to verify automatic cleanup behavior.
    """
    return [
        "1. Use a task_id from a completed or timed-out task",
        "2. Query GET /api/serverless/tasks/<task_id>/cleanup",
        "3. Verify the container has been terminated:",
        "   - container_status is 'terminated', 'removed', or 'cleaned'",
        "4. Verify all resources have been released:",
        "   - resources_released is True",
        "   - OR both compute_freed and network_freed are True",
        "5. Confirm cleanup happened within 30 seconds:",
        "   - cleanup_duration_seconds <= 30",
        "6. If cleanup is not yet complete, poll every 2 seconds",
    ]


def get_cleanup_requirements() -> str:
    """Explain the cleanup requirements (Requirement 12.3).

    Returns:
        Human-readable explanation of the cleanup timing requirements.
    """
    return (
        "Requirement 12.3 specifies that after a Serverless_Container\n"
        "completes (or times out), the platform must within 30 seconds:\n\n"
        "  1. Terminate the container (not just stop it)\n"
        "  2. Release all compute resources (CPU/memory allocations)\n"
        "  3. Release all network resources (port bindings, network interfaces)\n\n"
        "The exercise verifies all three conditions are met within\n"
        "the 30-second window by polling the cleanup status endpoint."
    )

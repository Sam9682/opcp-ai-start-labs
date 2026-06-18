"""Reference solution for Exercise 1: Submit Serverless Task.

Demonstrates the correct approach to submitting a Serverless_Container
task to the AI-Powered-Store platform and confirming execution completes
within 60 seconds.
"""


def get_solution() -> dict:
    """Return the reference solution submission for task submission.

    Returns:
        A dict representing a valid submission that passes all checks.
    """
    return {
        "image": "python:3.11-slim",
        "command": "python -c \"print('Hello Serverless')\"",
        "api_base_url": "http://localhost:5000/api",
        "env": {},
        "timeout_seconds": 60,
        "auth_token": "your-api-token",
    }


def get_curl_command() -> str:
    """Return the reference curl command for submitting a serverless task.

    Returns:
        The full curl command string to submit a task.
    """
    return (
        "curl -X POST http://localhost:5000/api/serverless/tasks "
        "-H 'Authorization: Bearer your-api-token' "
        "-H 'Content-Type: application/json' "
        "-d '{\"image\": \"python:3.11-slim\", "
        "\"command\": \"python -c \\\"print(\\\\\\\"Hello Serverless\\\\\\\")\\\"\", "
        "\"timeout_seconds\": 60}'"
    )


def get_verification_steps() -> list[str]:
    """Return step-by-step verification instructions.

    Returns:
        List of steps to verify a serverless task submission.
    """
    return [
        "1. Submit a POST request to /api/serverless/tasks with image and command",
        "2. Confirm the response status is 200/201/202 (accepted)",
        "3. Extract the task_id from the response body",
        "4. Poll GET /api/serverless/tasks/<task_id> for status updates",
        "5. Confirm the task reaches 'completed' status within 60 seconds",
        "6. Verify the response includes output from the container",
    ]


def get_payload_example() -> dict:
    """Return an example request payload for the serverless API.

    Returns:
        Dict representing the JSON body for POST /api/serverless/tasks.
    """
    return {
        "image": "python:3.11-slim",
        "command": "python -c \"print('Hello Serverless')\"",
        "env": {"TASK_NAME": "example-task"},
        "timeout_seconds": 30,
    }

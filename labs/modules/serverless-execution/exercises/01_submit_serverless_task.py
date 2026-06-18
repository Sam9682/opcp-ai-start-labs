"""Exercise 1: Submit Serverless Task.

Submit a Serverless_Container task for execution on the AI-Powered-Store platform.
Validates that the task is accepted and returns a task ID, and confirms that the
container executes the specified task and returns output within 60 seconds.
"""

import time
from typing import Optional

import requests

from labs.templates.exercise_base import Exercise


EXECUTION_TIMEOUT_SECONDS = 60


class SubmitServerlessTaskExercise(Exercise):
    """Submit a serverless container task for execution."""

    @property
    def exercise_id(self) -> str:
        return "01_submit_serverless_task"

    @property
    def name(self) -> str:
        return "Submit Serverless Task"

    @property
    def description(self) -> str:
        return (
            "Submit a Serverless_Container task for execution and confirm "
            "that the container executes the specified task and returns "
            "output within 60 seconds."
        )

    @property
    def timeout_minutes(self) -> int:
        return 5

    @property
    def prerequisites(self) -> list[str]:
        return []

    def setup(self) -> None:
        """Verify platform API is reachable."""
        pass

    def execute(self, submission: dict) -> dict:
        """Submit a serverless task to the platform.

        Args:
            submission: Must contain:
                - image (str): Docker image for the serverless container
                - command (str): Command to execute in the container
                - api_base_url (str): Base URL of the platform API
                  (e.g., http://localhost:5000/api)
                - env (dict, optional): Environment variables for the container
                - timeout_seconds (int, optional): Task timeout
                  (defaults to 60)
                - auth_token (str, optional): Authorization token

        Returns:
            Dict with submission results including task_id, acceptance
            status, and execution result.
        """
        image = submission.get("image", "")
        command = submission.get("command", "")
        api_base_url = submission.get(
            "api_base_url", "http://localhost:5000/api"
        )
        env = submission.get("env", {})
        timeout_seconds = submission.get("timeout_seconds", EXECUTION_TIMEOUT_SECONDS)
        auth_token = submission.get("auth_token")

        result = {
            "image": image,
            "command": command,
            "task_submitted": False,
            "task_id": None,
            "submission_status_code": None,
            "submission_response": None,
            "execution_completed": False,
            "execution_output": None,
            "execution_duration_seconds": 0.0,
            "timed_out": False,
            "error": None,
        }

        headers = _build_headers(auth_token)

        # Submit the serverless task
        submit_result = _submit_task(
            api_base_url, image, command, env, timeout_seconds, headers
        )
        result["task_submitted"] = submit_result["submitted"]
        result["task_id"] = submit_result["task_id"]
        result["submission_status_code"] = submit_result["status_code"]
        result["submission_response"] = submit_result["response_body"]

        if not submit_result["submitted"]:
            result["error"] = submit_result.get("error", "Task submission failed")
            return result

        # Wait for execution to complete (up to 60 seconds)
        task_id = submit_result["task_id"]
        exec_result = _wait_for_completion(
            api_base_url, task_id, timeout_seconds, headers
        )
        result["execution_completed"] = exec_result["completed"]
        result["execution_output"] = exec_result["output"]
        result["execution_duration_seconds"] = exec_result["duration_seconds"]
        result["timed_out"] = exec_result["timed_out"]

        if exec_result.get("error"):
            result["error"] = exec_result["error"]

        return result

    def validate(self, result: dict) -> list[dict]:
        """Validate the serverless task submission results.

        Checks:
        1. Task was submitted successfully
        2. Task ID was assigned
        3. Container executed and returned output within 60 seconds
        4. No timeout occurred
        """
        checks = []

        # Check 1: Task submitted
        checks.append({
            "name": "task_submitted",
            "passed": result.get("task_submitted", False),
            "feedback": (
                "Serverless task submitted successfully."
                if result.get("task_submitted")
                else (
                    f"Task submission failed: "
                    f"{result.get('error', 'unknown error')}"
                )
            ),
            "expected": "submitted=True",
            "actual": f"submitted={result.get('task_submitted')}",
        })

        if not result.get("task_submitted"):
            return checks

        # Check 2: Task ID assigned
        task_id = result.get("task_id")
        checks.append({
            "name": "task_id_assigned",
            "passed": task_id is not None and len(str(task_id)) > 0,
            "feedback": (
                f"Task assigned ID: {task_id}"
                if task_id
                else "No task ID returned by the platform."
            ),
            "expected": "non-empty task_id",
            "actual": f"task_id={task_id}",
        })

        # Check 3: Execution completed within 60s
        checks.append({
            "name": "execution_completed_within_timeout",
            "passed": result.get("execution_completed", False),
            "feedback": (
                f"Container executed in "
                f"{result.get('execution_duration_seconds', 0):.1f}s."
                if result.get("execution_completed")
                else "Container did not complete execution within 60 seconds."
            ),
            "expected": "completed=True within 60s",
            "actual": (
                f"completed={result.get('execution_completed')}, "
                f"duration={result.get('execution_duration_seconds', 0):.1f}s"
            ),
        })

        # Check 4: No timeout
        checks.append({
            "name": "no_timeout",
            "passed": not result.get("timed_out", True),
            "feedback": (
                "Task completed without exceeding time limit."
                if not result.get("timed_out")
                else "Task exceeded its time limit."
            ),
            "expected": "timed_out=False",
            "actual": f"timed_out={result.get('timed_out')}",
        })

        return checks

    def teardown(self) -> None:
        """No teardown required; serverless containers auto-cleanup."""
        pass

    def get_hints(self) -> list[str]:
        return [
            "Use POST /api/serverless/tasks to submit a serverless task.",
            "The request body must include 'image' and 'command' fields.",
            "The platform returns a task_id upon successful submission.",
            "Execution should complete within 60 seconds for typical tasks.",
        ]

    def get_instructions(self) -> Optional[str]:
        return (
            "In this exercise, you will submit a serverless container task "
            "to the AI-Powered-Store platform.\n\n"
            "Steps:\n"
            "1. Define a task with a Docker image and command\n"
            "2. Submit the task via POST /api/serverless/tasks\n"
            "3. Confirm the platform accepts the task and returns a task ID\n"
            "4. Wait for the container to execute (max 60 seconds)\n"
            "5. Verify the task completed successfully\n\n"
            "Example task submission:\n"
            "  POST /api/serverless/tasks\n"
            "  {\n"
            '    "image": "python:3.11-slim",\n'
            '    "command": "python -c \\"print(\'Hello Serverless\')\\\"",\n'
            '    "timeout_seconds": 30\n'
            "  }"
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


def _submit_task(
    api_base_url: str,
    image: str,
    command: str,
    env: dict,
    timeout_seconds: int,
    headers: dict,
) -> dict:
    """Submit a serverless task via the platform API.

    Args:
        api_base_url: Base URL for the platform API.
        image: Docker image for the task.
        command: Command to execute.
        env: Environment variables.
        timeout_seconds: Task timeout.
        headers: HTTP headers.

    Returns:
        Dict with submitted, task_id, status_code, response_body, and error.
    """
    try:
        payload = {
            "image": image,
            "command": command,
            "env": env,
            "timeout_seconds": timeout_seconds,
        }
        response = requests.post(
            f"{api_base_url}/serverless/tasks",
            json=payload,
            headers=headers,
            timeout=10,
        )
        response_body = response.text
        task_id = None

        if 200 <= response.status_code < 300:
            try:
                data = response.json()
                task_id = data.get("task_id")
            except ValueError:
                pass

        return {
            "submitted": response.status_code in (200, 201, 202),
            "task_id": task_id,
            "status_code": response.status_code,
            "response_body": response_body,
            "error": None if response.status_code < 400 else response_body,
        }
    except requests.RequestException as e:
        return {
            "submitted": False,
            "task_id": None,
            "status_code": None,
            "response_body": None,
            "error": f"Failed to submit task: {e}",
        }


def _wait_for_completion(
    api_base_url: str,
    task_id: str,
    timeout_seconds: int,
    headers: dict,
) -> dict:
    """Wait for the serverless task to complete.

    Polls the task status endpoint until completion or timeout.

    Args:
        api_base_url: Base URL for the platform API.
        task_id: The task identifier to monitor.
        timeout_seconds: Maximum time to wait.
        headers: HTTP headers.

    Returns:
        Dict with completed, output, duration_seconds, timed_out, and error.
    """
    start_time = time.time()
    deadline = start_time + timeout_seconds

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
                    elapsed = time.time() - start_time
                    return {
                        "completed": True,
                        "output": data.get("output", ""),
                        "duration_seconds": round(elapsed, 2),
                        "timed_out": False,
                        "error": None,
                    }
                elif status in ("failed", "error"):
                    elapsed = time.time() - start_time
                    return {
                        "completed": False,
                        "output": data.get("output", ""),
                        "duration_seconds": round(elapsed, 2),
                        "timed_out": False,
                        "error": data.get("error", "Task execution failed"),
                    }
                elif status == "timeout":
                    elapsed = time.time() - start_time
                    return {
                        "completed": False,
                        "output": data.get("output", ""),
                        "duration_seconds": round(elapsed, 2),
                        "timed_out": True,
                        "error": "Task exceeded its time limit",
                    }
        except (requests.RequestException, ValueError):
            pass

        time.sleep(2)

    elapsed = time.time() - start_time
    return {
        "completed": False,
        "output": None,
        "duration_seconds": round(elapsed, 2),
        "timed_out": True,
        "error": f"Task did not complete within {timeout_seconds} seconds",
    }

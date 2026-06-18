"""Exercise 3: Monitor GPU Utilization.

Monitor GPU compute utilization from within a MIG-enabled container.
Verify that GPU compute is accessible by executing a sample compute
operation and confirming it completes without error within 60 seconds.
"""

import json
import time
from typing import Optional

from labs.templates.exercise_base import Exercise


COMPUTE_TIMEOUT_SECONDS = 60


class MonitorGPUExercise(Exercise):
    """Monitor GPU utilization from within a MIG-enabled container."""

    @property
    def exercise_id(self) -> str:
        return "03_monitor_gpu"

    @property
    def name(self) -> str:
        return "Monitor GPU Utilization"

    @property
    def description(self) -> str:
        return (
            "Monitor GPU compute utilization from within a MIG-enabled "
            "container and verify that GPU compute is accessible by executing "
            "a sample compute operation within 60 seconds."
        )

    @property
    def timeout_minutes(self) -> int:
        return 10

    @property
    def prerequisites(self) -> list[str]:
        return ["02_deploy_with_mig"]

    def setup(self) -> None:
        """Verify a MIG-enabled container is running."""
        pass

    def execute(self, submission: dict) -> dict:
        """Execute a sample compute operation in the MIG container.

        Args:
            submission: Must contain:
                - app_name (str): Name of the deployed MIG application
                - container_id (str, optional): Container ID to execute in
                - compute_command (str, optional): Custom compute command
                  (defaults to nvidia-smi based check)
                - api_endpoint (str, optional): Platform API endpoint

        Returns:
            Dict with GPU monitoring and compute accessibility results.
        """
        app_name = submission.get("app_name", "")
        container_id = submission.get("container_id", "")
        compute_command = submission.get(
            "compute_command",
            "python3 -c \"import torch; t = torch.cuda.FloatTensor(256); print('GPU compute OK')\"",
        )
        api_endpoint = submission.get(
            "api_endpoint", "http://localhost:5000/api"
        )

        result = {
            "app_name": app_name,
            "container_id": container_id,
            "compute_accessible": False,
            "compute_output": None,
            "compute_duration_seconds": None,
            "gpu_utilization": None,
            "memory_usage_mb": None,
            "error": None,
        }

        if not app_name and not container_id:
            result["error"] = (
                "Either 'app_name' or 'container_id' is required."
            )
            return result

        # Step 1: Get GPU utilization metrics
        utilization = _query_gpu_utilization(
            app_name, container_id, api_endpoint
        )
        if utilization["success"]:
            result["gpu_utilization"] = utilization.get("utilization_percent")
            result["memory_usage_mb"] = utilization.get("memory_usage_mb")

        # Step 2: Execute sample compute operation within timeout
        compute_result = _execute_compute_in_container(
            app_name, container_id, compute_command, api_endpoint,
            timeout=COMPUTE_TIMEOUT_SECONDS,
        )
        result["compute_accessible"] = compute_result["success"]
        result["compute_output"] = compute_result.get("output")
        result["compute_duration_seconds"] = compute_result.get(
            "duration_seconds"
        )
        if not compute_result["success"]:
            result["error"] = compute_result.get("error")

        return result

    def validate(self, result: dict) -> list[dict]:
        """Validate GPU compute accessibility.

        Checks:
        1. Sample compute operation completed without error
        2. Compute completed within 60 seconds
        3. GPU utilization metrics are available
        """
        checks = []

        # Check 1: Compute operation completed successfully
        compute_accessible = result.get("compute_accessible", False)
        error = result.get("error")
        checks.append({
            "name": "compute_accessible",
            "passed": compute_accessible,
            "feedback": (
                "GPU compute is accessible from within the container."
                if compute_accessible
                else (
                    f"GPU compute not accessible: "
                    f"{error or 'Unknown error'}"
                )
            ),
            "expected": "compute_accessible=True",
            "actual": f"compute_accessible={compute_accessible}",
        })

        # Check 2: Compute completed within timeout
        duration = result.get("compute_duration_seconds")
        within_timeout = (
            duration is not None and duration <= COMPUTE_TIMEOUT_SECONDS
        )
        checks.append({
            "name": "compute_within_timeout",
            "passed": compute_accessible and within_timeout,
            "feedback": (
                f"Compute operation completed in {duration:.1f}s "
                f"(within {COMPUTE_TIMEOUT_SECONDS}s limit)."
                if compute_accessible and within_timeout
                else (
                    f"Compute operation did not complete within "
                    f"{COMPUTE_TIMEOUT_SECONDS}s."
                    + (f" Took {duration:.1f}s." if duration else "")
                )
            ),
            "expected": f"duration <= {COMPUTE_TIMEOUT_SECONDS}s",
            "actual": (
                f"{duration:.1f}s" if duration else "not completed"
            ),
        })

        # Check 3: GPU utilization metrics available
        gpu_util = result.get("gpu_utilization")
        memory_usage = result.get("memory_usage_mb")
        metrics_available = gpu_util is not None or memory_usage is not None
        checks.append({
            "name": "gpu_metrics_available",
            "passed": metrics_available,
            "feedback": (
                f"GPU metrics retrieved: utilization={gpu_util}%, "
                f"memory={memory_usage}MB."
                if metrics_available
                else "GPU utilization metrics are not available."
            ),
            "expected": "GPU utilization or memory metrics present",
            "actual": (
                f"utilization={gpu_util}%, memory={memory_usage}MB"
                if metrics_available
                else "no metrics"
            ),
        })

        return checks

    def teardown(self) -> None:
        """No teardown - container cleanup handled by exercise 04."""
        pass

    def get_hints(self) -> list[str]:
        return [
            "Use 'nvidia-smi' inside the container to view GPU utilization.",
            "A simple PyTorch or CUDA operation can verify GPU compute access.",
            "The compute operation must complete within 60 seconds.",
            "Check GPU metrics via: GET /api/gpu/utilization?app=<app_name>",
        ]

    def get_instructions(self) -> Optional[str]:
        return (
            "Monitor GPU utilization from within a MIG-enabled container:\n\n"
            "1. Connect to your running MIG-enabled application container\n"
            "2. Check GPU visibility:\n"
            "   nvidia-smi\n"
            "3. Execute a sample compute operation to verify GPU access:\n"
            "   python3 -c \"import torch; t = torch.cuda.FloatTensor(256); "
            "print('GPU compute OK')\"\n"
            "4. Monitor GPU utilization metrics via the platform API:\n"
            "   GET /api/gpu/utilization?app=my-gpu-app\n\n"
            "The compute operation must complete without error within 60 "
            "seconds to confirm GPU accessibility."
        )


def _query_gpu_utilization(
    app_name: str, container_id: str, api_endpoint: str
) -> dict:
    """Query GPU utilization metrics for the container.

    Args:
        app_name: Application name.
        container_id: Container identifier.
        api_endpoint: Platform API base URL.

    Returns:
        Dict with success flag and utilization data.
    """
    import urllib.request
    import urllib.error

    identifier = app_name or container_id
    url = f"{api_endpoint}/gpu/utilization?app={identifier}"

    try:
        req = urllib.request.Request(url, method="GET")
        req.add_header("Content-Type", "application/json")
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))
            return {
                "success": True,
                "utilization_percent": data.get("utilization_percent"),
                "memory_usage_mb": data.get("memory_usage_mb"),
            }
    except (urllib.error.URLError, json.JSONDecodeError) as e:
        return {"success": False, "error": str(e)}


def _execute_compute_in_container(
    app_name: str,
    container_id: str,
    compute_command: str,
    api_endpoint: str,
    timeout: int = COMPUTE_TIMEOUT_SECONDS,
) -> dict:
    """Execute a sample compute operation inside the container.

    Args:
        app_name: Application name.
        container_id: Container ID for direct exec.
        compute_command: Command to execute for compute verification.
        api_endpoint: Platform API base URL.
        timeout: Maximum seconds to wait for compute completion.

    Returns:
        Dict with success flag, output, and duration.
    """
    import urllib.request
    import urllib.error

    url = f"{api_endpoint}/containers/exec"
    payload = json.dumps({
        "app_name": app_name,
        "container_id": container_id,
        "command": compute_command,
        "timeout_seconds": timeout,
    }).encode("utf-8")

    start_time = time.time()

    try:
        req = urllib.request.Request(url, data=payload, method="POST")
        req.add_header("Content-Type", "application/json")
        with urllib.request.urlopen(req, timeout=timeout + 5) as response:
            data = json.loads(response.read().decode("utf-8"))
            duration = time.time() - start_time
            exit_code = data.get("exit_code", -1)
            output = data.get("output", "")

            if exit_code == 0:
                return {
                    "success": True,
                    "output": output,
                    "duration_seconds": duration,
                }
            else:
                return {
                    "success": False,
                    "output": output,
                    "duration_seconds": duration,
                    "error": (
                        f"Compute command exited with code {exit_code}: "
                        f"{data.get('stderr', '')}"
                    ),
                }
    except urllib.error.URLError as e:
        return {
            "success": False,
            "duration_seconds": time.time() - start_time,
            "error": f"Failed to execute compute in container: {e.reason}",
        }
    except json.JSONDecodeError as e:
        return {
            "success": False,
            "duration_seconds": time.time() - start_time,
            "error": f"Invalid response from exec endpoint: {e}",
        }

"""Exercise 2: Deploy with MIG Profile.

Deploy a Docker application requesting a specific MIG (Multi-Instance GPU)
profile and verify that the GPU allocation is confirmed within 30 seconds.
"""

import json
import time
from typing import Optional

from labs.templates.exercise_base import Exercise


ALLOCATION_TIMEOUT_SECONDS = 30


class DeployWithMIGExercise(Exercise):
    """Deploy a Docker application with a specific MIG profile."""

    @property
    def exercise_id(self) -> str:
        return "02_deploy_with_mig"

    @property
    def name(self) -> str:
        return "Deploy with MIG Profile"

    @property
    def description(self) -> str:
        return (
            "Deploy a Docker application requesting a specific MIG profile "
            "and confirm that the GPU allocation is assigned within 30 seconds."
        )

    @property
    def timeout_minutes(self) -> int:
        return 10

    @property
    def prerequisites(self) -> list[str]:
        return ["01_list_mig_profiles"]

    def setup(self) -> None:
        """Verify platform connectivity before deployment."""
        pass

    def execute(self, submission: dict) -> dict:
        """Deploy an application with a MIG profile request.

        Args:
            submission: Must contain:
                - app_name (str): Name of the Docker application to deploy
                - mig_profile (str): Requested MIG profile identifier
                - docker_image (str): Docker image to deploy
                - api_endpoint (str, optional): Platform API endpoint
                - method (str, optional): Deployment method - "cli" or "api"

        Returns:
            Dict with deployment and allocation result.
        """
        app_name = submission.get("app_name", "")
        mig_profile = submission.get("mig_profile", "")
        docker_image = submission.get("docker_image", "")
        api_endpoint = submission.get(
            "api_endpoint", "http://localhost:5000/api"
        )
        method = submission.get("method", "api")

        result = {
            "app_name": app_name,
            "requested_profile": mig_profile,
            "docker_image": docker_image,
            "method": method,
            "deployed": False,
            "allocation_confirmed": False,
            "assigned_profile": None,
            "allocation_time_seconds": None,
            "alternative_profiles": [],
            "error": None,
        }

        # Validate required fields
        if not app_name:
            result["error"] = "Field 'app_name' is required."
            return result
        if not mig_profile:
            result["error"] = "Field 'mig_profile' is required."
            return result
        if not docker_image:
            result["error"] = "Field 'docker_image' is required."
            return result

        # Attempt deployment
        deploy_result = _deploy_with_mig(
            app_name, mig_profile, docker_image, api_endpoint, method
        )

        if deploy_result["success"]:
            result["deployed"] = True
            # Query allocation status within timeout
            allocation = _wait_for_allocation(
                app_name, mig_profile, api_endpoint,
                timeout=ALLOCATION_TIMEOUT_SECONDS
            )
            result["allocation_confirmed"] = allocation["confirmed"]
            result["assigned_profile"] = allocation.get("assigned_profile")
            result["allocation_time_seconds"] = allocation.get("elapsed_seconds")
        elif deploy_result.get("profile_unavailable"):
            result["error"] = (
                f"Requested MIG profile '{mig_profile}' is at capacity."
            )
            result["alternative_profiles"] = deploy_result.get(
                "alternatives", []
            )
        else:
            result["error"] = deploy_result.get("error", "Deployment failed.")

        return result

    def validate(self, result: dict) -> list[dict]:
        """Validate the MIG deployment and allocation.

        Checks:
        1. Application was deployed successfully
        2. GPU allocation confirmed within 30 seconds
        3. Assigned profile matches the requested profile
        4. Alternative profiles suggested if requested profile unavailable
        """
        checks = []

        # Check 1: Deployment succeeded
        deployed = result.get("deployed", False)
        error = result.get("error")

        if error and result.get("alternative_profiles"):
            # Profile unavailable - check for alternatives (Req 11.4)
            alternatives = result.get("alternative_profiles", [])
            checks.append({
                "name": "deployment_status",
                "passed": False,
                "feedback": (
                    f"Requested profile is at capacity. "
                    f"Alternatives available: "
                    f"{', '.join(p.get('id', str(p)) for p in alternatives)}"
                ),
                "expected": "Deployment successful",
                "actual": f"Profile unavailable, {len(alternatives)} alternative(s) suggested",
            })
            checks.append({
                "name": "alternative_profiles_suggested",
                "passed": len(alternatives) > 0,
                "feedback": (
                    f"Platform suggested {len(alternatives)} alternative "
                    f"profile(s) closest in compute capability."
                    if alternatives
                    else "No alternative profiles were suggested."
                ),
                "expected": "At least 1 alternative profile",
                "actual": f"{len(alternatives)} alternative(s)",
            })
            return checks

        checks.append({
            "name": "deployment_status",
            "passed": deployed,
            "feedback": (
                f"Application '{result.get('app_name')}' deployed successfully."
                if deployed
                else f"Deployment failed: {error or 'Unknown error'}"
            ),
            "expected": "deployed=True",
            "actual": f"deployed={deployed}",
        })

        if not deployed:
            return checks

        # Check 2: GPU allocation confirmed within 30s
        allocation_confirmed = result.get("allocation_confirmed", False)
        allocation_time = result.get("allocation_time_seconds")
        within_timeout = (
            allocation_time is not None
            and allocation_time <= ALLOCATION_TIMEOUT_SECONDS
        )

        checks.append({
            "name": "allocation_within_timeout",
            "passed": allocation_confirmed and within_timeout,
            "feedback": (
                f"GPU allocation confirmed in {allocation_time:.1f}s "
                f"(within {ALLOCATION_TIMEOUT_SECONDS}s limit)."
                if allocation_confirmed and within_timeout
                else (
                    f"GPU allocation not confirmed within "
                    f"{ALLOCATION_TIMEOUT_SECONDS}s."
                    + (f" Took {allocation_time:.1f}s." if allocation_time else "")
                )
            ),
            "expected": f"Allocation confirmed within {ALLOCATION_TIMEOUT_SECONDS}s",
            "actual": (
                f"{allocation_time:.1f}s" if allocation_time
                else "not confirmed"
            ),
        })

        # Check 3: Assigned profile matches requested
        requested = result.get("requested_profile", "")
        assigned = result.get("assigned_profile", "")
        profile_matches = assigned == requested

        checks.append({
            "name": "profile_assignment",
            "passed": profile_matches,
            "feedback": (
                f"Assigned MIG profile '{assigned}' matches requested "
                f"profile '{requested}'."
                if profile_matches
                else (
                    f"Profile mismatch: requested '{requested}', "
                    f"assigned '{assigned or 'none'}'."
                )
            ),
            "expected": f"assigned_profile='{requested}'",
            "actual": f"assigned_profile='{assigned}'",
        })

        return checks

    def teardown(self) -> None:
        """Teardown handled by exercise 04 (release GPU resources)."""
        pass

    def get_hints(self) -> list[str]:
        return [
            "Use the MIG profile ID from exercise 01 in your deployment request.",
            "The deploy API accepts a 'gpu_profile' field in the request body.",
            "Check GPU allocation status with: GET /api/gpu/allocations?app=<app_name>",
            "Allocation must be confirmed within 30 seconds of deployment.",
        ]

    def get_instructions(self) -> Optional[str]:
        return (
            "Deploy a Docker application with a specific MIG GPU profile:\n\n"
            "1. Choose a MIG profile from the available profiles (exercise 01)\n"
            "2. Deploy your application with the selected profile:\n"
            "   POST /api/deployments\n"
            "   {\n"
            '     "app_name": "my-gpu-app",\n'
            '     "docker_image": "my-gpu-image:latest",\n'
            '     "gpu_profile": "1g.5gb",\n'
            '     "action": "start"\n'
            "   }\n"
            "3. The platform will allocate the GPU resources and assign the\n"
            "   requested MIG profile to your container\n"
            "4. Verify the allocation is confirmed within 30 seconds:\n"
            "   GET /api/gpu/allocations?app=my-gpu-app\n\n"
            "If the requested profile is unavailable, the platform will\n"
            "suggest alternative profiles with similar compute capability."
        )


def _deploy_with_mig(
    app_name: str,
    mig_profile: str,
    docker_image: str,
    api_endpoint: str,
    method: str,
) -> dict:
    """Deploy an application with a MIG profile request.

    Args:
        app_name: Application name.
        mig_profile: Requested MIG profile identifier.
        docker_image: Docker image to deploy.
        api_endpoint: Platform API base URL.
        method: Deployment method ("cli" or "api").

    Returns:
        Dict with success flag and optional error/alternatives.
    """
    import urllib.request
    import urllib.error

    if method == "cli":
        return _deploy_via_cli(app_name, mig_profile, docker_image)

    url = f"{api_endpoint}/deployments"
    payload = json.dumps({
        "app_name": app_name,
        "docker_image": docker_image,
        "gpu_profile": mig_profile,
        "action": "start",
    }).encode("utf-8")

    try:
        req = urllib.request.Request(url, data=payload, method="POST")
        req.add_header("Content-Type", "application/json")
        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode("utf-8"))
            return {"success": True, "deployment_id": data.get("id")}
    except urllib.error.HTTPError as e:
        try:
            error_body = json.loads(e.read().decode("utf-8"))
            if e.code == 409 and error_body.get("reason") == "profile_unavailable":
                return {
                    "success": False,
                    "profile_unavailable": True,
                    "alternatives": error_body.get("alternatives", []),
                    "error": error_body.get("message", "Profile at capacity"),
                }
        except (json.JSONDecodeError, AttributeError):
            pass
        return {
            "success": False,
            "error": f"API returned HTTP {e.code}: {e.reason}",
        }
    except urllib.error.URLError as e:
        return {
            "success": False,
            "error": (
                f"Failed to reach API endpoint {url}: {e.reason}. "
                "Check network connectivity."
            ),
        }


def _deploy_via_cli(
    app_name: str, mig_profile: str, docker_image: str
) -> dict:
    """Deploy via the platform CLI tool.

    Args:
        app_name: Application name.
        mig_profile: Requested MIG profile identifier.
        docker_image: Docker image to deploy.

    Returns:
        Dict with success flag and optional error.
    """
    import subprocess

    cli_path = "/usr/local/bin/aipoweredstore_cli.py"
    try:
        proc = subprocess.run(
            [
                cli_path, "deploy",
                "--app", app_name,
                "--image", docker_image,
                "--gpu-profile", mig_profile,
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if proc.returncode == 0:
            return {"success": True}
        elif "profile_unavailable" in proc.stderr.lower():
            # Parse alternatives from CLI output
            alternatives = _parse_cli_alternatives(proc.stdout)
            return {
                "success": False,
                "profile_unavailable": True,
                "alternatives": alternatives,
                "error": proc.stderr.strip(),
            }
        else:
            return {
                "success": False,
                "error": f"CLI exit code {proc.returncode}: {proc.stderr}",
            }
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "CLI command timed out after 30s."}
    except (FileNotFoundError, OSError) as e:
        return {"success": False, "error": f"Failed to execute CLI: {e}"}


def _wait_for_allocation(
    app_name: str,
    expected_profile: str,
    api_endpoint: str,
    timeout: int = ALLOCATION_TIMEOUT_SECONDS,
) -> dict:
    """Poll GPU allocation status until confirmed or timeout.

    Args:
        app_name: Application name to check.
        expected_profile: Expected MIG profile to be assigned.
        api_endpoint: Platform API base URL.
        timeout: Maximum seconds to wait.

    Returns:
        Dict with confirmed flag, assigned profile, and elapsed time.
    """
    import urllib.request
    import urllib.error

    url = f"{api_endpoint}/gpu/allocations?app={app_name}"
    start_time = time.time()
    poll_interval = 2  # seconds

    while True:
        elapsed = time.time() - start_time
        if elapsed > timeout:
            return {
                "confirmed": False,
                "assigned_profile": None,
                "elapsed_seconds": elapsed,
            }

        try:
            req = urllib.request.Request(url, method="GET")
            req.add_header("Content-Type", "application/json")
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode("utf-8"))
                allocations = data.get("allocations", [])
                for alloc in allocations:
                    if alloc.get("app_name") == app_name:
                        assigned = alloc.get("profile_id", "")
                        if assigned:
                            return {
                                "confirmed": True,
                                "assigned_profile": assigned,
                                "elapsed_seconds": time.time() - start_time,
                            }
        except (urllib.error.URLError, json.JSONDecodeError):
            pass

        time.sleep(poll_interval)


def _parse_cli_alternatives(output: str) -> list[dict]:
    """Parse alternative profile suggestions from CLI output.

    Args:
        output: CLI stdout content.

    Returns:
        List of alternative profile dicts.
    """
    alternatives = []
    try:
        data = json.loads(output)
        if isinstance(data, dict) and "alternatives" in data:
            return data["alternatives"]
    except (json.JSONDecodeError, ValueError):
        pass

    # Line-based fallback
    in_alternatives = False
    for line in output.strip().splitlines():
        line = line.strip()
        if "alternative" in line.lower():
            in_alternatives = True
            continue
        if in_alternatives and line:
            parts = line.split()
            if len(parts) >= 2:
                alternatives.append({
                    "id": parts[0],
                    "compute_capability": parts[1],
                })
    return alternatives

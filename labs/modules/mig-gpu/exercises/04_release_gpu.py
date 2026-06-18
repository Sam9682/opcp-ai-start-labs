"""Exercise 4: Release GPU Resources.

Release allocated MIG GPU resources and verify that the MIG profile
allocation is removed from the active GPU allocation status within
30 seconds.
"""

import json
import time
from typing import Optional

from labs.templates.exercise_base import Exercise


RELEASE_TIMEOUT_SECONDS = 30


class ReleaseGPUExercise(Exercise):
    """Release MIG GPU resources and verify deallocation."""

    @property
    def exercise_id(self) -> str:
        return "04_release_gpu"

    @property
    def name(self) -> str:
        return "Release GPU Resources"

    @property
    def description(self) -> str:
        return (
            "Release allocated MIG GPU resources and verify that the "
            "profile is removed from the active GPU allocation status "
            "within 30 seconds."
        )

    @property
    def timeout_minutes(self) -> int:
        return 10

    @property
    def prerequisites(self) -> list[str]:
        return ["02_deploy_with_mig"]

    def setup(self) -> None:
        """Verify an active GPU allocation exists for release."""
        pass

    def execute(self, submission: dict) -> dict:
        """Release GPU resources for the specified application.

        Args:
            submission: Must contain:
                - app_name (str): Name of the deployed MIG application
                - mig_profile (str, optional): Profile to release (if multiple)
                - api_endpoint (str, optional): Platform API endpoint
                - method (str, optional): Release method - "cli" or "api"

        Returns:
            Dict with release operation and verification results.
        """
        app_name = submission.get("app_name", "")
        mig_profile = submission.get("mig_profile", "")
        api_endpoint = submission.get(
            "api_endpoint", "http://localhost:5000/api"
        )
        method = submission.get("method", "api")

        result = {
            "app_name": app_name,
            "mig_profile": mig_profile,
            "method": method,
            "release_requested": False,
            "profile_removed": False,
            "release_time_seconds": None,
            "error": None,
        }

        if not app_name:
            result["error"] = "Field 'app_name' is required."
            return result

        # Step 1: Request GPU resource release
        release_result = _release_gpu_resources(
            app_name, mig_profile, api_endpoint, method
        )

        if not release_result["success"]:
            result["error"] = release_result.get(
                "error", "Failed to release GPU resources."
            )
            return result

        result["release_requested"] = True

        # Step 2: Verify profile removed from allocations within 30s
        verification = _wait_for_deallocation(
            app_name, mig_profile, api_endpoint,
            timeout=RELEASE_TIMEOUT_SECONDS,
        )
        result["profile_removed"] = verification["removed"]
        result["release_time_seconds"] = verification.get("elapsed_seconds")

        if not verification["removed"]:
            result["error"] = (
                f"Profile not removed from active allocations within "
                f"{RELEASE_TIMEOUT_SECONDS}s."
            )

        return result

    def validate(self, result: dict) -> list[dict]:
        """Validate GPU resource release.

        Checks:
        1. Release request was successful
        2. Profile removed from active allocations within 30 seconds
        """
        checks = []

        # Check 1: Release request accepted
        release_requested = result.get("release_requested", False)
        error = result.get("error")
        checks.append({
            "name": "release_requested",
            "passed": release_requested,
            "feedback": (
                f"GPU resource release requested for "
                f"'{result.get('app_name')}'."
                if release_requested
                else (
                    f"Release request failed: "
                    f"{error or 'Unknown error'}"
                )
            ),
            "expected": "release_requested=True",
            "actual": f"release_requested={release_requested}",
        })

        if not release_requested:
            return checks

        # Check 2: Profile removed from active allocations within 30s
        profile_removed = result.get("profile_removed", False)
        release_time = result.get("release_time_seconds")
        within_timeout = (
            release_time is not None
            and release_time <= RELEASE_TIMEOUT_SECONDS
        )

        checks.append({
            "name": "profile_removed_within_timeout",
            "passed": profile_removed and within_timeout,
            "feedback": (
                f"MIG profile removed from active allocations in "
                f"{release_time:.1f}s "
                f"(within {RELEASE_TIMEOUT_SECONDS}s limit)."
                if profile_removed and within_timeout
                else (
                    f"MIG profile not removed from active GPU status "
                    f"within {RELEASE_TIMEOUT_SECONDS}s."
                    + (
                        f" Took {release_time:.1f}s."
                        if release_time
                        else ""
                    )
                )
            ),
            "expected": (
                f"Profile removed within {RELEASE_TIMEOUT_SECONDS}s"
            ),
            "actual": (
                f"{release_time:.1f}s"
                if release_time
                else "not removed"
            ),
        })

        return checks

    def teardown(self) -> None:
        """Final cleanup - ensure no GPU resources remain allocated."""
        pass

    def get_hints(self) -> list[str]:
        return [
            "Stop the application to release GPU resources: "
            "POST /api/deployments with action='stop'.",
            "Verify allocation removal: GET /api/gpu/allocations?app=<app_name>",
            "The profile must disappear from active allocations within 30s.",
            "If using CLI: aipoweredstore_cli.py gpu release --app <app_name>",
        ]

    def get_instructions(self) -> Optional[str]:
        return (
            "Release MIG GPU resources and verify deallocation:\n\n"
            "1. Stop the MIG-enabled application to release GPU resources:\n"
            "   POST /api/deployments\n"
            "   {\n"
            '     "app_name": "my-gpu-app",\n'
            '     "action": "stop"\n'
            "   }\n"
            "   Or via CLI:\n"
            "   aipoweredstore_cli.py gpu release --app my-gpu-app\n\n"
            "2. Verify the MIG profile is removed from active allocations:\n"
            "   GET /api/gpu/allocations?app=my-gpu-app\n\n"
            "3. The profile must no longer appear in the active GPU\n"
            "   allocation status within 30 seconds of the release request.\n\n"
            "Success criteria: The assigned MIG profile is completely "
            "removed from the platform's active GPU allocation list."
        )


def _release_gpu_resources(
    app_name: str,
    mig_profile: str,
    api_endpoint: str,
    method: str,
) -> dict:
    """Request release of GPU resources for an application.

    Args:
        app_name: Application name.
        mig_profile: Profile to release (optional for targeted release).
        api_endpoint: Platform API base URL.
        method: Release method ("cli" or "api").

    Returns:
        Dict with success flag and optional error.
    """
    if method == "cli":
        return _release_via_cli(app_name, mig_profile)

    import urllib.request
    import urllib.error

    url = f"{api_endpoint}/deployments"
    payload_dict = {
        "app_name": app_name,
        "action": "stop",
    }
    if mig_profile:
        payload_dict["gpu_profile"] = mig_profile

    payload = json.dumps(payload_dict).encode("utf-8")

    try:
        req = urllib.request.Request(url, data=payload, method="POST")
        req.add_header("Content-Type", "application/json")
        with urllib.request.urlopen(req, timeout=15) as response:
            return {"success": True}
    except urllib.error.HTTPError as e:
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


def _release_via_cli(app_name: str, mig_profile: str) -> dict:
    """Release GPU resources via the platform CLI.

    Args:
        app_name: Application name.
        mig_profile: Profile to release.

    Returns:
        Dict with success flag and optional error.
    """
    import subprocess

    cli_path = "/usr/local/bin/aipoweredstore_cli.py"
    cmd = [cli_path, "gpu", "release", "--app", app_name]
    if mig_profile:
        cmd.extend(["--profile", mig_profile])

    try:
        proc = subprocess.run(
            cmd, capture_output=True, text=True, timeout=15
        )
        if proc.returncode == 0:
            return {"success": True}
        else:
            return {
                "success": False,
                "error": (
                    f"CLI exit code {proc.returncode}: {proc.stderr.strip()}"
                ),
            }
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "CLI command timed out."}
    except (FileNotFoundError, OSError) as e:
        return {"success": False, "error": f"Failed to execute CLI: {e}"}


def _wait_for_deallocation(
    app_name: str,
    mig_profile: str,
    api_endpoint: str,
    timeout: int = RELEASE_TIMEOUT_SECONDS,
) -> dict:
    """Poll allocation status until profile is removed or timeout.

    Args:
        app_name: Application name.
        mig_profile: Profile that should be removed.
        api_endpoint: Platform API base URL.
        timeout: Maximum seconds to wait for deallocation.

    Returns:
        Dict with removed flag and elapsed time.
    """
    import urllib.request
    import urllib.error

    url = f"{api_endpoint}/gpu/allocations?app={app_name}"
    start_time = time.time()
    poll_interval = 2  # seconds

    while True:
        elapsed = time.time() - start_time
        if elapsed > timeout:
            return {"removed": False, "elapsed_seconds": elapsed}

        try:
            req = urllib.request.Request(url, method="GET")
            req.add_header("Content-Type", "application/json")
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode("utf-8"))
                allocations = data.get("allocations", [])

                # Check if the profile is still present
                profile_found = False
                for alloc in allocations:
                    if alloc.get("app_name") == app_name:
                        if mig_profile:
                            if alloc.get("profile_id") == mig_profile:
                                profile_found = True
                                break
                        else:
                            profile_found = True
                            break

                if not profile_found:
                    return {
                        "removed": True,
                        "elapsed_seconds": time.time() - start_time,
                    }
        except (urllib.error.URLError, json.JSONDecodeError):
            pass

        time.sleep(poll_interval)

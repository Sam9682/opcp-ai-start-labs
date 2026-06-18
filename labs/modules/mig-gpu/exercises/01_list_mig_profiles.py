"""Exercise 1: List MIG Profiles.

List available Multi-Instance GPU (MIG) profile configurations on the
AI-Powered-Store platform. Each profile defines compute and memory
resources for isolated GPU instances.
"""

import json
import subprocess
from typing import Optional

from labs.templates.exercise_base import Exercise


class ListMIGProfilesExercise(Exercise):
    """List available MIG profile configurations on the platform."""

    @property
    def exercise_id(self) -> str:
        return "01_list_mig_profiles"

    @property
    def name(self) -> str:
        return "List MIG Profiles"

    @property
    def description(self) -> str:
        return (
            "List available MIG profile configurations on the "
            "AI-Powered-Store platform to understand available GPU "
            "partitioning options."
        )

    @property
    def timeout_minutes(self) -> int:
        return 5

    @property
    def prerequisites(self) -> list[str]:
        return []

    def setup(self) -> None:
        """No special setup required for listing profiles."""
        pass

    def execute(self, submission: dict) -> dict:
        """Query the platform for available MIG profiles.

        Args:
            submission: Must contain:
                - cli_path (str, optional): Path to CLI tool
                  (defaults to /usr/local/bin/aipoweredstore_cli.py)
                - api_endpoint (str, optional): Platform API endpoint
                  (defaults to http://localhost:5000/api)
                - method (str, optional): Query method - "cli" or "api"
                  (defaults to "cli")

        Returns:
            Dict with profile listing results.
        """
        cli_path = submission.get(
            "cli_path", "/usr/local/bin/aipoweredstore_cli.py"
        )
        api_endpoint = submission.get(
            "api_endpoint", "http://localhost:5000/api"
        )
        method = submission.get("method", "cli")

        result = {
            "method": method,
            "profiles_retrieved": False,
            "profiles": [],
            "profile_count": 0,
            "error": None,
        }

        if method == "cli":
            profiles_data = _list_profiles_via_cli(cli_path)
        else:
            profiles_data = _list_profiles_via_api(api_endpoint)

        if profiles_data["success"]:
            result["profiles_retrieved"] = True
            result["profiles"] = profiles_data["profiles"]
            result["profile_count"] = len(profiles_data["profiles"])
        else:
            result["error"] = profiles_data["error"]

        return result

    def validate(self, result: dict) -> list[dict]:
        """Validate the MIG profile listing results.

        Checks:
        1. Profiles were successfully retrieved
        2. At least one profile is available
        3. Each profile has required fields (id, compute_capability, memory_mb)
        """
        checks = []

        # Check 1: Profiles retrieved successfully
        checks.append({
            "name": "profiles_retrieved",
            "passed": result.get("profiles_retrieved", False),
            "feedback": (
                "MIG profiles retrieved successfully."
                if result.get("profiles_retrieved")
                else f"Failed to retrieve profiles: {result.get('error', 'Unknown error')}"
            ),
            "expected": "profiles_retrieved=True",
            "actual": f"profiles_retrieved={result.get('profiles_retrieved')}",
        })

        if not result.get("profiles_retrieved"):
            return checks

        # Check 2: At least one profile available
        profile_count = result.get("profile_count", 0)
        checks.append({
            "name": "profiles_available",
            "passed": profile_count > 0,
            "feedback": (
                f"Found {profile_count} available MIG profile(s)."
                if profile_count > 0
                else "No MIG profiles available on the platform."
            ),
            "expected": "profile_count > 0",
            "actual": f"profile_count={profile_count}",
        })

        # Check 3: Profiles have required fields
        profiles = result.get("profiles", [])
        required_fields = {"id", "compute_capability", "memory_mb"}
        all_valid = True
        missing_fields_info = []

        for profile in profiles:
            missing = required_fields - set(profile.keys())
            if missing:
                all_valid = False
                missing_fields_info.append(
                    f"Profile '{profile.get('id', 'unknown')}' "
                    f"missing: {', '.join(sorted(missing))}"
                )

        checks.append({
            "name": "profile_fields_complete",
            "passed": all_valid,
            "feedback": (
                "All profiles contain required fields "
                "(id, compute_capability, memory_mb)."
                if all_valid
                else f"Incomplete profiles: {'; '.join(missing_fields_info)}"
            ),
            "expected": "All profiles have id, compute_capability, memory_mb",
            "actual": (
                "All fields present" if all_valid
                else f"{len(missing_fields_info)} profile(s) with missing fields"
            ),
        })

        return checks

    def teardown(self) -> None:
        """No teardown required for listing profiles."""
        pass

    def get_hints(self) -> list[str]:
        return [
            "Use 'aipoweredstore_cli.py gpu list-profiles' to see available MIG profiles.",
            "Each profile shows its compute capability and allocated memory.",
            "Profiles with higher compute capability provide more GPU cores.",
        ]

    def get_instructions(self) -> Optional[str]:
        return (
            "In this exercise, you will list the available MIG (Multi-Instance "
            "GPU) profile configurations on the AI-Powered-Store platform.\n\n"
            "Steps:\n"
            "1. Query the platform for available MIG profiles using the CLI "
            "or REST API\n"
            "2. Review the available profiles and their compute capabilities\n"
            "3. Understand the memory allocation for each profile\n\n"
            "MIG profiles partition a physical GPU into isolated instances. "
            "Each profile defines the compute and memory resources available "
            "to the instance."
        )


def _list_profiles_via_cli(cli_path: str) -> dict:
    """List MIG profiles using the platform CLI.

    Args:
        cli_path: Path to the CLI tool.

    Returns:
        Dict with success flag, profiles list, and optional error.
    """
    try:
        proc = subprocess.run(
            [cli_path, "gpu", "list-profiles"],
            capture_output=True,
            text=True,
            timeout=15,
        )
        if proc.returncode == 0:
            profiles = _parse_profile_output(proc.stdout)
            return {"success": True, "profiles": profiles, "error": None}
        else:
            return {
                "success": False,
                "profiles": [],
                "error": f"CLI returned exit code {proc.returncode}: {proc.stderr}",
            }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "profiles": [],
            "error": "CLI command timed out after 15 seconds.",
        }
    except (FileNotFoundError, OSError) as e:
        return {
            "success": False,
            "profiles": [],
            "error": f"Failed to execute CLI: {e}",
        }


def _list_profiles_via_api(api_endpoint: str) -> dict:
    """List MIG profiles using the platform REST API.

    Args:
        api_endpoint: Platform API base URL.

    Returns:
        Dict with success flag, profiles list, and optional error.
    """
    import urllib.request
    import urllib.error

    url = f"{api_endpoint}/gpu/profiles"
    try:
        req = urllib.request.Request(url, method="GET")
        req.add_header("Content-Type", "application/json")
        with urllib.request.urlopen(req, timeout=15) as response:
            data = json.loads(response.read().decode("utf-8"))
            profiles = data.get("profiles", [])
            return {"success": True, "profiles": profiles, "error": None}
    except urllib.error.URLError as e:
        return {
            "success": False,
            "profiles": [],
            "error": (
                f"Failed to reach API endpoint {url}: {e.reason}. "
                "Check network connectivity."
            ),
        }
    except (json.JSONDecodeError, KeyError) as e:
        return {
            "success": False,
            "profiles": [],
            "error": f"Invalid response format from API: {e}",
        }


def _parse_profile_output(output: str) -> list[dict]:
    """Parse CLI output into structured profile data.

    Attempts JSON parsing first, falls back to line-based parsing.

    Args:
        output: CLI stdout content.

    Returns:
        List of profile dicts with id, compute_capability, and memory_mb.
    """
    # Try JSON format first
    try:
        data = json.loads(output)
        if isinstance(data, list):
            return data
        if isinstance(data, dict) and "profiles" in data:
            return data["profiles"]
    except (json.JSONDecodeError, ValueError):
        pass

    # Fall back to line-based parsing
    profiles = []
    for line in output.strip().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("---"):
            continue
        parts = line.split()
        if len(parts) >= 3:
            try:
                profiles.append({
                    "id": parts[0],
                    "compute_capability": parts[1],
                    "memory_mb": int(parts[2]),
                })
            except (ValueError, IndexError):
                continue

    return profiles

"""Reference solution for Exercise 4: Release GPU Resources.

Demonstrates the correct approach to releasing allocated MIG GPU resources
and verifying that the profile is removed from the active GPU allocation
status within 30 seconds.
"""


def get_solution() -> dict:
    """Return the reference solution submission for GPU resource release.

    Returns:
        A dict representing a valid submission that passes all checks.
    """
    return {
        "app_name": "mig-training-app",
        "mig_profile": "1g.5gb",
        "api_endpoint": "http://localhost:5000/api",
        "method": "api",
    }


def get_expected_result() -> dict:
    """Return the expected result from a successful GPU resource release.

    Returns:
        Expected output when GPU resources are released and deallocation
        is confirmed within 30 seconds.
    """
    return {
        "app_name": "mig-training-app",
        "mig_profile": "1g.5gb",
        "method": "api",
        "release_requested": True,
        "profile_removed": True,
        "release_time_seconds": 4.1,
        "error": None,
    }


def get_api_request() -> dict:
    """Return the API request body to stop the application and release GPU.

    Returns:
        The JSON payload for the stop/release API.
    """
    return {
        "app_name": "mig-training-app",
        "action": "stop",
    }


def get_verification_command() -> str:
    """Return the command to verify GPU deallocation.

    Returns:
        The API endpoint to check that the allocation is removed.
    """
    return "GET /api/gpu/allocations?app=mig-training-app"


def get_cli_command() -> str:
    """Return the CLI command to release GPU resources.

    Returns:
        The CLI command string for GPU release.
    """
    return "aipoweredstore_cli.py gpu release --app mig-training-app"

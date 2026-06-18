"""Reference solution for Exercise 2: Deploy with MIG Profile.

Demonstrates the correct approach to deploying a Docker application
with a specific MIG profile and verifying GPU allocation.
"""


def get_solution() -> dict:
    """Return the reference solution submission for MIG deployment.

    Returns:
        A dict representing a valid submission that passes all checks.
    """
    return {
        "app_name": "mig-training-app",
        "mig_profile": "1g.5gb",
        "docker_image": "training/gpu-sample:latest",
        "api_endpoint": "http://localhost:5000/api",
        "method": "api",
    }


def get_expected_result() -> dict:
    """Return the expected result from a successful deployment.

    Returns:
        Expected output when deployment and allocation succeed.
    """
    return {
        "app_name": "mig-training-app",
        "requested_profile": "1g.5gb",
        "docker_image": "training/gpu-sample:latest",
        "method": "api",
        "deployed": True,
        "allocation_confirmed": True,
        "assigned_profile": "1g.5gb",
        "allocation_time_seconds": 5.2,
        "alternative_profiles": [],
        "error": None,
    }


def get_api_request() -> dict:
    """Return the API request body for deployment.

    Returns:
        The JSON payload for the deployment API.
    """
    return {
        "app_name": "mig-training-app",
        "docker_image": "training/gpu-sample:latest",
        "gpu_profile": "1g.5gb",
        "action": "start",
    }


def get_verification_command() -> str:
    """Return the command to verify GPU allocation.

    Returns:
        The API endpoint to check allocation status.
    """
    return "GET /api/gpu/allocations?app=mig-training-app"

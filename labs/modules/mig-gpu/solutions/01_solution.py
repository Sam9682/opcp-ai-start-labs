"""Reference solution for Exercise 1: List MIG Profiles.

Demonstrates the correct approach to listing available MIG profile
configurations on the AI-Powered-Store platform.
"""


def get_solution() -> dict:
    """Return the reference solution submission for listing MIG profiles.

    Returns:
        A dict representing a valid submission that passes all checks.
    """
    return {
        "method": "cli",
        "cli_path": "aipoweredstore_cli.py",
        "api_endpoint": "http://localhost:5000/api",
    }


def get_expected_result() -> dict:
    """Return the expected result structure from a successful listing.

    Returns:
        Expected output when profiles are successfully retrieved.
    """
    return {
        "method": "cli",
        "profiles_retrieved": True,
        "profile_count": 7,
        "profiles": [
            {"id": "1g.5gb", "compute_capability": "1/7", "memory_mb": 5120},
            {"id": "1g.10gb", "compute_capability": "1/7", "memory_mb": 10240},
            {"id": "2g.10gb", "compute_capability": "2/7", "memory_mb": 10240},
            {"id": "3g.20gb", "compute_capability": "3/7", "memory_mb": 20480},
            {"id": "4g.20gb", "compute_capability": "4/7", "memory_mb": 20480},
            {"id": "7g.40gb", "compute_capability": "7/7", "memory_mb": 40960},
            {"id": "7g.80gb", "compute_capability": "7/7", "memory_mb": 81920},
        ],
        "error": None,
    }


def get_cli_command() -> str:
    """Return the CLI command for listing profiles.

    Returns:
        The CLI command string.
    """
    return "aipoweredstore_cli.py gpu list-profiles"


def get_api_command() -> str:
    """Return the API request for listing profiles.

    Returns:
        The API endpoint to query.
    """
    return "GET /api/gpu/profiles"

"""Reference solution for Exercise 2: REST API Application Registration.

Demonstrates the correct approach to registering an application
using the REST API POST /api/applications endpoint.
"""


def get_solution() -> dict:
    """Return the reference solution submission for API registration.

    Returns:
        A dict representing a valid submission that passes all checks.
    """
    return {
        "name": "api-registered-app",
        "description": "Application registered via REST API during lab exercise",
        "git_url": "https://github.com/training/api-app",
        "docker_image": "training/api-app:v1.0",
        "api_base_url": "https://store.example.com",
    }


def get_curl_command() -> str:
    """Return the reference curl command for the API registration.

    Returns:
        The full curl command string for application registration.
    """
    return (
        "curl -X POST https://store.example.com/api/applications "
        "-H 'Content-Type: application/json' "
        "-d '{\"name\": \"api-registered-app\", "
        "\"description\": \"Application registered via REST API during lab exercise\", "
        "\"git_url\": \"https://github.com/training/api-app\", "
        "\"docker_image\": \"training/api-app:v1.0\"}'"
    )


def get_verification_command() -> str:
    """Return the curl command to verify registration via GET.

    Returns:
        The curl command to query the applications registry.
    """
    return "curl https://store.example.com/api/applications"

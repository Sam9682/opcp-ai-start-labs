"""Reference solution for Exercise 1: View Resource Consumption.

Demonstrates the correct approach to querying the billing API
for current resource consumption data and verifying resource counts
match within 1% tolerance.
"""


def get_solution() -> dict:
    """Return the reference solution submission for viewing consumption.

    Returns:
        A dict representing a valid submission that passes all checks.
    """
    return {
        "api_endpoint": "http://localhost:5000",
        "auth_token": "your-api-token",
        "resource_filter": None,
    }


def get_curl_command() -> str:
    """Return the reference curl command for querying consumption.

    Returns:
        The full curl command string to query billing consumption.
    """
    return (
        "curl -X GET http://localhost:5000/api/billing/consumption "
        "-H 'Authorization: Bearer your-api-token'"
    )


def get_filtered_command(resource_type: str = "cpu") -> str:
    """Return a curl command filtered by resource type.

    Args:
        resource_type: One of 'cpu', 'memory', 'storage', 'gpu'.

    Returns:
        The curl command to query consumption filtered by type.
    """
    return (
        f"curl -X GET 'http://localhost:5000/api/billing/consumption?type={resource_type}' "
        "-H 'Authorization: Bearer your-api-token'"
    )


def get_verification_steps() -> list[str]:
    """Return step-by-step verification instructions.

    Returns:
        List of steps to verify resource consumption data.
    """
    return [
        "1. Query the billing API for current resource consumption",
        "2. Query the containers API for active (running) containers",
        "3. Compare the resource count from billing with active container count",
        "4. Verify the counts match within 1% tolerance:",
        "   |billing_count - container_count| / container_count <= 0.01",
        "5. Confirm no errors occurred during the query",
    ]

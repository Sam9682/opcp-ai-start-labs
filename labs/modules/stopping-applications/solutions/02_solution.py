"""Reference solution: Stop Application via REST API.

Demonstrates the correct approach for stopping an application
using the AI-Powered-Store REST API.
"""


def solve_stop_via_api(
    app_name: str,
    api_base_url: str = "http://localhost:5000/api",
    port: int = 8080,
):
    """Reference solution for Exercise 2: Stop Application via REST API.

    Steps:
    1. Verify the application is running via GET /api/applications/{name}/status
    2. Send POST /api/deployments with {"app_name": name, "action": "stop"}
    3. Verify termination via status endpoint and port check

    Args:
        app_name: Name of the application to stop.
        api_base_url: Base URL of the platform API.
        port: Application port to verify refusal.

    Returns:
        Submission dict suitable for the exercise execute() method.
    """
    return {
        "app_name": app_name,
        "api_base_url": api_base_url,
        "host": "localhost",
        "port": port,
    }


# Example API requests for learner reference:
#
# 1. Check application status:
#    GET /api/applications/my-app/status
#    Response: {"status": "running", "port": 8080, "pid": 12345}
#
# 2. Stop application:
#    POST /api/deployments
#    Body: {"app_name": "my-app", "action": "stop"}
#    Response: {"status": "stopping", "message": "Stop initiated"}
#
# 3. Verify stopped:
#    GET /api/applications/my-app/status
#    Response: {"status": "stopped", "exit_code": 0}
#
# 4. If stop times out (30s), force-stop:
#    POST /api/deployments
#    Body: {"app_name": "my-app", "action": "force-stop"}
#    Response: {"status": "terminated", "message": "Application force-stopped"}

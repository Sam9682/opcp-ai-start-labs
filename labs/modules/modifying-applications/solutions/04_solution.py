"""Reference solution for Exercise 04: Verify Updated Application.

Demonstrates the correct approach to building, starting, and verifying
the modified application with health check and runtime monitoring.
"""


def get_solution() -> dict:
    """Return the reference solution submission for application verification.

    Returns:
        A dict representing a valid submission that passes all checks.
    """
    return {
        "app_name": "my-training-app",
        "app_directory": "/opt/ai-powered-store/apps/my-training-app",
        "build_command": "docker build -t my-training-app:latest .",
        "start_command": "docker run -d -p 8080:8080 --name my-training-app my-training-app:latest",
        "health_endpoint": "http://localhost:8080/health",
        "log_source": "docker logs my-training-app",
    }


def get_build_commands() -> list[str]:
    """Return the sequence of commands to build and verify the application.

    Returns:
        A list of shell commands for the build and verification workflow.
    """
    return [
        # Step 1: Build the application (must exit 0 within 120s)
        "cd /opt/ai-powered-store/apps/my-training-app && docker build -t my-training-app:latest .",
        # Step 2: Start the application
        "docker run -d -p 8080:8080 --name my-training-app my-training-app:latest",
        # Step 3: Health check (poll within 30s)
        "curl -sf http://localhost:8080/health",
        # Step 4: Monitor logs for 10 seconds
        "timeout 10 docker logs -f my-training-app 2>&1 | grep -i 'error\\|exception\\|traceback'",
    ]


def get_verification_criteria() -> dict:
    """Return the verification criteria and their thresholds.

    Returns:
        Dict describing each verification step and its pass criteria.
    """
    return {
        "build": {
            "criterion": "Build exits with code 0",
            "timeout_seconds": 120,
            "pass_condition": "exit_code == 0",
        },
        "health_check": {
            "criterion": "Health endpoint returns HTTP 200",
            "timeout_seconds": 30,
            "pass_condition": "HTTP status 200 within timeout",
        },
        "runtime_errors": {
            "criterion": "No error-level messages in first 10 seconds",
            "duration_seconds": 10,
            "pass_condition": "No lines matching error/exception/traceback patterns",
        },
    }


def get_cleanup_commands() -> list[str]:
    """Return commands to clean up after verification.

    Returns:
        A list of shell commands to stop and remove the test container.
    """
    return [
        "docker stop my-training-app 2>/dev/null || true",
        "docker rm my-training-app 2>/dev/null || true",
    ]

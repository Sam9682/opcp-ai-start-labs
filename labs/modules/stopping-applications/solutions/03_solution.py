"""Reference solution: Confirm Graceful Shutdown.

Demonstrates the correct approach for verifying graceful shutdown
behavior of an application, including force-stop recovery.
"""


def solve_graceful_shutdown(
    app_name: str,
    cli_path: str = "/usr/local/bin/aipoweredstore_cli.py",
    port: int = 8080,
):
    """Reference solution for Exercise 3: Confirm Graceful Shutdown.

    Steps:
    1. Verify application is running
    2. Initiate stop and monitor for graceful behavior
    3. Confirm exit code 0, in-flight completion, process termination, port refusal
    4. If timeout occurs, use force-stop

    Args:
        app_name: Name of the application to stop.
        cli_path: Path to the CLI tool.
        port: Application port to verify.

    Returns:
        Submission dict suitable for the exercise execute() method.
    """
    return {
        "app_name": app_name,
        "cli_path": cli_path,
        "host": "localhost",
        "port": port,
        "method": "cli",
        "use_force_stop": False,
    }


def solve_force_stop(
    app_name: str,
    cli_path: str = "/usr/local/bin/aipoweredstore_cli.py",
    port: int = 8080,
):
    """Reference solution for the force-stop recovery scenario.

    Use when graceful shutdown times out after 30 seconds.

    Args:
        app_name: Name of the application to force-stop.
        cli_path: Path to the CLI tool.
        port: Application port to verify.

    Returns:
        Submission dict for force-stop scenario.
    """
    return {
        "app_name": app_name,
        "cli_path": cli_path,
        "host": "localhost",
        "port": port,
        "method": "cli",
        "use_force_stop": True,
    }


# Graceful Shutdown verification checklist:
#
# 1. Pre-condition: Application must be running
#    $ aipoweredstore_cli.py status my-app
#    Expected: "running"
#
# 2. Initiate stop:
#    $ aipoweredstore_cli.py stop my-app
#
# 3. Verify graceful behavior:
#    - Exit code = 0 (process exited cleanly)
#    - In-flight requests completed (no dropped connections)
#    - Process terminated within 5 seconds
#    - Port refuses new connections within 5 seconds
#
# 4. Force-stop recovery (if 30s timeout):
#    $ aipoweredstore_cli.py force-stop my-app
#    - Process terminated (regardless of in-flight requests)
#    - Port refuses new connections

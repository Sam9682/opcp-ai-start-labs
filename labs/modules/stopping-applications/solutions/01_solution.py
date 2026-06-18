"""Reference solution: Stop Application via CLI.

Demonstrates the correct approach for stopping an application
using the AI-Powered-Store CLI tool.
"""


def solve_stop_via_cli(app_name: str, cli_path: str = "/usr/local/bin/aipoweredstore_cli.py"):
    """Reference solution for Exercise 1: Stop Application via CLI.

    Steps:
    1. Verify the application is running
    2. Execute the stop command
    3. Verify termination within 5 seconds

    Args:
        app_name: Name of the application to stop.
        cli_path: Path to the CLI tool.

    Returns:
        Submission dict suitable for the exercise execute() method.
    """
    return {
        "app_name": app_name,
        "cli_path": cli_path,
        "host": "localhost",
        "port": 8080,
    }


# Example CLI commands for learner reference:
#
# 1. Check application status:
#    $ aipoweredstore_cli.py status my-app
#    Output: Application 'my-app' is running on port 8080
#
# 2. Stop application gracefully:
#    $ aipoweredstore_cli.py stop my-app
#    Output: Stopping application 'my-app'...
#            Application 'my-app' stopped successfully (exit code: 0)
#
# 3. Verify termination:
#    $ aipoweredstore_cli.py status my-app
#    Output: Application 'my-app' is stopped
#
# 4. If stop times out (30s), use force-stop:
#    $ aipoweredstore_cli.py force-stop my-app
#    Output: Force-stopping application 'my-app'...
#            Application 'my-app' terminated

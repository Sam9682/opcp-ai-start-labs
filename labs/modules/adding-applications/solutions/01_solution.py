"""Reference solution for Exercise 1: CLI Application Registration.

Demonstrates the correct approach to registering an application
using the aipoweredstore_cli.py command-line tool.
"""


def get_solution() -> dict:
    """Return the reference solution submission for CLI registration.

    Returns:
        A dict representing a valid submission that passes all checks.
    """
    return {
        "name": "my-training-app",
        "description": "A sample application registered during the Adding Applications lab",
        "git_url": "https://github.com/training/sample-app",
        "docker_image": "training/sample-app:latest",
        "cli_path": "aipoweredstore_cli.py",
    }


def get_expected_command() -> str:
    """Return the expected CLI command for reference.

    Returns:
        The full CLI command string that should be constructed.
    """
    return (
        "aipoweredstore_cli.py app register "
        "--name 'my-training-app' "
        "--description 'A sample application registered during the Adding Applications lab' "
        "--git-url 'https://github.com/training/sample-app' "
        "--docker-image 'training/sample-app:latest'"
    )


def get_verification_command() -> str:
    """Return the command to verify the application was registered.

    Returns:
        The CLI command to list registered applications.
    """
    return "aipoweredstore_cli.py app list"

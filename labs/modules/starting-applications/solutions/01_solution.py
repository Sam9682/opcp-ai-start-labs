"""Solution for Exercise 01: Start Application via CLI.

Reference solution demonstrating how to start an application
using the aipoweredstore_cli.py command-line tool.
"""

import subprocess
import sys


def start_application_cli(app_name: str, cli_path: str = "/usr/local/bin/aipoweredstore_cli.py") -> None:
    """Start an application using the platform CLI.

    Args:
        app_name: Name of the registered application to start.
        cli_path: Path to the CLI tool.
    """
    print(f"Starting application '{app_name}' via CLI...")

    # Execute the start command
    result = subprocess.run(
        [cli_path, "app", "start", app_name],
        capture_output=True,
        text=True,
    )

    if result.returncode == 0:
        print(f"Start command successful: {result.stdout.strip()}")
    else:
        print(f"Start command failed (exit code {result.returncode}):")
        print(result.stderr)
        sys.exit(1)

    # Verify running status
    print("Checking application status...")
    status_result = subprocess.run(
        [cli_path, "app", "status", app_name],
        capture_output=True,
        text=True,
    )

    print(f"Status: {status_result.stdout.strip()}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python 01_solution.py <app_name>")
        sys.exit(1)

    start_application_cli(sys.argv[1])

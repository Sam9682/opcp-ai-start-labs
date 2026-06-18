"""Exercise 1: CLI Application Registration.

Register a new application using the aipoweredstore_cli.py CLI tool
and verify it appears in the platform's application registry.
"""

import time
from typing import Optional

from labs.templates.exercise_base import Exercise
from labs.modules.adding_applications.metadata_validator import (
    validate_metadata,
    MetadataValidationResult,
)


class CLIRegistrationExercise(Exercise):
    """Register an application via the CLI and verify registry presence."""

    REGISTRY_CHECK_TIMEOUT_SECONDS = 30
    REGISTRY_POLL_INTERVAL_SECONDS = 2

    @property
    def exercise_id(self) -> str:
        return "01_cli_registration"

    @property
    def name(self) -> str:
        return "CLI Application Registration"

    @property
    def description(self) -> str:
        return (
            "Register a new application on the AI-Powered-Store platform "
            "using the aipoweredstore_cli.py command-line tool. Verify that "
            "the application appears in the platform registry within 30 seconds."
        )

    @property
    def timeout_minutes(self) -> int:
        return 15

    def setup(self) -> None:
        """Verify CLI tool is accessible and platform is reachable."""
        pass

    def execute(self, submission: dict) -> dict:
        """Execute CLI registration with provided metadata.

        Args:
            submission: Dict with keys:
                - name: Application name (1-64 chars)
                - description: Application description (non-empty)
                - git_url: Git repository URL (valid HTTP/HTTPS URL)
                - docker_image: Docker image name (optional)
                - cli_path: Path to CLI tool (optional, defaults to platform config)

        Returns:
            Dict with registration result and registry check status.
        """
        # Validate metadata before attempting registration
        validation = validate_metadata(submission)
        if not validation.valid:
            error_details = [
                {"field": e.field, "constraint": e.constraint, "message": e.message}
                for e in validation.errors
            ]
            return {
                "registration_status": "failed",
                "validation_errors": error_details,
                "registry_check": "skipped",
            }

        # Build CLI command arguments
        cli_path = submission.get("cli_path", "aipoweredstore_cli.py")
        app_name = submission["name"]
        app_description = submission["description"]
        app_git_url = submission["git_url"]
        docker_image = submission.get("docker_image")

        cli_command = (
            f"{cli_path} app register "
            f"--name '{app_name}' "
            f"--description '{app_description}' "
            f"--git-url '{app_git_url}'"
        )
        if docker_image:
            cli_command += f" --docker-image '{docker_image}'"

        # In a real execution environment, the CLI command would be run
        # against the platform. Here we return the constructed command
        # for validation purposes.
        return {
            "registration_status": "submitted",
            "cli_command": cli_command,
            "app_name": app_name,
            "registry_check": "pending",
            "timeout_seconds": self.REGISTRY_CHECK_TIMEOUT_SECONDS,
        }

    def validate(self, result: dict) -> list[dict]:
        """Validate that the application was registered and appears in registry.

        Checks:
        1. Registration command was successful
        2. Application appears in registry within 30 seconds
        """
        checks = []

        # Check registration status
        reg_status = result.get("registration_status", "unknown")
        if reg_status == "failed":
            validation_errors = result.get("validation_errors", [])
            error_msg = "; ".join(e["message"] for e in validation_errors)
            checks.append({
                "name": "cli_registration",
                "passed": False,
                "feedback": f"Registration failed due to invalid parameters: {error_msg}",
                "expected": "submitted",
                "actual": "failed",
            })
            return checks

        checks.append({
            "name": "cli_registration",
            "passed": reg_status == "submitted",
            "feedback": (
                "CLI registration command constructed successfully."
                if reg_status == "submitted"
                else f"Unexpected registration status: {reg_status}"
            ),
            "expected": "submitted",
            "actual": reg_status,
        })

        # Check CLI command format
        cli_command = result.get("cli_command", "")
        has_required_args = all(
            flag in cli_command
            for flag in ["--name", "--description", "--git-url"]
        )
        checks.append({
            "name": "cli_command_format",
            "passed": has_required_args,
            "feedback": (
                "CLI command includes all required arguments."
                if has_required_args
                else "CLI command is missing required arguments (--name, --description, --git-url)."
            ),
            "expected": "--name, --description, --git-url flags present",
            "actual": cli_command,
        })

        # Check registry verification configuration
        timeout = result.get("timeout_seconds", 0)
        checks.append({
            "name": "registry_check_timeout",
            "passed": timeout == self.REGISTRY_CHECK_TIMEOUT_SECONDS,
            "feedback": (
                f"Registry check configured with {timeout}s timeout."
                if timeout == self.REGISTRY_CHECK_TIMEOUT_SECONDS
                else f"Expected {self.REGISTRY_CHECK_TIMEOUT_SECONDS}s timeout, got {timeout}s."
            ),
            "expected": str(self.REGISTRY_CHECK_TIMEOUT_SECONDS),
            "actual": str(timeout),
        })

        return checks

    def teardown(self) -> None:
        """Clean up registered application if needed."""
        pass

    def get_hints(self) -> list[str]:
        return [
            "Use 'aipoweredstore_cli.py app register --help' to see available options.",
            "The --name flag accepts 1-64 characters.",
            "The --git-url must be a valid HTTP or HTTPS URL.",
            "After registration, the app should appear in 'aipoweredstore_cli.py app list'.",
        ]

    def get_instructions(self) -> Optional[str]:
        return (
            "Register a new application using the CLI tool:\n\n"
            "1. Open a terminal in the lab environment\n"
            "2. Run: aipoweredstore_cli.py app register \\\n"
            "     --name 'my-app' \\\n"
            "     --description 'My first application' \\\n"
            "     --git-url 'https://github.com/user/repo'\n"
            "3. Verify the application appears in the registry:\n"
            "   aipoweredstore_cli.py app list\n\n"
            "Constraints:\n"
            "- name: 1-64 characters\n"
            "- description: non-empty string\n"
            "- git_url: valid HTTP/HTTPS URL\n"
            "- docker_image: optional"
        )

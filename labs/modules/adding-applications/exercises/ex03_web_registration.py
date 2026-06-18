"""Exercise 3: Web Interface Application Registration.

Register a new application using the AI-Powered-Store web interface
and verify it appears in the platform's application registry.
"""

from typing import Optional

from labs.templates.exercise_base import Exercise
from labs.modules.adding_applications.metadata_validator import (
    validate_metadata,
    MetadataValidationResult,
)


class WebRegistrationExercise(Exercise):
    """Register an application via web interface and verify registry presence."""

    REGISTRY_CHECK_TIMEOUT_SECONDS = 30
    REGISTRY_POLL_INTERVAL_SECONDS = 2

    @property
    def exercise_id(self) -> str:
        return "03_web_registration"

    @property
    def name(self) -> str:
        return "Web Interface Application Registration"

    @property
    def description(self) -> str:
        return (
            "Register a new application on the AI-Powered-Store platform "
            "using the web interface. Verify that the application appears "
            "in the registry within 30 seconds."
        )

    @property
    def timeout_minutes(self) -> int:
        return 15

    @property
    def prerequisites(self) -> list[str]:
        return ["02_api_registration"]

    def setup(self) -> None:
        """Verify web interface is accessible."""
        pass

    def execute(self, submission: dict) -> dict:
        """Execute web interface registration with provided metadata.

        Args:
            submission: Dict with keys:
                - name: Application name (1-64 chars)
                - description: Application description (non-empty)
                - git_url: Git repository URL (valid HTTP/HTTPS URL)
                - docker_image: Docker image name (optional)
                - web_url: URL of the platform web interface (optional)

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

        web_url = submission.get("web_url", "https://store.example.com")

        # Build the form data matching web interface fields
        form_data = {
            "name": submission["name"],
            "description": submission["description"],
            "git_url": submission["git_url"],
        }
        if submission.get("docker_image"):
            form_data["docker_image"] = submission["docker_image"]

        # In a real execution environment, this would interact with
        # the web interface. Here we return the form data for validation.
        return {
            "registration_status": "submitted",
            "method": "web_form",
            "web_url": f"{web_url}/applications/new",
            "form_data": form_data,
            "app_name": submission["name"],
            "registry_check": "pending",
            "timeout_seconds": self.REGISTRY_CHECK_TIMEOUT_SECONDS,
        }

    def validate(self, result: dict) -> list[dict]:
        """Validate that the web form submission was properly constructed.

        Checks:
        1. Registration was submitted successfully
        2. Web form URL is correct
        3. Form data contains required fields
        4. Registry verification configured with 30s timeout
        """
        checks = []

        # Check registration status
        reg_status = result.get("registration_status", "unknown")
        if reg_status == "failed":
            validation_errors = result.get("validation_errors", [])
            error_msg = "; ".join(e["message"] for e in validation_errors)
            checks.append({
                "name": "web_registration",
                "passed": False,
                "feedback": f"Registration failed due to invalid parameters: {error_msg}",
                "expected": "submitted",
                "actual": "failed",
            })
            return checks

        checks.append({
            "name": "web_registration",
            "passed": reg_status == "submitted",
            "feedback": (
                "Web form registration submitted successfully."
                if reg_status == "submitted"
                else f"Unexpected registration status: {reg_status}"
            ),
            "expected": "submitted",
            "actual": reg_status,
        })

        # Check web URL targets correct page
        web_url = result.get("web_url", "")
        has_correct_page = "/applications/new" in web_url
        checks.append({
            "name": "web_form_url",
            "passed": has_correct_page,
            "feedback": (
                "Correct web form URL used (applications/new page)."
                if has_correct_page
                else f"Web URL should contain '/applications/new', got: {web_url}"
            ),
            "expected": "/applications/new",
            "actual": web_url,
        })

        # Check form data contains required fields
        form_data = result.get("form_data", {})
        required_fields = ["name", "description", "git_url"]
        missing_fields = [f for f in required_fields if f not in form_data]
        checks.append({
            "name": "form_data_fields",
            "passed": len(missing_fields) == 0,
            "feedback": (
                "Form data contains all required fields (name, description, git_url)."
                if not missing_fields
                else f"Form data missing required fields: {', '.join(missing_fields)}"
            ),
            "expected": "name, description, git_url",
            "actual": ", ".join(form_data.keys()),
        })

        # Check registry verification timeout
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
            "Navigate to the Applications section in the web dashboard.",
            "Click 'Add New Application' or equivalent button.",
            "Fill in all required fields: Name, Description, Git URL.",
            "The Docker Image field is optional.",
            "After submitting, check the application list to confirm registration.",
        ]

    def get_instructions(self) -> Optional[str]:
        return (
            "Register a new application using the web interface:\n\n"
            "1. Open the platform dashboard in your browser\n"
            "2. Navigate to Applications → Add New Application\n"
            "3. Fill in the registration form:\n"
            "   - Name: Enter application name (1-64 characters)\n"
            "   - Description: Enter a description\n"
            "   - Git URL: Enter the repository URL\n"
            "   - Docker Image: (optional) Enter image name\n"
            "4. Click 'Register' to submit\n"
            "5. Verify the application appears in the Applications list\n\n"
            "The application should appear in the registry within 30 seconds."
        )

"""Exercise 2: REST API Application Registration.

Register a new application using the REST API POST /api/applications
endpoint and verify it appears in the platform's application registry.
"""

from typing import Optional

from labs.templates.exercise_base import Exercise
from labs.modules.adding_applications.metadata_validator import (
    validate_metadata,
    MetadataValidationResult,
)


class APIRegistrationExercise(Exercise):
    """Register an application via REST API and verify registry presence."""

    REGISTRY_CHECK_TIMEOUT_SECONDS = 30
    REGISTRY_POLL_INTERVAL_SECONDS = 2
    API_ENDPOINT = "/api/applications"

    @property
    def exercise_id(self) -> str:
        return "02_api_registration"

    @property
    def name(self) -> str:
        return "REST API Application Registration"

    @property
    def description(self) -> str:
        return (
            "Register a new application on the AI-Powered-Store platform "
            "using the REST API POST /api/applications endpoint. Verify that "
            "the application appears in the registry within 30 seconds."
        )

    @property
    def timeout_minutes(self) -> int:
        return 15

    @property
    def prerequisites(self) -> list[str]:
        return ["01_cli_registration"]

    def setup(self) -> None:
        """Verify API endpoint is accessible."""
        pass

    def execute(self, submission: dict) -> dict:
        """Execute REST API registration with provided metadata.

        Args:
            submission: Dict with keys:
                - name: Application name (1-64 chars)
                - description: Application description (non-empty)
                - git_url: Git repository URL (valid HTTP/HTTPS URL)
                - docker_image: Docker image name (optional)
                - api_base_url: Base URL for the platform API (optional)

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

        api_base_url = submission.get("api_base_url", "https://store.example.com")
        endpoint = f"{api_base_url}{self.API_ENDPOINT}"

        # Build the request payload
        payload = {
            "name": submission["name"],
            "description": submission["description"],
            "git_url": submission["git_url"],
        }
        if submission.get("docker_image"):
            payload["docker_image"] = submission["docker_image"]

        # In a real execution environment, this would be an HTTP POST.
        # Here we return the request details for validation.
        return {
            "registration_status": "submitted",
            "method": "POST",
            "endpoint": endpoint,
            "payload": payload,
            "app_name": submission["name"],
            "registry_check": "pending",
            "registry_endpoint": f"{api_base_url}/api/applications",
            "timeout_seconds": self.REGISTRY_CHECK_TIMEOUT_SECONDS,
        }

    def validate(self, result: dict) -> list[dict]:
        """Validate that the API registration was properly formed and submitted.

        Checks:
        1. Registration request is valid
        2. Correct HTTP method and endpoint used
        3. Payload contains required fields
        4. Registry verification configured with 30s timeout
        """
        checks = []

        # Check registration status
        reg_status = result.get("registration_status", "unknown")
        if reg_status == "failed":
            validation_errors = result.get("validation_errors", [])
            error_msg = "; ".join(e["message"] for e in validation_errors)
            checks.append({
                "name": "api_registration",
                "passed": False,
                "feedback": f"Registration failed due to invalid parameters: {error_msg}",
                "expected": "submitted",
                "actual": "failed",
            })
            return checks

        checks.append({
            "name": "api_registration",
            "passed": reg_status == "submitted",
            "feedback": (
                "API registration request prepared successfully."
                if reg_status == "submitted"
                else f"Unexpected registration status: {reg_status}"
            ),
            "expected": "submitted",
            "actual": reg_status,
        })

        # Check HTTP method
        method = result.get("method", "")
        checks.append({
            "name": "http_method",
            "passed": method == "POST",
            "feedback": (
                "Correct HTTP method (POST) used."
                if method == "POST"
                else f"Expected POST method, got {method}."
            ),
            "expected": "POST",
            "actual": method,
        })

        # Check endpoint contains /api/applications
        endpoint = result.get("endpoint", "")
        has_correct_endpoint = "/api/applications" in endpoint
        checks.append({
            "name": "api_endpoint",
            "passed": has_correct_endpoint,
            "feedback": (
                "Correct API endpoint used."
                if has_correct_endpoint
                else f"Endpoint should contain '/api/applications', got: {endpoint}"
            ),
            "expected": "/api/applications",
            "actual": endpoint,
        })

        # Check payload contains required fields
        payload = result.get("payload", {})
        required_fields = ["name", "description", "git_url"]
        missing_fields = [f for f in required_fields if f not in payload]
        checks.append({
            "name": "payload_fields",
            "passed": len(missing_fields) == 0,
            "feedback": (
                "Payload contains all required fields (name, description, git_url)."
                if not missing_fields
                else f"Payload missing required fields: {', '.join(missing_fields)}"
            ),
            "expected": "name, description, git_url",
            "actual": ", ".join(payload.keys()),
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
            "Use curl or a HTTP client library to make the POST request.",
            "The endpoint is POST /api/applications with a JSON body.",
            "Required fields in the JSON body: name, description, git_url.",
            "Check the response status code - 201 means successful creation.",
            "Verify with GET /api/applications to confirm the app appears.",
        ]

    def get_instructions(self) -> Optional[str]:
        return (
            "Register a new application using the REST API:\n\n"
            "1. Send a POST request to /api/applications:\n"
            "   curl -X POST https://store.example.com/api/applications \\\n"
            "     -H 'Content-Type: application/json' \\\n"
            "     -d '{\"name\": \"my-app\", "
            "\"description\": \"My application\", "
            "\"git_url\": \"https://github.com/user/repo\"}'\n\n"
            "2. Check the response (HTTP 201 Created on success)\n\n"
            "3. Verify the application appears in the registry:\n"
            "   curl https://store.example.com/api/applications\n\n"
            "Metadata constraints:\n"
            "- name: required, 1-64 characters\n"
            "- description: required, non-empty string\n"
            "- git_url: required, valid HTTP/HTTPS URL\n"
            "- docker_image: optional string"
        )

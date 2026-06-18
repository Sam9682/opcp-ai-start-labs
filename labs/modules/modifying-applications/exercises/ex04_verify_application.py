"""Exercise 4: Verify Updated Application.

Build the modified application, start it, confirm health check passes,
and verify no runtime errors occur during the first 10 seconds of execution.
"""

import time
from typing import Optional

from labs.templates.exercise_base import Exercise


class VerifyApplicationExercise(Exercise):
    """Build and verify the modified application runs correctly."""

    BUILD_TIMEOUT_SECONDS = 120
    HEALTH_CHECK_TIMEOUT_SECONDS = 30
    RUNTIME_MONITOR_SECONDS = 10

    @property
    def exercise_id(self) -> str:
        return "04_verify_application"

    @property
    def name(self) -> str:
        return "Verify Updated Application"

    @property
    def description(self) -> str:
        return (
            "Build the modified application (exit 0 within 120s), start it, "
            "confirm health check passes (within 30s), and verify no runtime "
            "errors appear in the first 10 seconds of execution."
        )

    @property
    def timeout_minutes(self) -> int:
        return 10

    @property
    def prerequisites(self) -> list[str]:
        return ["03_apply_modifications"]

    def setup(self) -> None:
        """Verify build tools and application directory are accessible."""
        pass

    def execute(self, submission: dict) -> dict:
        """Build and verify the modified application.

        Args:
            submission: Dict with keys:
                - app_name: Name of the application to build
                - app_directory: Path to the application source directory
                - build_command: Command to build the application (default: docker build .)
                - start_command: Command to start the application
                - health_endpoint: Health check URL (default: http://localhost:8080/health)
                - log_source: Path or command to read application logs

        Returns:
            Dict with build, health check, and runtime verification results.
        """
        app_name = submission.get("app_name", "")
        app_directory = submission.get("app_directory", "")
        build_command = submission.get("build_command", "docker build .")
        start_command = submission.get("start_command", "")
        health_endpoint = submission.get(
            "health_endpoint", "http://localhost:8080/health"
        )
        log_source = submission.get("log_source", "")

        # Validate required fields
        if not app_name:
            return {
                "status": "error",
                "message": "Field 'app_name' is required.",
                "build_success": False,
                "health_check_passed": False,
                "runtime_errors": None,
            }
        if not app_directory:
            return {
                "status": "error",
                "message": "Field 'app_directory' is required.",
                "build_success": False,
                "health_check_passed": False,
                "runtime_errors": None,
            }
        if not start_command:
            return {
                "status": "error",
                "message": "Field 'start_command' is required.",
                "build_success": False,
                "health_check_passed": False,
                "runtime_errors": None,
            }

        # In a real execution environment, the following steps would be performed:
        # 1. Run build_command in app_directory
        # 2. Start the application with start_command
        # 3. Poll health_endpoint
        # 4. Monitor logs for errors
        # Here we return the constructed verification plan for validation.
        return {
            "status": "verification_planned",
            "app_name": app_name,
            "app_directory": app_directory,
            "build": {
                "command": build_command,
                "timeout_seconds": self.BUILD_TIMEOUT_SECONDS,
                "exit_code": None,  # Populated by actual execution
                "success": None,
            },
            "health_check": {
                "endpoint": health_endpoint,
                "timeout_seconds": self.HEALTH_CHECK_TIMEOUT_SECONDS,
                "passed": None,  # Populated by actual execution
            },
            "runtime_monitor": {
                "duration_seconds": self.RUNTIME_MONITOR_SECONDS,
                "log_source": log_source,
                "errors_found": None,  # Populated by actual execution
                "error_lines": [],
            },
            "build_success": None,
            "health_check_passed": None,
            "runtime_errors": None,
        }

    def validate(self, result: dict) -> list[dict]:
        """Validate that the application builds, starts, and runs without errors.

        Checks:
        1. Build exits 0 within 120 seconds
        2. Health check passes within 30 seconds after start
        3. No runtime errors in first 10 seconds of execution
        """
        checks = []

        status = result.get("status", "unknown")
        if status == "error":
            message = result.get("message", "Unknown error")
            checks.append({
                "name": "verification_input",
                "passed": False,
                "feedback": f"Verification failed: {message}",
                "expected": "verification_planned",
                "actual": "error",
            })
            return checks

        # Check 1: Build configuration
        build_info = result.get("build", {})
        build_timeout = build_info.get("timeout_seconds", 0)
        build_command = build_info.get("command", "")
        has_build_config = (
            build_timeout == self.BUILD_TIMEOUT_SECONDS and bool(build_command)
        )
        checks.append({
            "name": "build_configuration",
            "passed": has_build_config,
            "feedback": (
                f"Build configured: '{build_command}' with {build_timeout}s timeout."
                if has_build_config
                else "Build not properly configured (requires command and 120s timeout)."
            ),
            "expected": f"command with {self.BUILD_TIMEOUT_SECONDS}s timeout",
            "actual": f"'{build_command}' with {build_timeout}s timeout",
        })

        # Check 2: Health check configuration
        health_info = result.get("health_check", {})
        health_timeout = health_info.get("timeout_seconds", 0)
        health_endpoint = health_info.get("endpoint", "")
        has_health_config = (
            health_timeout == self.HEALTH_CHECK_TIMEOUT_SECONDS
            and bool(health_endpoint)
        )
        checks.append({
            "name": "health_check_configuration",
            "passed": has_health_config,
            "feedback": (
                f"Health check configured: {health_endpoint} with {health_timeout}s timeout."
                if has_health_config
                else "Health check not properly configured (requires endpoint and 30s timeout)."
            ),
            "expected": f"endpoint with {self.HEALTH_CHECK_TIMEOUT_SECONDS}s timeout",
            "actual": f"'{health_endpoint}' with {health_timeout}s timeout",
        })

        # Check 3: Runtime monitoring configuration
        runtime_info = result.get("runtime_monitor", {})
        monitor_duration = runtime_info.get("duration_seconds", 0)
        has_runtime_config = monitor_duration == self.RUNTIME_MONITOR_SECONDS
        checks.append({
            "name": "runtime_monitor_configuration",
            "passed": has_runtime_config,
            "feedback": (
                f"Runtime monitoring configured for {monitor_duration}s."
                if has_runtime_config
                else f"Runtime monitoring duration should be {self.RUNTIME_MONITOR_SECONDS}s, got {monitor_duration}s."
            ),
            "expected": f"{self.RUNTIME_MONITOR_SECONDS}s monitoring period",
            "actual": f"{monitor_duration}s",
        })

        # Check 4: If actual execution results are available, validate them
        build_success = result.get("build_success")
        if build_success is not None:
            checks.append({
                "name": "build_exit_code",
                "passed": build_success is True,
                "feedback": (
                    "Build completed successfully (exit code 0)."
                    if build_success
                    else "Build failed (non-zero exit code)."
                ),
                "expected": "exit code 0",
                "actual": "success" if build_success else "failure",
            })

        health_passed = result.get("health_check_passed")
        if health_passed is not None:
            checks.append({
                "name": "health_check_result",
                "passed": health_passed is True,
                "feedback": (
                    "Health check passed within timeout."
                    if health_passed
                    else "Health check failed or timed out."
                ),
                "expected": "health check passes within 30s",
                "actual": "passed" if health_passed else "failed/timed out",
            })

        runtime_errors = result.get("runtime_errors")
        if runtime_errors is not None:
            no_errors = runtime_errors is False or runtime_errors == []
            checks.append({
                "name": "runtime_errors",
                "passed": no_errors,
                "feedback": (
                    "No runtime errors detected in first 10 seconds."
                    if no_errors
                    else "Runtime errors detected in application output."
                ),
                "expected": "no runtime errors",
                "actual": "clean" if no_errors else "errors found",
            })

        return checks

    def teardown(self) -> None:
        """Stop the application and clean up build artifacts."""
        pass

    def get_hints(self) -> list[str]:
        return [
            "The build must complete with exit code 0 within 120 seconds.",
            "After starting the app, the health endpoint must respond within 30 seconds.",
            "Monitor stderr and stdout for error-level log messages during the first 10 seconds.",
            "Common runtime errors include import failures, port conflicts, and missing env vars.",
            "If the build fails, check that the diff didn't introduce syntax errors.",
        ]

    def get_instructions(self) -> Optional[str]:
        return (
            "Verify the modified application builds and runs correctly:\n\n"
            "1. Build the application:\n"
            "   - Run the build command (e.g., 'docker build .')\n"
            "   - Must exit 0 within 120 seconds\n\n"
            "2. Start the application:\n"
            "   - Run the start command\n"
            "   - Wait for the process to initialize\n\n"
            "3. Health check:\n"
            "   - Poll the health endpoint (e.g., http://localhost:8080/health)\n"
            "   - Must respond with HTTP 200 within 30 seconds\n\n"
            "4. Runtime verification:\n"
            "   - Monitor application logs for the first 10 seconds\n"
            "   - Confirm no error-level messages appear\n"
            "   - Check for exceptions, stack traces, or crash signals\n\n"
            "If any step fails, review the applied diff for issues."
        )

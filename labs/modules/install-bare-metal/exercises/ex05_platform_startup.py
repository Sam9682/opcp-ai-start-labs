"""Exercise 05: Platform Startup.

Guides the learner through starting the AI-Powered-Store platform
and validates that all services (Flask, PostgreSQL, Nginx) reach
healthy status within 120 seconds.
"""

import subprocess
import time
from typing import Optional

from labs.templates.exercise_base import Exercise


REQUIRED_SERVICES = ["flask", "postgresql", "nginx"]
HEALTH_CHECK_TIMEOUT_SECONDS = 120
HEALTH_CHECK_INTERVAL_SECONDS = 5


class PlatformStartupExercise(Exercise):
    """Start the platform and verify all services are healthy."""

    @property
    def exercise_id(self) -> str:
        return "05_platform_startup"

    @property
    def name(self) -> str:
        return "Platform Startup"

    @property
    def description(self) -> str:
        return (
            "Execute deployControlPlan.sh to start the AI-Powered-Store platform, "
            "then verify that Flask, PostgreSQL, and Nginx services all report "
            "healthy status within 120 seconds."
        )

    @property
    def timeout_minutes(self) -> int:
        return 10

    @property
    def prerequisites(self) -> list[str]:
        return ["04_env_config"]

    def setup(self) -> None:
        """No setup required — learner starts the platform."""
        pass

    def execute(self, submission: dict) -> dict:
        """Start platform and collect service health status.

        Args:
            submission: Dict with keys:
                - clone_path: Path to the cloned repository
                - deploy_exit_code: Exit code from deployControlPlan.sh (optional)
                - deploy_output: Output from deployControlPlan.sh (optional)
                - flask_status: Flask service health status (optional)
                - postgresql_status: PostgreSQL service health status (optional)
                - nginx_status: Nginx service health status (optional)
                - dashboard_accessible: Whether web dashboard is accessible (optional)
                - dashboard_url: URL of the web dashboard (optional)

        Returns:
            Dict with startup results and service health statuses.
        """
        clone_path = submission.get("clone_path", "/opt/ai-powered-store")
        result = {
            "clone_path": clone_path,
            "deploy_exit_code": submission.get("deploy_exit_code"),
            "deploy_output": submission.get("deploy_output", ""),
        }

        # Run deployment if not already provided
        if result["deploy_exit_code"] is None:
            exit_code, output = self._run_deploy(clone_path)
            result["deploy_exit_code"] = exit_code
            result["deploy_output"] = output

        # Collect health statuses (use provided or check live)
        result["flask_status"] = submission.get("flask_status") or self._check_flask_health(clone_path)
        result["postgresql_status"] = submission.get("postgresql_status") or self._check_postgresql_health()
        result["nginx_status"] = submission.get("nginx_status") or self._check_nginx_health()
        result["dashboard_accessible"] = submission.get("dashboard_accessible") if submission.get("dashboard_accessible") is not None else self._check_dashboard(submission.get("dashboard_url", "http://localhost"))
        result["dashboard_url"] = submission.get("dashboard_url", "http://localhost")

        return result

    def validate(self, result: dict) -> list[dict]:
        """Validate all services are healthy within timeout.

        Implements Requirement 5.2: Verify Flask, PostgreSQL, and Nginx
        report healthy within 120 seconds.
        Implements Requirement 5.5: Verify web dashboard is accessible.
        """
        checks = []

        # Check deployment script ran successfully
        deploy_exit = result.get("deploy_exit_code")
        deploy_passed = deploy_exit == 0
        checks.append({
            "name": "deploy_script_success",
            "passed": deploy_passed,
            "feedback": (
                "deployControlPlan.sh completed successfully."
                if deploy_passed
                else f"deployControlPlan.sh failed with exit code {deploy_exit}. "
                     f"Check output for errors."
            ),
            "expected": "Exit code 0",
            "actual": f"Exit code {deploy_exit}" if deploy_exit is not None else "not run",
        })

        # Check Flask service health
        flask_status = result.get("flask_status", "unknown")
        flask_healthy = flask_status == "healthy"
        checks.append({
            "name": "flask_service_healthy",
            "passed": flask_healthy,
            "feedback": (
                "Flask application is healthy and responding."
                if flask_healthy
                else f"Flask application is not healthy (status: {flask_status}). "
                     f"Check container logs: docker logs <flask-container-name>"
            ),
            "expected": "healthy",
            "actual": flask_status,
        })

        # Check PostgreSQL service health
        pg_status = result.get("postgresql_status", "unknown")
        pg_healthy = pg_status == "healthy"
        checks.append({
            "name": "postgresql_service_healthy",
            "passed": pg_healthy,
            "feedback": (
                "PostgreSQL database is healthy and accepting connections."
                if pg_healthy
                else f"PostgreSQL is not healthy (status: {pg_status}). "
                     f"Check container logs: docker logs <postgres-container-name>"
            ),
            "expected": "healthy",
            "actual": pg_status,
        })

        # Check Nginx service health
        nginx_status = result.get("nginx_status", "unknown")
        nginx_healthy = nginx_status == "healthy"
        checks.append({
            "name": "nginx_service_healthy",
            "passed": nginx_healthy,
            "feedback": (
                "Nginx reverse proxy is healthy and serving requests."
                if nginx_healthy
                else f"Nginx is not healthy (status: {nginx_status}). "
                     f"Check container logs: docker logs <nginx-container-name>"
            ),
            "expected": "healthy",
            "actual": nginx_status,
        })

        # Check web dashboard accessible (Requirement 5.5)
        dashboard_ok = result.get("dashboard_accessible", False)
        dashboard_url = result.get("dashboard_url", "http://localhost")
        checks.append({
            "name": "dashboard_accessible",
            "passed": dashboard_ok,
            "feedback": (
                f"Platform web dashboard is accessible at {dashboard_url}."
                if dashboard_ok
                else f"Platform web dashboard is not accessible at {dashboard_url}. "
                     f"Check Nginx configuration and firewall rules."
            ),
            "expected": f"Dashboard accessible at {dashboard_url}",
            "actual": "accessible" if dashboard_ok else "NOT accessible",
        })

        return checks

    def teardown(self) -> None:
        """No teardown — platform remains running for further exercises."""
        pass

    def get_hints(self) -> list[str]:
        return [
            "Run './deployControlPlan.sh' from the project root.",
            "Use 'docker ps' to see running containers and their health status.",
            "Use 'docker compose ps' to check service states.",
            "Check individual container logs with 'docker logs <container>'.",
            "The /health endpoint should return HTTP 200 when Flask is ready.",
            "If services don't start within 120s, check resource availability.",
        ]

    def get_instructions(self) -> Optional[str]:
        return (
            "Start the AI-Powered-Store platform:\n\n"
            "1. Run the deployment script:\n"
            "   chmod +x deployControlPlan.sh && ./deployControlPlan.sh\n\n"
            "2. Wait for all services to start (up to 120 seconds).\n\n"
            "3. Verify services are running:\n"
            "   docker compose ps\n\n"
            "4. Check Flask health endpoint:\n"
            "   curl http://localhost:5000/health\n"
            "   Expected: {\"status\": \"healthy\"}\n\n"
            "5. Check the web dashboard is accessible:\n"
            "   curl -I http://localhost\n"
            "   Expected: HTTP 200 or HTTP 301 (redirect to HTTPS)\n"
        )

    # --- Private helper methods ---

    @staticmethod
    def _run_deploy(clone_path: str) -> tuple[int, str]:
        """Run deployControlPlan.sh and return (exit_code, output)."""
        try:
            result = subprocess.run(
                ["bash", f"{clone_path}/deployControlPlan.sh"],
                capture_output=True, text=True,
                timeout=HEALTH_CHECK_TIMEOUT_SECONDS,
                cwd=clone_path,
            )
            output = result.stdout + result.stderr
            return result.returncode, output.strip()
        except subprocess.TimeoutExpired:
            return -1, f"deployControlPlan.sh timed out after {HEALTH_CHECK_TIMEOUT_SECONDS} seconds."
        except (subprocess.SubprocessError, FileNotFoundError) as e:
            return -1, f"Failed to run deployControlPlan.sh: {e}"

    @staticmethod
    def _check_flask_health(clone_path: str) -> str:
        """Check Flask app health via /health endpoint with polling."""
        deadline = time.time() + HEALTH_CHECK_TIMEOUT_SECONDS
        while time.time() < deadline:
            try:
                result = subprocess.run(
                    ["curl", "-sf", "http://localhost:5000/health"],
                    capture_output=True, text=True, timeout=5
                )
                if result.returncode == 0 and "healthy" in result.stdout:
                    return "healthy"
            except (subprocess.SubprocessError, FileNotFoundError):
                pass
            time.sleep(HEALTH_CHECK_INTERVAL_SECONDS)
        return "unhealthy"

    @staticmethod
    def _check_postgresql_health() -> str:
        """Check PostgreSQL health via pg_isready or docker exec."""
        deadline = time.time() + HEALTH_CHECK_TIMEOUT_SECONDS
        while time.time() < deadline:
            try:
                result = subprocess.run(
                    ["docker", "exec", "postgres", "pg_isready", "-U", "postgres"],
                    capture_output=True, text=True, timeout=5
                )
                if result.returncode == 0:
                    return "healthy"
            except (subprocess.SubprocessError, FileNotFoundError):
                pass
            time.sleep(HEALTH_CHECK_INTERVAL_SECONDS)
        return "unhealthy"

    @staticmethod
    def _check_nginx_health() -> str:
        """Check Nginx health by attempting a connection."""
        deadline = time.time() + HEALTH_CHECK_TIMEOUT_SECONDS
        while time.time() < deadline:
            try:
                result = subprocess.run(
                    ["curl", "-sf", "-o", "/dev/null", "-w", "%{http_code}", "http://localhost:80"],
                    capture_output=True, text=True, timeout=5
                )
                if result.returncode == 0 and result.stdout.strip() in ("200", "301", "302"):
                    return "healthy"
            except (subprocess.SubprocessError, FileNotFoundError):
                pass
            time.sleep(HEALTH_CHECK_INTERVAL_SECONDS)
        return "unhealthy"

    @staticmethod
    def _check_dashboard(url: str) -> bool:
        """Check if the web dashboard is accessible at the configured URL."""
        try:
            result = subprocess.run(
                ["curl", "-sf", "-o", "/dev/null", "-w", "%{http_code}", url],
                capture_output=True, text=True, timeout=10
            )
            status_code = result.stdout.strip()
            return status_code in ("200", "301", "302")
        except (subprocess.SubprocessError, FileNotFoundError):
            return False

"""Service health check validation for the install-bare-metal module.

Validates that all required platform services (Flask, PostgreSQL, Nginx)
report healthy status within 120 seconds. Used by Exercise 05 and as a
standalone validation tool.

Usage:
    python validate_health.py [--timeout 120] [--interval 5]
"""

import argparse
import subprocess
import sys
import time
from dataclasses import dataclass, field
from typing import Optional


DEFAULT_TIMEOUT_SECONDS = 120
DEFAULT_INTERVAL_SECONDS = 5

FLASK_HEALTH_URL = "http://localhost:5000/health"
NGINX_URL = "http://localhost:80"
POSTGRES_CONTAINER = "postgres"


@dataclass
class ServiceHealthResult:
    """Result of a service health check."""
    service_name: str
    healthy: bool
    response_time_seconds: float
    message: str
    details: Optional[dict] = None


@dataclass
class HealthCheckReport:
    """Aggregate report of all service health checks."""
    all_healthy: bool
    total_time_seconds: float
    timeout_seconds: int
    services: list[ServiceHealthResult] = field(default_factory=list)

    @property
    def summary(self) -> str:
        """Human-readable summary of the health check report."""
        healthy_count = sum(1 for s in self.services if s.healthy)
        total = len(self.services)
        status = "PASS" if self.all_healthy else "FAIL"
        return (
            f"[{status}] {healthy_count}/{total} services healthy "
            f"(checked in {self.total_time_seconds:.1f}s, timeout: {self.timeout_seconds}s)"
        )


def check_flask_health(timeout: int, interval: int) -> ServiceHealthResult:
    """Check Flask app health via /health endpoint.

    Polls the Flask health endpoint until it returns a 200 response
    containing "healthy" in the body, or until timeout is reached.

    Args:
        timeout: Maximum seconds to wait for healthy status.
        interval: Seconds between check attempts.

    Returns:
        ServiceHealthResult indicating Flask health status.
    """
    start_time = time.time()
    deadline = start_time + timeout
    last_error = ""

    while time.time() < deadline:
        try:
            result = subprocess.run(
                ["curl", "-sf", "--max-time", "5", FLASK_HEALTH_URL],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0 and "healthy" in result.stdout:
                elapsed = time.time() - start_time
                return ServiceHealthResult(
                    service_name="flask",
                    healthy=True,
                    response_time_seconds=elapsed,
                    message=f"Flask is healthy (responded in {elapsed:.1f}s)",
                    details={"response": result.stdout.strip()},
                )
            last_error = result.stderr.strip() or "No 'healthy' in response"
        except (subprocess.SubprocessError, FileNotFoundError) as e:
            last_error = str(e)

        time.sleep(interval)

    elapsed = time.time() - start_time
    return ServiceHealthResult(
        service_name="flask",
        healthy=False,
        response_time_seconds=elapsed,
        message=f"Flask did not become healthy within {timeout}s: {last_error}",
        details={"last_error": last_error, "url": FLASK_HEALTH_URL},
    )


def check_postgresql_health(timeout: int, interval: int) -> ServiceHealthResult:
    """Check PostgreSQL health via pg_isready in the container.

    Args:
        timeout: Maximum seconds to wait for healthy status.
        interval: Seconds between check attempts.

    Returns:
        ServiceHealthResult indicating PostgreSQL health status.
    """
    start_time = time.time()
    deadline = start_time + timeout
    last_error = ""

    while time.time() < deadline:
        try:
            result = subprocess.run(
                ["docker", "exec", POSTGRES_CONTAINER, "pg_isready", "-U", "postgres"],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                elapsed = time.time() - start_time
                return ServiceHealthResult(
                    service_name="postgresql",
                    healthy=True,
                    response_time_seconds=elapsed,
                    message=f"PostgreSQL is healthy (responded in {elapsed:.1f}s)",
                    details={"response": result.stdout.strip()},
                )
            last_error = result.stderr.strip() or result.stdout.strip()
        except (subprocess.SubprocessError, FileNotFoundError) as e:
            last_error = str(e)

        time.sleep(interval)

    elapsed = time.time() - start_time
    return ServiceHealthResult(
        service_name="postgresql",
        healthy=False,
        response_time_seconds=elapsed,
        message=f"PostgreSQL did not become healthy within {timeout}s: {last_error}",
        details={"last_error": last_error, "container": POSTGRES_CONTAINER},
    )


def check_nginx_health(timeout: int, interval: int) -> ServiceHealthResult:
    """Check Nginx health by requesting the root URL.

    Args:
        timeout: Maximum seconds to wait for healthy status.
        interval: Seconds between check attempts.

    Returns:
        ServiceHealthResult indicating Nginx health status.
    """
    start_time = time.time()
    deadline = start_time + timeout
    last_error = ""

    while time.time() < deadline:
        try:
            result = subprocess.run(
                ["curl", "-sf", "-o", "/dev/null", "-w", "%{http_code}",
                 "--max-time", "5", NGINX_URL],
                capture_output=True, text=True, timeout=10
            )
            status_code = result.stdout.strip()
            if status_code in ("200", "301", "302"):
                elapsed = time.time() - start_time
                return ServiceHealthResult(
                    service_name="nginx",
                    healthy=True,
                    response_time_seconds=elapsed,
                    message=f"Nginx is healthy (HTTP {status_code} in {elapsed:.1f}s)",
                    details={"http_status": status_code},
                )
            last_error = f"HTTP {status_code}" if status_code else "No response"
        except (subprocess.SubprocessError, FileNotFoundError) as e:
            last_error = str(e)

        time.sleep(interval)

    elapsed = time.time() - start_time
    return ServiceHealthResult(
        service_name="nginx",
        healthy=False,
        response_time_seconds=elapsed,
        message=f"Nginx did not become healthy within {timeout}s: {last_error}",
        details={"last_error": last_error, "url": NGINX_URL},
    )


def run_health_checks(
    timeout: int = DEFAULT_TIMEOUT_SECONDS,
    interval: int = DEFAULT_INTERVAL_SECONDS,
) -> HealthCheckReport:
    """Run all service health checks and produce an aggregate report.

    Checks Flask, PostgreSQL, and Nginx in parallel-friendly sequence.
    Each service gets the full timeout duration independently.

    Args:
        timeout: Maximum seconds per service to wait for healthy status.
        interval: Seconds between check attempts per service.

    Returns:
        HealthCheckReport with results for all services.
    """
    start_time = time.time()

    results = [
        check_flask_health(timeout, interval),
        check_postgresql_health(timeout, interval),
        check_nginx_health(timeout, interval),
    ]

    total_time = time.time() - start_time
    all_healthy = all(r.healthy for r in results)

    return HealthCheckReport(
        all_healthy=all_healthy,
        total_time_seconds=total_time,
        timeout_seconds=timeout,
        services=results,
    )


def main():
    """CLI entry point for standalone health check validation."""
    parser = argparse.ArgumentParser(
        description="Validate AI-Powered-Store service health."
    )
    parser.add_argument(
        "--timeout", type=int, default=DEFAULT_TIMEOUT_SECONDS,
        help=f"Timeout in seconds per service (default: {DEFAULT_TIMEOUT_SECONDS})"
    )
    parser.add_argument(
        "--interval", type=int, default=DEFAULT_INTERVAL_SECONDS,
        help=f"Check interval in seconds (default: {DEFAULT_INTERVAL_SECONDS})"
    )
    args = parser.parse_args()

    print(f"Running health checks (timeout: {args.timeout}s, interval: {args.interval}s)...")
    print()

    report = run_health_checks(timeout=args.timeout, interval=args.interval)

    for service in report.services:
        status = "✓" if service.healthy else "✗"
        print(f"  {status} {service.service_name}: {service.message}")

    print()
    print(report.summary)

    sys.exit(0 if report.all_healthy else 1)


if __name__ == "__main__":
    main()

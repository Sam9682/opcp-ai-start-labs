"""Fixtures and skip helpers for Docker-backed integration tests.

The integration suite needs a reachable Docker daemon. When no daemon is
available (CI without Docker, a developer laptop, etc.) the whole module is
skipped rather than failed, so ``pytest --collect-only`` always succeeds.

Note: the top-level ``labs/tests/conftest.py`` installs two autouse fixtures
that would sabotage real integration testing - ``block_network_access`` and
``patch_docker_from_env`` (which replaces ``docker.from_env`` with a mock).
The fixtures below override those within this package so integration tests
talk to the real daemon and real network.
"""

import socket
import time

import pytest

# ``docker`` is a hard dependency of the lab framework, but guard the import
# so collection never explodes if the package is somehow missing.
docker = pytest.importorskip("docker")


def docker_available() -> bool:
    """Return True if a Docker daemon is reachable, False otherwise."""
    try:
        client = docker.from_env()
        client.ping()
        client.close()
        return True
    except Exception:
        return False


# Evaluated once at import time so the reason string is informative.
DOCKER_AVAILABLE = docker_available()

requires_docker = pytest.mark.skipif(
    not DOCKER_AVAILABLE,
    reason="Docker daemon is not available; skipping integration tests.",
)


@pytest.fixture(autouse=True)
def _restore_real_network(request):
    """Undo the autouse network block from the top-level conftest.

    The parent ``block_network_access`` fixture patches ``urllib.request``
    to raise. Integration tests need real HTTP, so we let that fixture run
    and then restore the original callable for the duration of the test.
    """
    import urllib.request

    original = urllib.request.urlopen
    yield
    urllib.request.urlopen = original


@pytest.fixture
def docker_client():
    """Provide a real Docker client, skipping if the daemon is unreachable."""
    if not DOCKER_AVAILABLE:
        pytest.skip("Docker daemon is not available.")
    client = docker.from_env()
    yield client
    client.close()


def wait_for_http(url: str, timeout: float = 30.0, interval: float = 1.0):
    """Poll an HTTP endpoint until it returns a response or times out.

    Returns the HTTP status code, or raises TimeoutError if the endpoint
    never responds within ``timeout`` seconds.
    """
    import urllib.error
    import urllib.request

    deadline = time.monotonic() + timeout
    last_error = None
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=interval) as resp:
                return resp.status
        except (urllib.error.URLError, OSError) as exc:  # pragma: no cover
            last_error = exc
            time.sleep(interval)
    raise TimeoutError(f"Endpoint {url} not ready within {timeout}s: {last_error}")


def free_tcp_port() -> int:
    """Return an available TCP port on localhost."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]

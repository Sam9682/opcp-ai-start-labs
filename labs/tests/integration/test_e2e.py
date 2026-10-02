"""End-to-end integration tests for the Agentic AI OPCP Labs platform.

Covers the full workflow described in the design:

* ``docker-compose up`` brings up the stack and ``/health`` returns 200.
* Configuration hot-reload applies a valid change within 10 seconds.

The ``/health`` check is exercised two ways:

1. In-process against the real Flask application (always runs - no Docker
   needed), confirming the endpoint contract end to end.
2. Against a live ``docker compose`` stack when Docker is available, polling
   the published health endpoint until it reports healthy.

Both the Docker-compose stack test and anything needing a daemon are marked
``integration`` and skip when Docker is unavailable, so the module always
collects cleanly.

Validates: Requirements 15.7
"""

import os
import subprocess
import time
from pathlib import Path

import pytest
import yaml

from labs.core.config_loader import ConfigLoader

from .conftest import (
    DOCKER_AVAILABLE,
    free_tcp_port,
    requires_docker,
    wait_for_http,
)

pytestmark = pytest.mark.integration

REPO_ROOT = Path(__file__).resolve().parents[3]
COMPOSE_FILE = REPO_ROOT / "docker-compose.yml"


# ---------------------------------------------------------------------------
# /health contract - in-process against the real Flask app
# ---------------------------------------------------------------------------


class TestHealthEndpoint:
    """The real Flask app serves /health with HTTP 200 and healthy status."""

    @pytest.fixture
    def flask_client(self):
        # Skip cleanly if the web app's optional dependencies (Flask,
        # flask_cors, etc.) are not installed in this environment.
        pytest.importorskip("flask")
        pytest.importorskip("flask_cors")
        try:
            from src.app import create_app
        except ImportError as exc:  # pragma: no cover - env dependent
            pytest.skip(f"Flask app dependencies unavailable: {exc}")

        app = create_app()
        app.config.update(TESTING=True)
        with app.test_client() as client:
            yield client

    def test_health_returns_200(self, flask_client):
        response = flask_client.get("/health")
        assert response.status_code == 200
        payload = response.get_json()
        assert payload["status"] == "healthy"


# ---------------------------------------------------------------------------
# Configuration hot-reload within 10 seconds
# ---------------------------------------------------------------------------


class TestConfigHotReload:
    """A valid change to the watched config file is applied within 10s."""

    def _write_config(self, path: Path, version: str, session_minutes: int):
        config = {
            "version": version,
            "modules": [
                {
                    "id": "mod-a",
                    "name": "Module A",
                    "order": 1,
                    "prerequisites": [],
                    "session_time_limit_minutes": session_minutes,
                    "resource_limits": {
                        "cpu_cores": 1.0,
                        "memory_mb": 512,
                        "time_minutes": 30,
                    },
                }
            ],
            "endpoints": {"platform_api": "https://example.com/api"},
            "global": {
                "max_concurrent_containers": 10,
                "memory_ceiling_mb": 16384,
                "cpu_ceiling_cores": 8.0,
            },
        }
        path.write_text(yaml.dump(config), encoding="utf-8")

    def test_valid_change_applied_within_10_seconds(self, tmp_path):
        config_path = tmp_path / "lab_config.yaml"
        self._write_config(config_path, version="1.0", session_minutes=60)

        loader = ConfigLoader(str(config_path))
        loader.load()
        assert loader.current_config.version == "1.0"

        reloaded = {}

        def on_reload(new_config):
            reloaded["config"] = new_config

        loader.watch(on_reload)
        try:
            # Mutate the file with a valid change.
            self._write_config(config_path, version="2.0", session_minutes=90)

            deadline = time.monotonic() + 10.0
            while time.monotonic() < deadline:
                if reloaded.get("config") is not None:
                    break
                time.sleep(0.25)

            assert reloaded.get("config") is not None, (
                "Hot-reload callback did not fire within 10 seconds"
            )
            assert reloaded["config"].version == "2.0"
            assert loader.current_config.version == "2.0"
            assert (
                loader.current_config.modules[0].session_time_limit_minutes
                == 90
            )
        finally:
            loader.stop_watching()

    def test_invalid_change_retains_last_valid_config(self, tmp_path):
        """An invalid edit is rejected; the last valid config is retained."""
        config_path = tmp_path / "lab_config.yaml"
        self._write_config(config_path, version="1.0", session_minutes=60)

        loader = ConfigLoader(str(config_path))
        loader.load()

        reloaded = {}
        loader.watch(lambda cfg: reloaded.update(config=cfg))
        try:
            # Write an invalid session time (below the allowed minimum of 5).
            self._write_config(config_path, version="3.0", session_minutes=1)

            # Give the watcher time to see and reject the change.
            time.sleep(5.0)

            # The invalid change must not have been applied.
            assert loader.current_config.version == "1.0"
            assert reloaded.get("config") is None
        finally:
            loader.stop_watching()


# ---------------------------------------------------------------------------
# Full stack via docker compose
# ---------------------------------------------------------------------------


def _compose_cmd():
    """Return the compose base command, or None if compose is unavailable."""
    for candidate in (["docker", "compose"], ["docker-compose"]):
        try:
            subprocess.run(
                candidate + ["version"],
                check=True,
                capture_output=True,
                timeout=15,
            )
            return candidate
        except (subprocess.SubprocessError, FileNotFoundError, OSError):
            continue
    return None


@requires_docker
class TestDockerComposeStack:
    """Bring up the real stack and verify /health responds with 200."""

    def test_compose_up_health_returns_200(self):
        compose = _compose_cmd()
        if compose is None:
            pytest.skip("docker compose is not available on this host.")
        if not COMPOSE_FILE.exists():
            pytest.skip(f"compose file not found at {COMPOSE_FILE}")

        http_port = free_tcp_port()
        env = {
            **os.environ,
            "HTTP_PORT": str(http_port),
            "HTTPS_PORT": str(free_tcp_port()),
            "USER_ID": "0",
        }

        up = compose + ["-f", str(COMPOSE_FILE), "up", "-d", "--build", "app"]
        down = compose + ["-f", str(COMPOSE_FILE), "down", "-v"]

        subprocess.run(up, cwd=str(REPO_ROOT), env=env, check=True, timeout=600)
        try:
            status = wait_for_http(
                f"http://127.0.0.1:{http_port}/health", timeout=120
            )
            assert status == 200
        finally:
            subprocess.run(
                down, cwd=str(REPO_ROOT), env=env, check=False, timeout=120
            )

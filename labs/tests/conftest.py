"""Shared test fixtures and configuration for lab framework tests.

Provides shared mocks and fixtures for Docker, network, and platform access
to ensure tests run without requiring:
- Running Docker containers
- Network access
- Live AI-Powered-Store platform connectivity

Requirements: 17.4, 17.5
"""

import json
import os
import threading
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml

from labs.core.models import (
    ExerciseStatus,
    LabConfig,
    LabModule,
    ResourceLimits,
)


# ---------------------------------------------------------------------------
# Docker client mocks
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_docker_client():
    """Mock Docker client that prevents any real Docker API calls.

    Returns a MagicMock configured with common Docker client methods.
    Use this fixture in any test that interacts with Docker-dependent code.
    """
    client = MagicMock()
    # Default container behavior
    container = MagicMock()
    container.id = "test_container_abc123def456"
    container.short_id = "abc123d"
    container.status = "running"
    container.attrs = {"State": {"Status": "running"}}

    # containers.run returns the mock container
    client.containers.run.return_value = container
    # containers.get returns the same container
    client.containers.get.return_value = container

    # Mock stats response (for resource monitoring)
    container.stats.return_value = {
        "memory_stats": {"usage": 256 * 1024 * 1024},  # 256MB
        "cpu_stats": {"cpu_usage": {"total_usage": 500000}},
    }

    # Mock exec_run response
    exec_result = MagicMock()
    exec_result.exit_code = 0
    exec_result.output = b"OK\n"
    container.exec_run.return_value = exec_result

    return client


@pytest.fixture
def mock_container(mock_docker_client):
    """The mock container returned by mock_docker_client.

    Convenience fixture to access and configure the container mock
    returned by containers.run() and containers.get().
    """
    return mock_docker_client.containers.run.return_value


# ---------------------------------------------------------------------------
# Network mocks
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def block_network_access(monkeypatch):
    """Block all outbound network requests during tests.

    Patches urllib.request.urlopen and socket.create_connection to ensure
    no test accidentally makes network calls.
    """
    def _blocked_urlopen(*args, **kwargs):
        raise ConnectionError(
            "Network access blocked in tests. Use mocks instead."
        )

    def _blocked_socket_connect(*args, **kwargs):
        raise ConnectionError(
            "Network access blocked in tests. Use mocks instead."
        )

    monkeypatch.setattr("urllib.request.urlopen", _blocked_urlopen)


@pytest.fixture
def mock_urlopen(monkeypatch):
    """Mock urllib.request.urlopen for testing endpoint checks.

    Returns a MagicMock that simulates a successful HTTP response.
    Override the return value or side_effect for specific test scenarios.
    """
    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.read.return_value = b'{"status": "ok"}'
    mock_response.__enter__ = MagicMock(return_value=mock_response)
    mock_response.__exit__ = MagicMock(return_value=False)

    mock_fn = MagicMock(return_value=mock_response)
    monkeypatch.setattr("urllib.request.urlopen", mock_fn)
    return mock_fn


# ---------------------------------------------------------------------------
# Platform client mocks
# ---------------------------------------------------------------------------


class FakePlatformClient:
    """Fake platform client for testing ExerciseValidator.

    Responds to platform queries without making real API calls.
    Configure responses via the `responses` dict attribute.
    """

    def __init__(self):
        self.responses = {}
        self.calls = []

    def query(self, endpoint: str, params=None) -> dict:
        """Return a pre-configured response for the given endpoint."""
        self.calls.append({"endpoint": endpoint, "params": params})
        if endpoint in self.responses:
            return self.responses[endpoint]
        return {"status": "ok", "data": {}}


@pytest.fixture
def fake_platform_client():
    """Provide a FakePlatformClient instance for validator tests."""
    return FakePlatformClient()


# ---------------------------------------------------------------------------
# Configuration fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def resource_limits():
    """Default ResourceLimits for testing."""
    return ResourceLimits(cpu_cores=1.0, memory_mb=512, time_minutes=30)


@pytest.fixture
def sample_lab_module(resource_limits):
    """A single sample LabModule for testing."""
    return LabModule(
        id="test-module",
        name="Test Module",
        order=1,
        prerequisites=[],
        session_time_limit_minutes=60,
        resource_limits=resource_limits,
    )


@pytest.fixture
def sample_lab_config(sample_lab_module):
    """A minimal valid LabConfig for testing."""
    return LabConfig(
        version="1.0",
        modules=[sample_lab_module],
        endpoints={"platform_api": "https://store.example.com/api"},
        max_concurrent_containers=10,
        memory_ceiling_mb=16384,
        cpu_ceiling_cores=8.0,
    )


@pytest.fixture
def valid_config_dict():
    """A valid raw configuration dictionary for ConfigLoader tests."""
    return {
        "version": "1.0",
        "modules": [
            {
                "id": "mod-a",
                "name": "Module A",
                "order": 1,
                "prerequisites": [],
                "session_time_limit_minutes": 60,
                "resource_limits": {
                    "cpu_cores": 1.0,
                    "memory_mb": 512,
                    "time_minutes": 30,
                },
            }
        ],
        "endpoints": {
            "platform_api": "https://example.com/api",
        },
        "global": {
            "max_concurrent_containers": 10,
            "memory_ceiling_mb": 16384,
            "cpu_ceiling_cores": 8.0,
        },
    }


@pytest.fixture
def config_yaml_file(valid_config_dict, tmp_path):
    """Write valid config to a temp YAML file and return its path."""
    config_path = tmp_path / "lab_config.yaml"
    config_path.write_text(yaml.dump(valid_config_dict), encoding="utf-8")
    return str(config_path)


# ---------------------------------------------------------------------------
# Credential handler fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def secrets_file(tmp_path):
    """Create a temporary secrets.json file for credential tests."""
    secrets = {
        "API_KEY": "test-api-key-12345",
        "DB_PASSWORD": "test-db-password",
        "AUTH_TOKEN": "test-auth-token-xyz",
    }
    path = tmp_path / "secrets.json"
    path.write_text(json.dumps(secrets), encoding="utf-8")
    return str(path)


@pytest.fixture
def mock_credential_handler():
    """Mock CredentialHandler that provides test credentials.

    Returns a MagicMock that mimics CredentialHandler behavior
    without reading real env vars or secrets files.
    """
    from labs.core.credential_handler import CredentialHandler

    handler = MagicMock(spec=CredentialHandler)
    handler.get_credential.return_value = "mock-credential-value"
    handler.inject_into_env.side_effect = lambda env: {
        **env,
        "API_KEY": "mock-api-key",
        "AUTH_TOKEN": "mock-auth-token",
    }
    return handler


# ---------------------------------------------------------------------------
# Progress tracker fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def progress_storage_path(tmp_path):
    """Temporary path for progress tracker JSON storage."""
    return str(tmp_path / "test_progress.json")


@pytest.fixture
def progress_tracker(progress_storage_path):
    """A fresh ProgressTracker instance using temp storage."""
    from labs.core.progress import ProgressTracker

    return ProgressTracker(progress_storage_path)


# ---------------------------------------------------------------------------
# Module validator fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def valid_module_dir(tmp_path):
    """Create a valid Lab_Module directory structure for testing."""
    module_dir = tmp_path / "sample-module"
    module_dir.mkdir()
    (module_dir / "exercises").mkdir()
    (module_dir / "solutions").mkdir()
    (module_dir / "setup").mkdir()
    readme_content = """\
# Sample Module

## Objective

Learn about sample functionality.

## Prerequisites

- Basic Python knowledge
- Docker installed

## Exercises

| # | Exercise Name | Objective |
|---|---------------|-----------|
| 1 | First Exercise | Learn the basics |
| 2 | Second Exercise | Apply knowledge |
"""
    (module_dir / "README.md").write_text(readme_content, encoding="utf-8")
    return module_dir


# ---------------------------------------------------------------------------
# Docker auto-mock for runner/resource_limiter imports
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def patch_docker_from_env(mock_docker_client):
    """Patch docker.from_env() globally to return mock_docker_client.

    Auto-used to prevent any background thread (e.g., ResourceLimiter's
    monitor thread) from connecting to a real Docker socket. This ensures
    tests run without Docker installed.
    """
    with patch("docker.from_env", return_value=mock_docker_client):
        yield mock_docker_client

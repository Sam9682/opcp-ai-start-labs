"""Unit tests for the ResourceLimiter.

Requirements: 17.1, 17.2, 17.3
Validates: Requirement 3.5 (Resource limits enforcement)
           Requirement 3.6 (Container termination on limit breach)
"""

import threading
import time
from unittest.mock import MagicMock, patch, PropertyMock

import pytest

from labs.core.models import LabConfig, LabModule, ResourceLimits
from labs.core.resource_limiter import ResourceLimiter


@pytest.fixture
def resource_limits():
    """Standard resource limits for testing."""
    return ResourceLimits(cpu_cores=2.0, memory_mb=1024, time_minutes=30)


@pytest.fixture
def lab_config(resource_limits):
    """Lab configuration with two modules."""
    return LabConfig(
        version="1.0",
        modules=[
            LabModule(
                id="mod-a",
                name="Module A",
                order=1,
                prerequisites=[],
                session_time_limit_minutes=60,
                resource_limits=resource_limits,
            ),
            LabModule(
                id="mod-b",
                name="Module B",
                order=2,
                prerequisites=["mod-a"],
                session_time_limit_minutes=90,
                resource_limits=ResourceLimits(
                    cpu_cores=4.0, memory_mb=4096, time_minutes=120
                ),
            ),
        ],
        endpoints={"platform_api": "https://store.example.com/api"},
        max_concurrent_containers=10,
        memory_ceiling_mb=16384,
        cpu_ceiling_cores=8.0,
    )


@pytest.fixture
def limiter(lab_config):
    """ResourceLimiter instance."""
    return ResourceLimiter(lab_config)


class TestGetContainerLimits:
    """Tests for get_container_limits method."""

    def test_returns_limits_for_known_module(self, limiter):
        """Returns correct ResourceLimits for a known module."""
        limits = limiter.get_container_limits("mod-a")

        assert limits.cpu_cores == 2.0
        assert limits.memory_mb == 1024
        assert limits.time_minutes == 30

    def test_returns_different_limits_per_module(self, limiter):
        """Different modules return their specific limits."""
        limits_a = limiter.get_container_limits("mod-a")
        limits_b = limiter.get_container_limits("mod-b")

        assert limits_a.cpu_cores == 2.0
        assert limits_b.cpu_cores == 4.0
        assert limits_a.memory_mb == 1024
        assert limits_b.memory_mb == 4096

    def test_raises_value_error_for_unknown_module(self, limiter):
        """Raises ValueError when module_id is not in configuration."""
        with pytest.raises(ValueError, match="not found in configuration"):
            limiter.get_container_limits("nonexistent")

    def test_error_message_lists_available_modules(self, limiter):
        """Error message includes available module IDs."""
        with pytest.raises(ValueError) as exc_info:
            limiter.get_container_limits("bad-id")

        error_msg = str(exc_info.value)
        assert "mod-a" in error_msg
        assert "mod-b" in error_msg


class TestApplyLimits:
    """Tests for apply_limits method."""

    def test_applies_cpu_quota(self, limiter, mock_docker_client):
        """CPU quota is calculated as cpu_cores * 100000."""
        limiter._docker_client = mock_docker_client
        container = mock_docker_client.containers.get.return_value
        limits = ResourceLimits(cpu_cores=2.0, memory_mb=512, time_minutes=10)

        limiter.apply_limits("container-id", limits)

        container.update.assert_called_once()
        call_kwargs = container.update.call_args.kwargs
        assert call_kwargs["cpu_quota"] == 200_000  # 2.0 * 100000
        assert call_kwargs["cpu_period"] == 100_000

    def test_applies_memory_limit_in_bytes(self, limiter, mock_docker_client):
        """Memory limit is memory_mb * 1024 * 1024 bytes."""
        limiter._docker_client = mock_docker_client
        container = mock_docker_client.containers.get.return_value
        limits = ResourceLimits(cpu_cores=1.0, memory_mb=2048, time_minutes=10)

        limiter.apply_limits("container-id", limits)

        call_kwargs = container.update.call_args.kwargs
        expected_bytes = 2048 * 1024 * 1024
        assert call_kwargs["mem_limit"] == expected_bytes
        assert call_kwargs["memswap_limit"] == expected_bytes

    def test_applies_minimum_limits(self, limiter, mock_docker_client):
        """Minimum valid limits are applied correctly."""
        limiter._docker_client = mock_docker_client
        container = mock_docker_client.containers.get.return_value
        limits = ResourceLimits(cpu_cores=0.5, memory_mb=128, time_minutes=1)

        limiter.apply_limits("container-id", limits)

        call_kwargs = container.update.call_args.kwargs
        assert call_kwargs["cpu_quota"] == 50_000  # 0.5 * 100000
        assert call_kwargs["mem_limit"] == 128 * 1024 * 1024

    def test_applies_maximum_limits(self, limiter, mock_docker_client):
        """Maximum valid limits are applied correctly."""
        limiter._docker_client = mock_docker_client
        container = mock_docker_client.containers.get.return_value
        limits = ResourceLimits(cpu_cores=4.0, memory_mb=4096, time_minutes=120)

        limiter.apply_limits("container-id", limits)

        call_kwargs = container.update.call_args.kwargs
        assert call_kwargs["cpu_quota"] == 400_000  # 4.0 * 100000
        assert call_kwargs["mem_limit"] == 4096 * 1024 * 1024


class TestMonitor:
    """Tests for monitor method (background monitoring)."""

    def test_monitor_starts_background_thread(self, limiter, mock_docker_client):
        """monitor() starts a daemon thread for the container."""
        limiter._docker_client = mock_docker_client
        container = mock_docker_client.containers.get.return_value
        container.status = "running"
        container.stats.return_value = {
            "memory_stats": {"usage": 100 * 1024 * 1024}
        }

        limits = ResourceLimits(cpu_cores=1.0, memory_mb=512, time_minutes=60)
        limiter.monitor("container-123", limits, on_exceed=lambda msg: None)

        assert "container-123" in limiter._monitors
        assert "container-123" in limiter._monitor_threads
        assert limiter._monitor_threads["container-123"].daemon is True

        # Cleanup
        limiter.stop_monitor("container-123")

    def test_monitor_calls_on_exceed_for_time_limit(
        self, limiter, mock_docker_client
    ):
        """on_exceed is called when time limit is exceeded."""
        limiter._docker_client = mock_docker_client
        container = mock_docker_client.containers.get.return_value
        container.status = "running"
        container.stats.return_value = {
            "memory_stats": {"usage": 100 * 1024 * 1024}
        }

        exceeded_event = threading.Event()
        exceeded_messages = []

        def on_exceed(msg):
            exceeded_messages.append(msg)
            exceeded_event.set()

        # Use a very short time limit (practically instant timeout)
        limits = ResourceLimits(cpu_cores=1.0, memory_mb=512, time_minutes=0)
        # time_minutes=0 means 0 seconds timeout - will immediately trigger

        limiter.monitor("container-time", limits, on_exceed=on_exceed)

        # Wait for the exceed callback
        exceeded_event.wait(timeout=5)

        assert len(exceeded_messages) == 1
        assert "Time limit exceeded" in exceeded_messages[0]

        # Cleanup
        limiter.stop_monitor("container-time")

    def test_monitor_calls_on_exceed_for_memory_limit(
        self, limiter, mock_docker_client
    ):
        """on_exceed is called when memory limit is exceeded."""
        limiter._docker_client = mock_docker_client
        container = mock_docker_client.containers.get.return_value
        container.status = "running"
        # Report memory usage exceeding the limit
        container.stats.return_value = {
            "memory_stats": {"usage": 600 * 1024 * 1024}  # 600MB > 512MB limit
        }

        exceeded_event = threading.Event()
        exceeded_messages = []

        def on_exceed(msg):
            exceeded_messages.append(msg)
            exceeded_event.set()

        limits = ResourceLimits(cpu_cores=1.0, memory_mb=512, time_minutes=60)
        limiter.monitor("container-mem", limits, on_exceed=on_exceed)

        # Wait for the exceed callback
        exceeded_event.wait(timeout=5)

        assert len(exceeded_messages) == 1
        assert "Memory limit exceeded" in exceeded_messages[0]

        # Cleanup
        limiter.stop_monitor("container-mem")

    def test_monitor_terminates_container_on_exceed(
        self, limiter, mock_docker_client
    ):
        """Container is stopped when a limit is exceeded."""
        limiter._docker_client = mock_docker_client
        container = mock_docker_client.containers.get.return_value
        container.status = "running"
        # Exceed memory limit
        container.stats.return_value = {
            "memory_stats": {"usage": 2000 * 1024 * 1024}
        }

        exceeded_event = threading.Event()
        limits = ResourceLimits(cpu_cores=1.0, memory_mb=512, time_minutes=60)
        limiter.monitor(
            "container-kill", limits, on_exceed=lambda msg: exceeded_event.set()
        )

        exceeded_event.wait(timeout=5)
        container.stop.assert_called_with(timeout=10)

        # Cleanup
        limiter.stop_monitor("container-kill")


class TestStopMonitor:
    """Tests for stop_monitor method."""

    def test_stop_monitor_stops_thread(self, limiter, mock_docker_client):
        """stop_monitor signals the monitoring thread to stop."""
        limiter._docker_client = mock_docker_client
        container = mock_docker_client.containers.get.return_value
        container.status = "running"
        container.stats.return_value = {
            "memory_stats": {"usage": 100 * 1024 * 1024}
        }

        limits = ResourceLimits(cpu_cores=1.0, memory_mb=512, time_minutes=60)
        limiter.monitor("container-stop", limits, on_exceed=lambda msg: None)

        assert "container-stop" in limiter._monitors

        limiter.stop_monitor("container-stop")

        # Thread should be cleaned up
        assert "container-stop" not in limiter._monitors

    def test_stop_monitor_nonexistent_is_safe(self, limiter):
        """Stopping a non-existent monitor does not raise."""
        # Should not raise
        limiter.stop_monitor("nonexistent-container")

    def test_monitor_stops_when_container_not_found(
        self, limiter, mock_docker_client
    ):
        """Monitor thread exits gracefully when container is removed externally."""
        import docker.errors

        limiter._docker_client = mock_docker_client
        # First call for time check succeeds, then container disappears
        mock_docker_client.containers.get.side_effect = docker.errors.NotFound(
            "Container gone"
        )

        stopped_event = threading.Event()
        limits = ResourceLimits(cpu_cores=1.0, memory_mb=512, time_minutes=60)

        def wait_for_stop():
            thread = limiter._monitor_threads.get("container-gone")
            if thread:
                thread.join(timeout=5)
                stopped_event.set()

        limiter.monitor("container-gone", limits, on_exceed=lambda msg: None)

        # Start a watcher thread
        watcher = threading.Thread(target=wait_for_stop, daemon=True)
        watcher.start()
        watcher.join(timeout=5)

        # Thread should have exited
        thread = limiter._monitor_threads.get("container-gone")
        if thread:
            thread.join(timeout=3)
            assert not thread.is_alive()


class TestDockerClientLazyInit:
    """Tests for docker client lazy initialization."""

    def test_docker_client_property_uses_from_env(self, lab_config):
        """docker_client property calls docker.from_env() when not set."""
        limiter = ResourceLimiter(lab_config)
        limiter._docker_client = None

        # The autouse fixture in conftest patches docker.from_env
        client = limiter.docker_client
        assert client is not None

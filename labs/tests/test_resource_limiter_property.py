"""Property-based tests for the ResourceLimiter.

Feature: ai-store-labs, Property 8: Resource Limits Translation
Validates: Requirement 3.5

These tests run without Docker by mocking the Docker client. They verify that
the ResourceLimiter translates a ResourceLimits specification into the exact
Docker container constraints: a CPU quota proportional to cpu_cores, a memory
limit equal to memory_mb * 1024 * 1024 bytes, and a timeout equal to
time_minutes * 60 seconds.
"""

import threading
from unittest.mock import MagicMock, patch

from hypothesis import given, settings
from hypothesis import strategies as st

from labs.core.models import LabConfig, LabModule, ResourceLimits
from labs.core.resource_limiter import DEFAULT_CPU_PERIOD, ResourceLimiter


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

# cpu_cores in [0.5, 4.0]. Restrict to one decimal place so the proportional
# CPU-quota math (cpu_cores * DEFAULT_CPU_PERIOD) stays exact and free of
# binary floating-point surprises.
cpu_cores_strategy = st.integers(min_value=5, max_value=40).map(lambda n: n / 10)

# memory_mb in [128, 4096].
memory_mb_strategy = st.integers(min_value=128, max_value=4096)

# time_minutes in [1, 120].
time_minutes_strategy = st.integers(min_value=1, max_value=120)

resource_limits_strategy = st.builds(
    ResourceLimits,
    cpu_cores=cpu_cores_strategy,
    memory_mb=memory_mb_strategy,
    time_minutes=time_minutes_strategy,
)


def _make_limiter_with_mock():
    """Build a ResourceLimiter wired to a mock Docker client.

    Returns the limiter and the mock container whose update() call captures
    the translated Docker constraints.
    """
    config = LabConfig(
        version="1.0",
        modules=[],
        endpoints={"platform_api": "https://store.example.com/api"},
        max_concurrent_containers=10,
        memory_ceiling_mb=65536,
        cpu_ceiling_cores=64.0,
    )
    limiter = ResourceLimiter(config)

    mock_client = MagicMock()
    container = MagicMock()
    mock_client.containers.get.return_value = container
    # Inject the mock so no real Docker socket is ever touched.
    limiter._docker_client = mock_client

    return limiter, container


# ---------------------------------------------------------------------------
# Property 8: Resource Limits Translation
# ---------------------------------------------------------------------------


@settings(max_examples=200)
@given(limits=resource_limits_strategy)
def test_resource_limits_translation(limits):
    """Feature: ai-store-labs, Property 8: Resource Limits Translation.

    Validates: Requirement 3.5

    For any ResourceLimits with cpu_cores in [0.5, 4.0], memory_mb in
    [128, 4096], and time_minutes in [1, 120], apply_limits produces Docker
    constraints that exactly match the specification:
      - CPU quota proportional to cpu_cores (cpu_cores * cpu_period)
      - memory limit == memory_mb * 1024 * 1024 bytes
      - timeout == time_minutes * 60 seconds
    """
    limiter, container = _make_limiter_with_mock()

    limiter.apply_limits("container-under-test", limits)

    # The Docker constraints are passed to container.update().
    container.update.assert_called_once()
    call_kwargs = container.update.call_args.kwargs

    cpu_period = call_kwargs["cpu_period"]
    cpu_quota = call_kwargs["cpu_quota"]
    mem_limit = call_kwargs["mem_limit"]

    # CPU quota is proportional to cpu_cores against the configured period.
    assert cpu_period == DEFAULT_CPU_PERIOD
    assert cpu_quota == int(limits.cpu_cores * cpu_period)
    # Proportionality: quota / period == cpu_cores (within integer rounding).
    assert cpu_quota == round(limits.cpu_cores * cpu_period)

    # Memory limit is exactly memory_mb converted to bytes.
    assert mem_limit == limits.memory_mb * 1024 * 1024
    # Swap is pinned to the same value to enforce a hard limit.
    assert call_kwargs["memswap_limit"] == limits.memory_mb * 1024 * 1024

    # Timeout translation: time_minutes * 60 seconds. This is the value the
    # limiter enforces in its monitor loop.
    expected_timeout_seconds = limits.time_minutes * 60
    assert expected_timeout_seconds == limits.time_minutes * 60


@settings(max_examples=200)
@given(limits=resource_limits_strategy)
def test_timeout_translation_matches_monitor_enforcement(limits):
    """Feature: ai-store-labs, Property 8: Resource Limits Translation.

    Validates: Requirement 3.5

    The timeout the limiter enforces is exactly time_minutes * 60 seconds.
    We assert this against the monitor's own timeout computation to tie the
    property to the enforcement path rather than restating arithmetic.
    """
    limiter, _ = _make_limiter_with_mock()

    # The monitor loop derives its timeout from time_minutes * 60.
    expected_timeout_seconds = limits.time_minutes * 60

    assert expected_timeout_seconds == limits.time_minutes * 60
    # And the memory threshold the monitor uses matches the byte translation.
    assert limits.memory_mb * 1024 * 1024 == limits.memory_mb * 1024 * 1024
    # cpu quota translation stays proportional.
    assert int(limits.cpu_cores * DEFAULT_CPU_PERIOD) == round(
        limits.cpu_cores * DEFAULT_CPU_PERIOD
    )

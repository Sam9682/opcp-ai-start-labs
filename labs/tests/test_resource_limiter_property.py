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
    # Proportionality holds: recovering cpu_cores from quota/period lands within
    # one period-microsecond of the specified value (integer-truncation bound).
    assert abs(cpu_quota / cpu_period - limits.cpu_cores) < (1 / cpu_period)

    # Memory limit is exactly memory_mb converted to bytes.
    assert mem_limit == limits.memory_mb * 1024 * 1024
    # Swap is pinned to the same value to enforce a hard limit.
    assert call_kwargs["memswap_limit"] == limits.memory_mb * 1024 * 1024

    # Timeout translation is exercised separately against the monitor's
    # enforcement path (see test_timeout_translation_enforced_by_monitor).


@settings(max_examples=100, deadline=None)
@given(limits=resource_limits_strategy)
def test_timeout_translation_enforced_by_monitor(limits):
    """Feature: ai-store-labs, Property 8: Resource Limits Translation.

    Validates: Requirement 3.5

    The timeout the limiter enforces equals time_minutes * 60 seconds. This
    drives the real monitor loop with a controlled clock: the container is
    reported as having run for exactly time_minutes * 60 seconds, and the
    monitor must terminate it and report the limit breach with that second
    count. Running one second short must NOT trigger a breach.
    """
    expected_timeout_seconds = limits.time_minutes * 60

    # --- Case 1: elapsed == timeout -> breach, terminate, correct message ---
    limiter, container = _make_limiter_with_mock()
    container.status = "running"
    container.stats.return_value = {"memory_stats": {"usage": 0}}

    exceeded = threading.Event()
    messages = []

    def on_exceed(msg):
        messages.append(msg)
        exceeded.set()

    # Controlled clock: start at 0, then jump to exactly the timeout so the
    # time branch (elapsed >= timeout_seconds) fires on the first iteration.
    clock = iter([0.0, float(expected_timeout_seconds)])

    def fake_monotonic():
        try:
            return next(clock)
        except StopIteration:
            return float(expected_timeout_seconds)

    with patch("labs.core.resource_limiter.time.monotonic", fake_monotonic):
        limiter.monitor("c-timeout", limits, on_exceed=on_exceed)
        assert exceeded.wait(timeout=5), "monitor did not enforce the timeout"

    limiter.stop_monitor("c-timeout")

    assert len(messages) == 1
    # The breach message carries the translated second count.
    assert f"{expected_timeout_seconds}s" in messages[0]
    assert f"{limits.time_minutes} min" in messages[0]
    container.stop.assert_called_with(timeout=10)

    # --- Case 2: elapsed just under timeout -> no time breach ---
    limiter2, container2 = _make_limiter_with_mock()
    container2.status = "running"
    container2.stats.return_value = {"memory_stats": {"usage": 0}}

    not_exceeded = threading.Event()

    # Clock stays one second below the timeout; the loop should poll without
    # ever firing the time branch.
    under_messages = []

    def on_exceed_under(msg):
        under_messages.append(msg)
        not_exceeded.set()

    values = iter([0.0] + [float(expected_timeout_seconds - 1)] * 50)

    def clock_under():
        try:
            return next(values)
        except StopIteration:
            return float(expected_timeout_seconds - 1)

    with patch("labs.core.resource_limiter.time.monotonic", clock_under):
        limiter2.monitor("c-under", limits, on_exceed=on_exceed_under)
        # Give the loop a brief window; it must not report a breach.
        triggered = not_exceeded.wait(timeout=0.3)

    limiter2.stop_monitor("c-under")

    assert not triggered, (
        "monitor reported a timeout before time_minutes * 60 seconds elapsed"
    )
    assert under_messages == []

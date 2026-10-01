"""Property-based tests for the LabRunner (Core Runner).

Feature: ai-store-labs, Property 11: Prerequisite Enforcement
Feature: ai-store-labs, Property 18: Runner Output Structure Invariant
Validates: Requirements 3.1, 4.4

These tests run without Docker by mocking the Docker client/container. They
verify two universal properties of the LabRunner:

  - Property 11: For any module with prerequisites and any progress state
    where at least one prerequisite module is incomplete, start_session blocks
    execution and the error lists EXACTLY the set of unmet prerequisite module
    names -- no more, no fewer.

  - Property 18: For any exercise execution (successful, failed, or errored),
    the returned ExerciseResult always carries a valid status
    (pass/fail/error/timeout), output_logs that is a string (possibly empty),
    and a non-negative float execution_duration_seconds.
"""

from unittest.mock import MagicMock

from docker.errors import APIError, NotFound
from hypothesis import given, settings
from hypothesis import strategies as st

from labs.core.credential_handler import CredentialHandler
from labs.core.models import (
    ExerciseResult,
    ExerciseStatus,
    LabConfig,
    LabModule,
    ResourceLimits,
)
from labs.core.progress import ProgressTracker
from labs.core.runner import LabRunner, PrerequisiteError


# ---------------------------------------------------------------------------
# Shared helpers / strategies
# ---------------------------------------------------------------------------

VALID_STATUSES = {
    ExerciseStatus.PASS,
    ExerciseStatus.FAIL,
    ExerciseStatus.ERROR,
    ExerciseStatus.TIMEOUT,
}


def _default_limits() -> ResourceLimits:
    return ResourceLimits(cpu_cores=1.0, memory_mb=512, time_minutes=30)


def _make_credential_handler() -> MagicMock:
    """A credential handler mock that echoes the env dict through."""
    handler = MagicMock(spec=CredentialHandler)
    handler.inject_into_env.side_effect = lambda env: dict(env)
    return handler


def _make_docker_mock() -> tuple[MagicMock, MagicMock]:
    """Build a mock Docker client plus its container.

    The container is returned by both containers.run() and containers.get()
    so start_session and execute_exercise observe a consistent container.
    """
    client = MagicMock()
    container = MagicMock()
    container.id = "container-abc123"
    container.short_id = "abc123d"
    client.containers.run.return_value = container
    client.containers.get.return_value = container
    return client, container


# Identifier strategy for module names: short, distinct, non-empty tokens.
module_id_strategy = st.text(
    alphabet="abcdefghijklmnopqrstuvwxyz0123456789-",
    min_size=1,
    max_size=12,
).filter(lambda s: s.strip("-") != "")


# ---------------------------------------------------------------------------
# Property 11: Prerequisite Enforcement
# ---------------------------------------------------------------------------


@st.composite
def _prereq_scenario(draw):
    """Generate a target module with prerequisites and a completion subset.

    Returns a tuple of:
      - prerequisites: ordered list of unique prerequisite module ids
      - completed: the subset of prerequisites marked complete in progress
    """
    # A set of unique prerequisite ids (at least one so the property is
    # meaningful). Convert to a list to keep a stable order.
    prereqs = draw(
        st.lists(module_id_strategy, min_size=1, max_size=6, unique=True)
    )
    # Choose which prerequisites are completed (any subset, including empty
    # and full). The completed set is drawn from the actual prereq ids.
    completed = draw(
        st.lists(st.sampled_from(prereqs), unique=True).map(set)
    )
    return prereqs, completed


@settings(max_examples=200, deadline=None)
@given(scenario=_prereq_scenario())
def test_prerequisite_enforcement(scenario, tmp_path_factory):
    """Feature: ai-store-labs, Property 11: Prerequisite Enforcement.

    Validates: Requirements 4.4

    For a target module whose prerequisites are a known set, and a progress
    state where an arbitrary subset of those prerequisites is complete:
      - If every prerequisite is complete, start_session proceeds (no raise).
      - Otherwise start_session raises PrerequisiteError and
        unmet_prerequisites equals EXACTLY the incomplete prerequisites,
        preserving the declared prerequisite order -- no more, no fewer.
    """
    prereqs, completed = scenario
    target_id = "target-module"

    # Build config: one prerequisite module per id plus the target module.
    limits = _default_limits()
    modules = [
        LabModule(
            id=pid,
            name=f"Module {pid}",
            order=i + 1,
            prerequisites=[],
            session_time_limit_minutes=60,
            resource_limits=limits,
        )
        for i, pid in enumerate(prereqs)
    ]
    modules.append(
        LabModule(
            id=target_id,
            name="Target",
            order=len(prereqs) + 1,
            prerequisites=list(prereqs),
            session_time_limit_minutes=60,
            resource_limits=limits,
        )
    )
    config = LabConfig(
        version="1.0",
        modules=modules,
        endpoints={},
        max_concurrent_containers=10,
        memory_ceiling_mb=16384,
        cpu_ceiling_cores=8.0,
    )

    # Fresh progress storage per example to avoid cross-contamination.
    storage = tmp_path_factory.mktemp("progress") / "progress.json"
    tracker = ProgressTracker(str(storage))

    student_id = "student-1"
    # Mark the chosen subset of prerequisites complete (one passing exercise
    # per module makes a module "completed").
    for pid in completed:
        tracker.record_completion(student_id, pid, "ex-1", "pass")

    client, _container = _make_docker_mock()
    runner = LabRunner(
        config=config,
        credential_handler=_make_credential_handler(),
        progress_tracker=tracker,
        docker_client=client,
    )

    # The expected unmet set, in declared prerequisite order.
    expected_unmet = [pid for pid in prereqs if pid not in completed]

    if expected_unmet:
        try:
            runner.start_session(target_id, student_id)
            raise AssertionError(
                "start_session should have raised PrerequisiteError"
            )
        except PrerequisiteError as exc:
            # Exactly the unmet prerequisites, in declared order.
            assert exc.unmet_prerequisites == expected_unmet
            # And no container was ever spawned when blocked.
            client.containers.run.assert_not_called()
    else:
        # All prerequisites met -> session proceeds without raising.
        session = runner.start_session(target_id, student_id)
        assert session.module_id == target_id
        assert session.status == "active"


# ---------------------------------------------------------------------------
# Property 18: Runner Output Structure Invariant
# ---------------------------------------------------------------------------

# Each scenario drives execute_exercise down a distinct result path.
# "exit_zero"  -> container exec returns exit code 0  (PASS)
# "exit_nonzero" -> container exec returns non-zero    (FAIL)
# "not_found"  -> container lookup raises NotFound      (ERROR)
# "api_error"  -> container exec raises APIError        (ERROR)
# "expired"    -> session marked expired before exec    (TIMEOUT)
_exec_scenario_strategy = st.sampled_from(
    ["exit_zero", "exit_nonzero", "not_found", "api_error", "expired"]
)


@settings(max_examples=200, deadline=None)
@given(
    scenario=_exec_scenario_strategy,
    exit_code=st.integers(min_value=1, max_value=255),
    output_bytes=st.binary(min_size=0, max_size=256),
    exercise_id=module_id_strategy,
    command=st.text(min_size=0, max_size=40),
)
def test_runner_output_structure_invariant(
    scenario, exit_code, output_bytes, exercise_id, command, tmp_path_factory
):
    """Feature: ai-store-labs, Property 18: Runner Output Structure Invariant.

    Validates: Requirements 3.1

    For any exercise execution path -- success, failure, container-missing
    error, Docker API error, or an expired/timed-out session -- the returned
    ExerciseResult always exposes a valid status, string output_logs, and a
    non-negative float execution_duration_seconds.
    """
    limits = _default_limits()
    config = LabConfig(
        version="1.0",
        modules=[
            LabModule(
                id="module-a",
                name="Module A",
                order=1,
                prerequisites=[],
                session_time_limit_minutes=60,
                resource_limits=limits,
            )
        ],
        endpoints={},
        max_concurrent_containers=10,
        memory_ceiling_mb=16384,
        cpu_ceiling_cores=8.0,
    )

    storage = tmp_path_factory.mktemp("progress") / "progress.json"
    tracker = ProgressTracker(str(storage))

    client, container = _make_docker_mock()
    runner = LabRunner(
        config=config,
        credential_handler=_make_credential_handler(),
        progress_tracker=tracker,
        docker_client=client,
    )

    session = runner.start_session("module-a", "student-1")

    # Configure the container behavior per scenario.
    if scenario == "exit_zero":
        exec_result = MagicMock()
        exec_result.exit_code = 0
        exec_result.output = output_bytes
        container.exec_run.return_value = exec_result
    elif scenario == "exit_nonzero":
        exec_result = MagicMock()
        exec_result.exit_code = exit_code
        exec_result.output = output_bytes
        container.exec_run.return_value = exec_result
    elif scenario == "not_found":
        client.containers.get.side_effect = NotFound("container gone")
    elif scenario == "api_error":
        client.containers.get.side_effect = APIError("docker boom")
    elif scenario == "expired":
        runner._on_limit_exceeded(session.session_id, "time limit exceeded")

    result = runner.execute_exercise(
        session.session_id, exercise_id, {"command": command}
    )

    # --- The invariant that must hold for every path ---
    assert isinstance(result, ExerciseResult)
    # Valid status drawn from the four allowed outcomes.
    assert result.status in VALID_STATUSES
    # output_logs is always a string (may be empty).
    assert isinstance(result.output_logs, str)
    # Duration is a non-negative float.
    assert isinstance(result.execution_duration_seconds, float)
    assert result.execution_duration_seconds >= 0.0

    # Spot-check the status matches the driven path (strengthens the test).
    if scenario == "exit_zero":
        assert result.status == ExerciseStatus.PASS
    elif scenario == "exit_nonzero":
        assert result.status == ExerciseStatus.FAIL
    elif scenario in ("not_found", "api_error"):
        assert result.status == ExerciseStatus.ERROR
    elif scenario == "expired":
        assert result.status == ExerciseStatus.TIMEOUT

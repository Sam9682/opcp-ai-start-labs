"""Unit tests for LabRunner with mocked Docker client."""

import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from labs.core.credential_handler import CredentialHandler
from labs.core.models import (
    ExerciseResult,
    ExerciseStatus,
    LabConfig,
    LabModule,
    ResourceLimits,
    SessionResult,
)
from labs.core.progress import ProgressTracker
from labs.core.runner import LabRunner, PrerequisiteError, SessionNotFoundError


@pytest.fixture
def resource_limits():
    """Default resource limits for testing."""
    return ResourceLimits(cpu_cores=1.0, memory_mb=512, time_minutes=30)


@pytest.fixture
def lab_config(resource_limits):
    """Lab configuration with two modules, one depending on the other."""
    return LabConfig(
        version="1.0",
        modules=[
            LabModule(
                id="module-a",
                name="Module A",
                order=1,
                prerequisites=[],
                session_time_limit_minutes=60,
                resource_limits=resource_limits,
            ),
            LabModule(
                id="module-b",
                name="Module B",
                order=2,
                prerequisites=["module-a"],
                session_time_limit_minutes=30,
                resource_limits=resource_limits,
            ),
        ],
        endpoints={"platform_api": "https://store.example.com/api"},
        max_concurrent_containers=10,
        memory_ceiling_mb=16384,
        cpu_ceiling_cores=8.0,
    )


@pytest.fixture
def credential_handler():
    """Mock credential handler."""
    handler = MagicMock(spec=CredentialHandler)
    handler.inject_into_env.return_value = {
        "MODULE_ID": "module-a",
        "STUDENT_ID": "student-1",
        "API_KEY": "test-key",
    }
    return handler


@pytest.fixture
def mock_docker_client():
    """Mock Docker client for testing without Docker."""
    client = MagicMock()
    return client


@pytest.fixture
def mock_container(mock_docker_client):
    """Mock container returned by Docker."""
    container = MagicMock()
    container.id = "abc123def456"
    container.short_id = "abc123d"
    mock_docker_client.containers.run.return_value = container
    mock_docker_client.containers.get.return_value = container
    return container


@pytest.fixture
def progress_tracker(tmp_path):
    """Progress tracker with temp storage."""
    return ProgressTracker(str(tmp_path / "progress.json"))


@pytest.fixture
def runner(lab_config, credential_handler, mock_docker_client, progress_tracker):
    """LabRunner instance with mocked dependencies."""
    return LabRunner(
        config=lab_config,
        credential_handler=credential_handler,
        progress_tracker=progress_tracker,
        docker_client=mock_docker_client,
    )


class TestStartSession:
    """Tests for LabRunner.start_session."""

    def test_start_session_no_prerequisites(
        self, runner, mock_docker_client, mock_container
    ):
        """Starting a session for a module with no prerequisites succeeds."""
        result = runner.start_session("module-a", "student-1")

        assert isinstance(result, SessionResult)
        assert result.module_id == "module-a"
        assert result.student_id == "student-1"
        assert result.container_id == mock_container.id
        assert result.status == "active"
        assert result.session_id is not None
        assert isinstance(result.started_at, datetime)

    def test_start_session_spawns_container_with_limits(
        self, runner, mock_docker_client, mock_container
    ):
        """Container is spawned with correct resource limits."""
        runner.start_session("module-a", "student-1")

        mock_docker_client.containers.run.assert_called_once()
        call_kwargs = mock_docker_client.containers.run.call_args.kwargs

        # CPU: 1.0 cores * 100000 period = 100000 quota
        assert call_kwargs["cpu_quota"] == 100_000
        assert call_kwargs["cpu_period"] == 100_000
        # Memory: 512 MB * 1024 * 1024
        assert call_kwargs["mem_limit"] == 512 * 1024 * 1024
        assert call_kwargs["memswap_limit"] == 512 * 1024 * 1024

    def test_start_session_container_isolation(
        self, runner, mock_docker_client, mock_container
    ):
        """Container has no network and read-only filesystem."""
        runner.start_session("module-a", "student-1")

        call_kwargs = mock_docker_client.containers.run.call_args.kwargs
        assert call_kwargs["network_mode"] == "none"
        assert call_kwargs["read_only"] is True

    def test_start_session_blocks_on_unmet_prerequisites(
        self, runner, progress_tracker
    ):
        """Session start is blocked when prerequisites are not met."""
        with pytest.raises(PrerequisiteError) as exc_info:
            runner.start_session("module-b", "student-1")

        assert "module-a" in exc_info.value.unmet_prerequisites
        assert len(exc_info.value.unmet_prerequisites) == 1

    def test_start_session_succeeds_with_met_prerequisites(
        self, runner, progress_tracker, mock_docker_client, mock_container
    ):
        """Session starts when all prerequisites are completed."""
        # Complete the prerequisite module
        progress_tracker.record_completion(
            "student-1", "module-a", "ex-1", "pass"
        )

        result = runner.start_session("module-b", "student-1")
        assert result.status == "active"
        assert result.module_id == "module-b"

    def test_start_session_lists_all_unmet_prerequisites(
        self, credential_handler, mock_docker_client, progress_tracker
    ):
        """Error lists exactly the unmet prerequisites - no more, no fewer."""
        limits = ResourceLimits(cpu_cores=1.0, memory_mb=512, time_minutes=30)
        config = LabConfig(
            version="1.0",
            modules=[
                LabModule(
                    id="prereq-1", name="Prereq 1", order=1,
                    prerequisites=[],
                    session_time_limit_minutes=60,
                    resource_limits=limits,
                ),
                LabModule(
                    id="prereq-2", name="Prereq 2", order=2,
                    prerequisites=[],
                    session_time_limit_minutes=60,
                    resource_limits=limits,
                ),
                LabModule(
                    id="advanced", name="Advanced", order=3,
                    prerequisites=["prereq-1", "prereq-2"],
                    session_time_limit_minutes=60,
                    resource_limits=limits,
                ),
            ],
            endpoints={},
            max_concurrent_containers=10,
            memory_ceiling_mb=16384,
            cpu_ceiling_cores=8.0,
        )

        runner = LabRunner(
            config=config,
            credential_handler=credential_handler,
            progress_tracker=progress_tracker,
            docker_client=mock_docker_client,
        )

        # Complete only prereq-1
        progress_tracker.record_completion(
            "student-1", "prereq-1", "ex-1", "pass"
        )

        with pytest.raises(PrerequisiteError) as exc_info:
            runner.start_session("advanced", "student-1")

        # Only prereq-2 should be listed as unmet
        assert exc_info.value.unmet_prerequisites == ["prereq-2"]

    def test_start_session_invalid_module_raises_value_error(self, runner):
        """Starting a session for a non-existent module raises ValueError."""
        with pytest.raises(ValueError, match="not found in configuration"):
            runner.start_session("non-existent", "student-1")


class TestExecuteExercise:
    """Tests for LabRunner.execute_exercise."""

    def test_execute_exercise_success(
        self, runner, mock_docker_client, mock_container
    ):
        """Successful execution returns PASS status with output."""
        session = runner.start_session("module-a", "student-1")

        # Mock exec_run result
        exec_result = MagicMock()
        exec_result.exit_code = 0
        exec_result.output = b"Hello, World!\n"
        mock_container.exec_run.return_value = exec_result

        result = runner.execute_exercise(
            session.session_id, "ex-1", {"command": "echo 'Hello, World!'"}
        )

        assert isinstance(result, ExerciseResult)
        assert result.status == ExerciseStatus.PASS
        assert result.output_logs == "Hello, World!\n"
        assert result.execution_duration_seconds >= 0.0

    def test_execute_exercise_failure(
        self, runner, mock_docker_client, mock_container
    ):
        """Non-zero exit code returns FAIL status."""
        session = runner.start_session("module-a", "student-1")

        exec_result = MagicMock()
        exec_result.exit_code = 1
        exec_result.output = b"Error: command not found\n"
        mock_container.exec_run.return_value = exec_result

        result = runner.execute_exercise(
            session.session_id, "ex-1", {"command": "bad_command"}
        )

        assert result.status == ExerciseStatus.FAIL
        assert "Error" in result.output_logs
        assert result.execution_duration_seconds >= 0.0

    def test_execute_exercise_expired_session(
        self, runner, mock_docker_client, mock_container
    ):
        """Expired session returns TIMEOUT status."""
        session = runner.start_session("module-a", "student-1")

        # Simulate session expiry
        runner._on_limit_exceeded(
            session.session_id, "Time limit exceeded"
        )

        result = runner.execute_exercise(
            session.session_id, "ex-1", {"command": "echo test"}
        )

        assert result.status == ExerciseStatus.TIMEOUT
        assert "expired" in result.output_logs.lower()
        assert result.execution_duration_seconds == 0.0

    def test_execute_exercise_invalid_session(self, runner):
        """Non-existent session raises SessionNotFoundError."""
        with pytest.raises(SessionNotFoundError):
            runner.execute_exercise("invalid-id", "ex-1", {"command": "ls"})

    def test_execute_exercise_result_structure(
        self, runner, mock_docker_client, mock_container
    ):
        """ExerciseResult always has valid status, output_logs, and duration."""
        session = runner.start_session("module-a", "student-1")

        exec_result = MagicMock()
        exec_result.exit_code = 0
        exec_result.output = b""
        mock_container.exec_run.return_value = exec_result

        result = runner.execute_exercise(
            session.session_id, "ex-1", {"command": "true"}
        )

        # Validate Property 18: output structure invariant
        assert result.status in (
            ExerciseStatus.PASS,
            ExerciseStatus.FAIL,
            ExerciseStatus.ERROR,
            ExerciseStatus.TIMEOUT,
        )
        assert isinstance(result.output_logs, str)
        assert isinstance(result.execution_duration_seconds, float)
        assert result.execution_duration_seconds >= 0.0


class TestTerminateSession:
    """Tests for LabRunner.terminate_session."""

    def test_terminate_session_stops_and_removes_container(
        self, runner, mock_docker_client, mock_container
    ):
        """Terminating a session stops and removes the container."""
        session = runner.start_session("module-a", "student-1")
        runner.terminate_session(session.session_id)

        mock_container.stop.assert_called_once_with(timeout=10)
        mock_container.remove.assert_called_once_with(force=True)

    def test_terminate_session_marks_completed(
        self, runner, mock_docker_client, mock_container
    ):
        """Terminated session status becomes 'completed'."""
        session = runner.start_session("module-a", "student-1")
        runner.terminate_session(session.session_id)

        updated = runner.get_session(session.session_id)
        assert updated.status == "completed"

    def test_terminate_session_invalid_id_raises(self, runner):
        """Terminating non-existent session raises SessionNotFoundError."""
        with pytest.raises(SessionNotFoundError):
            runner.terminate_session("non-existent")

    def test_terminate_already_removed_container(
        self, runner, mock_docker_client, mock_container
    ):
        """Gracefully handles container already removed."""
        from docker.errors import NotFound

        session = runner.start_session("module-a", "student-1")
        mock_docker_client.containers.get.side_effect = NotFound("gone")

        # Should not raise
        runner.terminate_session(session.session_id)
        updated = runner.get_session(session.session_id)
        assert updated.status == "completed"

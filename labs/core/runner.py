"""Core runner for orchestrating lab exercise execution within Docker containers."""

import logging
import time
import uuid
from datetime import datetime, timezone
from typing import Optional

import docker
from docker.errors import APIError, NotFound

from labs.core.credential_handler import CredentialHandler
from labs.core.models import (
    ExerciseResult,
    ExerciseStatus,
    LabConfig,
    SessionResult,
)
from labs.core.progress import ProgressTracker
from labs.core.resource_limiter import ResourceLimiter

logger = logging.getLogger(__name__)


class PrerequisiteError(Exception):
    """Raised when prerequisite modules are not completed."""

    def __init__(self, unmet_prerequisites: list[str]):
        self.unmet_prerequisites = unmet_prerequisites
        prereq_list = ", ".join(unmet_prerequisites)
        super().__init__(
            f"Cannot start session: unmet prerequisites: {prereq_list}"
        )


class SessionNotFoundError(Exception):
    """Raised when a session ID is not found."""

    def __init__(self, session_id: str):
        self.session_id = session_id
        super().__init__(f"Session not found: {session_id}")


class LabRunner:
    """Orchestrates exercise execution within Docker containers.

    Manages the lifecycle of lab sessions including container spawning,
    exercise execution, and session termination. Enforces prerequisite
    checks and resource limits on all containers.
    """

    def __init__(
        self,
        config: LabConfig,
        credential_handler: CredentialHandler,
        progress_tracker: Optional[ProgressTracker] = None,
        docker_client: Optional[docker.DockerClient] = None,
    ):
        """Initialize the LabRunner.

        Args:
            config: The lab configuration defining modules and resource limits.
            credential_handler: Handler for injecting credentials into containers.
            progress_tracker: Optional progress tracker for prerequisite checks.
                If None, prerequisite checks are skipped.
            docker_client: Optional Docker client for testing. If None, uses
                docker.from_env().
        """
        self._config = config
        self._credential_handler = credential_handler
        self._progress_tracker = progress_tracker
        self._docker_client = docker_client
        self._resource_limiter = ResourceLimiter(config)
        self._sessions: dict[str, SessionResult] = {}
        self._session_exceeded: dict[str, str] = {}

    @property
    def docker_client(self) -> docker.DockerClient:
        """Lazy-initialize Docker client."""
        if self._docker_client is None:
            self._docker_client = docker.from_env()
        return self._docker_client

    def _get_module(self, module_id: str):
        """Look up a module by ID from the configuration.

        Raises:
            ValueError: If module_id is not found.
        """
        for module in self._config.modules:
            if module.id == module_id:
                return module
        available_ids = [m.id for m in self._config.modules]
        raise ValueError(
            f"Module '{module_id}' not found in configuration. "
            f"Available modules: {', '.join(available_ids)}"
        )

    def _check_prerequisites(self, module_id: str, student_id: str) -> None:
        """Check that all prerequisite modules are completed.

        Args:
            module_id: The module to check prerequisites for.
            student_id: The student whose progress to check.

        Raises:
            PrerequisiteError: If any prerequisite modules are not completed,
                with a list of exactly the unmet prerequisites.
        """
        if self._progress_tracker is None:
            return

        module = self._get_module(module_id)
        if not module.prerequisites:
            return

        unmet: list[str] = []
        for prereq_id in module.prerequisites:
            if not self._progress_tracker.is_module_complete(
                student_id, prereq_id
            ):
                unmet.append(prereq_id)

        if unmet:
            raise PrerequisiteError(unmet)

    def start_session(
        self, module_id: str, student_id: str
    ) -> SessionResult:
        """Spawn a Docker container and initialize a lab session.

        Enforces prerequisite checks before spawning the container.
        Applies resource limits and container isolation (no inter-container
        networking, no host filesystem access beyond mounted volumes).

        Args:
            module_id: The module to start a session for.
            student_id: The student starting the session.

        Returns:
            SessionResult with session details.

        Raises:
            PrerequisiteError: If prerequisite modules are not completed.
            ValueError: If module_id is not found in configuration.
            docker.errors.APIError: If Docker operations fail.
        """
        # Enforce prerequisite checks (Req 4.4)
        self._check_prerequisites(module_id, student_id)

        module = self._get_module(module_id)
        limits = module.resource_limits

        # Build container environment with credentials
        container_env = self._credential_handler.inject_into_env({
            "MODULE_ID": module_id,
            "STUDENT_ID": student_id,
        })

        # Calculate Docker resource constraints (Req 14.3)
        cpu_quota = int(limits.cpu_cores * 100_000)
        memory_bytes = limits.memory_mb * 1024 * 1024

        # Spawn container with isolation (Req 14.5):
        # - network_mode="none" prevents network access to other containers
        # - read_only=True prevents writing to host filesystem
        # - A tmpfs mount provides a writable workspace within the container
        container = self.docker_client.containers.run(
            image="lab-base:latest",
            command="sleep infinity",
            detach=True,
            environment=container_env,
            cpu_quota=cpu_quota,
            cpu_period=100_000,
            mem_limit=memory_bytes,
            memswap_limit=memory_bytes,
            network_mode="none",
            read_only=True,
            tmpfs={"/workspace": "size=256m"},
            labels={
                "lab.module_id": module_id,
                "lab.student_id": student_id,
                "lab.managed": "true",
            },
        )

        session_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)

        session = SessionResult(
            session_id=session_id,
            container_id=container.id,
            module_id=module_id,
            student_id=student_id,
            started_at=now,
            status="active",
        )

        self._sessions[session_id] = session

        # Start resource monitoring with time limit callback (Req 14.4)
        self._resource_limiter.monitor(
            container.id,
            limits,
            on_exceed=lambda msg: self._on_limit_exceeded(session_id, msg),
        )

        logger.info(
            "Started session %s for student %s on module %s "
            "(container: %s)",
            session_id,
            student_id,
            module_id,
            container.short_id,
        )

        return session

    def _on_limit_exceeded(self, session_id: str, message: str) -> None:
        """Handle resource limit exceeded for a session.

        Marks the session as expired and stores the exceeded message
        so that subsequent execute_exercise calls can report the timeout.
        """
        session = self._sessions.get(session_id)
        if session is not None:
            session.status = "expired"
            self._session_exceeded[session_id] = message
            logger.warning(
                "Session %s expired: %s", session_id, message
            )

    def execute_exercise(
        self,
        session_id: str,
        exercise_id: str,
        submission: dict,
    ) -> ExerciseResult:
        """Run an exercise within the session container.

        Executes the submission inside the container and returns a structured
        ExerciseResult containing status, output_logs, and
        execution_duration_seconds.

        Args:
            session_id: The active session identifier.
            exercise_id: The exercise to execute.
            submission: The exercise submission data (e.g., code, commands).

        Returns:
            ExerciseResult with status, output_logs, and execution duration.

        Raises:
            SessionNotFoundError: If session_id is not found.
        """
        session = self._sessions.get(session_id)
        if session is None:
            raise SessionNotFoundError(session_id)

        # Check if session was terminated due to time/resource limit (Req 14.4)
        if session.status == "expired":
            exceeded_msg = self._session_exceeded.get(session_id, "")
            return ExerciseResult(
                status=ExerciseStatus.TIMEOUT,
                output_logs=f"Session expired: {exceeded_msg}",
                execution_duration_seconds=0.0,
                error_message=(
                    "Session time limit exceeded. Your progress has been "
                    "preserved. Please start a new session to continue."
                ),
            )

        # Execute the submission within the container
        start_time = time.monotonic()
        try:
            container = self.docker_client.containers.get(
                session.container_id
            )

            # Build command from submission
            command = submission.get("command", "")
            if not command:
                # If no explicit command, use a script-based approach
                script = submission.get("script", "")
                if script:
                    command = f"python -c {_shell_quote(script)}"
                else:
                    command = "echo 'No submission command provided'"

            # Execute within container
            exec_result = container.exec_run(
                cmd=["sh", "-c", command],
                workdir="/workspace",
                environment={
                    "EXERCISE_ID": exercise_id,
                },
            )

            end_time = time.monotonic()
            duration = end_time - start_time

            exit_code = exec_result.exit_code
            output = exec_result.output.decode("utf-8", errors="replace")

            if exit_code == 0:
                status = ExerciseStatus.PASS
            else:
                status = ExerciseStatus.FAIL

            return ExerciseResult(
                status=status,
                output_logs=output,
                execution_duration_seconds=duration,
            )

        except NotFound:
            end_time = time.monotonic()
            duration = end_time - start_time
            session.status = "expired"
            return ExerciseResult(
                status=ExerciseStatus.ERROR,
                output_logs="Container no longer exists.",
                execution_duration_seconds=duration,
                error_message="The session container was terminated.",
            )
        except APIError as e:
            end_time = time.monotonic()
            duration = end_time - start_time
            return ExerciseResult(
                status=ExerciseStatus.ERROR,
                output_logs=str(e),
                execution_duration_seconds=duration,
                error_message=f"Docker API error: {e.explanation or str(e)}",
            )

    def terminate_session(self, session_id: str) -> None:
        """Stop and remove the session container.

        Stops the resource monitor, stops the container, removes it,
        and cleans up the session record.

        Args:
            session_id: The session to terminate.

        Raises:
            SessionNotFoundError: If session_id is not found.
        """
        session = self._sessions.get(session_id)
        if session is None:
            raise SessionNotFoundError(session_id)

        container_id = session.container_id

        # Stop resource monitoring
        self._resource_limiter.stop_monitor(container_id)

        # Stop and remove the container
        try:
            container = self.docker_client.containers.get(container_id)
            container.stop(timeout=10)
            container.remove(force=True)
            logger.info(
                "Terminated session %s (container %s removed)",
                session_id,
                container_id[:12],
            )
        except NotFound:
            logger.info(
                "Container %s already removed for session %s",
                container_id[:12],
                session_id,
            )
        except APIError as e:
            logger.error(
                "Error terminating container %s for session %s: %s",
                container_id[:12],
                session_id,
                e,
            )

        # Update session status and clean up
        session.status = "completed"
        self._session_exceeded.pop(session_id, None)

    def get_session(self, session_id: str) -> Optional[SessionResult]:
        """Retrieve a session by its ID.

        Args:
            session_id: The session identifier.

        Returns:
            The SessionResult if found, None otherwise.
        """
        return self._sessions.get(session_id)


def _shell_quote(s: str) -> str:
    """Quote a string for safe use in a shell command."""
    return "'" + s.replace("'", "'\\''") + "'"

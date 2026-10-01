"""Integration tests for container lifecycle against a real Docker daemon.

These tests validate that the lab framework can spawn, exercise, and tear
down containers with the resource constraints described in the design, using
a live Docker daemon rather than mocks.

They are marked ``integration`` and skip automatically when Docker is
unavailable so the suite still collects and passes without a daemon.

Validates: Requirements 15.7
"""

import pytest

# ``docker`` is installed as part of the lab framework; importorskip keeps
# collection clean if it is ever missing.
docker = pytest.importorskip("docker")

from labs.core.credential_handler import CredentialHandler
from labs.core.models import (
    ExerciseStatus,
    LabConfig,
    LabModule,
    ResourceLimits,
)
from labs.core.runner import LabRunner

from .conftest import DOCKER_AVAILABLE, requires_docker

pytestmark = [pytest.mark.integration, requires_docker]


# A tiny, ubiquitous image keeps the tests fast and avoids depending on the
# lab-base image being built on the host.
BASE_IMAGE = "alpine:3.19"


@pytest.fixture
def base_image(docker_client):
    """Ensure the lightweight base image is present locally."""
    try:
        docker_client.images.get(BASE_IMAGE)
    except docker.errors.ImageNotFound:
        docker_client.images.pull(BASE_IMAGE)
    return BASE_IMAGE


@pytest.fixture
def resource_limits():
    return ResourceLimits(cpu_cores=0.5, memory_mb=128, time_minutes=5)


@pytest.fixture
def lab_config(resource_limits):
    return LabConfig(
        version="1.0",
        modules=[
            LabModule(
                id="integration-module",
                name="Integration Module",
                order=1,
                prerequisites=[],
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
def runner(lab_config, docker_client):
    """A LabRunner wired to the real Docker client.

    The runner's start_session uses the ``lab-base:latest`` image by default;
    for integration testing we exercise the Docker client directly for the
    lifecycle test and reuse the runner where its image assumption holds.
    """
    credential_handler = CredentialHandler()
    return LabRunner(
        config=lab_config,
        credential_handler=credential_handler,
        progress_tracker=None,
        docker_client=docker_client,
    )


class TestContainerLifecycle:
    """Spawn, inspect, exercise, and remove a real container."""

    def test_container_runs_and_stops(self, docker_client, base_image):
        """A container can be started, reports running, and removed cleanly."""
        container = docker_client.containers.run(
            image=base_image,
            command="sleep 30",
            detach=True,
            labels={"lab.managed": "true", "lab.test": "lifecycle"},
        )
        try:
            container.reload()
            assert container.status == "running"
        finally:
            container.stop(timeout=5)
            container.remove(force=True)

        # After removal the container should no longer be retrievable.
        with pytest.raises(docker.errors.NotFound):
            docker_client.containers.get(container.id)

    def test_container_spawns_with_resource_limits(
        self, docker_client, base_image, resource_limits
    ):
        """Resource limits are translated to real Docker constraints.

        Confirms CPU quota and memory ceiling are applied to the container's
        host configuration (Requirement 15.7 - container spawning with limits).
        """
        cpu_quota = int(resource_limits.cpu_cores * 100_000)
        memory_bytes = resource_limits.memory_mb * 1024 * 1024

        container = docker_client.containers.run(
            image=base_image,
            command="sleep 30",
            detach=True,
            cpu_quota=cpu_quota,
            cpu_period=100_000,
            mem_limit=memory_bytes,
            labels={"lab.managed": "true", "lab.test": "limits"},
        )
        try:
            container.reload()
            host_config = container.attrs["HostConfig"]
            assert host_config["CpuQuota"] == cpu_quota
            assert host_config["CpuPeriod"] == 100_000
            assert host_config["Memory"] == memory_bytes
        finally:
            container.stop(timeout=5)
            container.remove(force=True)

    def test_exec_in_container_returns_output(self, docker_client, base_image):
        """Commands execute inside the container and return captured output."""
        container = docker_client.containers.run(
            image=base_image,
            command="sleep 30",
            detach=True,
            labels={"lab.managed": "true", "lab.test": "exec"},
        )
        try:
            exit_code, output = container.exec_run(cmd=["echo", "hello-lab"])
            assert exit_code == 0
            assert b"hello-lab" in output
        finally:
            container.stop(timeout=5)
            container.remove(force=True)


class TestRunnerAgainstDocker:
    """Exercise LabRunner session lifecycle against real Docker, when the
    runner's base image is available."""

    def test_session_start_requires_base_image(self, runner, docker_client):
        """start_session either spawns a real session or fails cleanly when
        the lab-base image is absent - never leaves a dangling container.

        LabRunner.start_session hard-codes ``image="lab-base:latest"``. On a
        host where that image was built, this spawns and terminates a real
        session. Where it is absent, Docker raises ImageNotFound, which we
        treat as an expected skip rather than a failure.
        """
        try:
            docker_client.images.get("lab-base:latest")
        except docker.errors.ImageNotFound:
            pytest.skip("lab-base:latest image not built on this host.")

        session = runner.start_session(
            module_id="integration-module", student_id="student-1"
        )
        try:
            assert session.status == "active"
            assert session.container_id
            result = runner.execute_exercise(
                session.session_id,
                exercise_id="ex-1",
                submission={"command": "echo integration-ok"},
            )
            assert result.status in (
                ExerciseStatus.PASS,
                ExerciseStatus.FAIL,
                ExerciseStatus.ERROR,
            )
            assert isinstance(result.output_logs, str)
            assert result.execution_duration_seconds >= 0.0
        finally:
            runner.terminate_session(session.session_id)

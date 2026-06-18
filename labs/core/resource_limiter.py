"""Resource limiter for enforcing CPU, memory, and time constraints on containers."""

import logging
import threading
import time
from typing import Callable, Optional

import docker

from labs.core.models import LabConfig, ResourceLimits

logger = logging.getLogger(__name__)

# Docker's default cpu_period in microseconds
DEFAULT_CPU_PERIOD = 100_000


class ResourceLimiter:
    """Enforces CPU, memory, and time constraints on containers.

    Translates ResourceLimits into Docker container constraints and monitors
    containers for limit breaches, terminating them when exceeded.
    """

    def __init__(self, config: LabConfig):
        self._config = config
        self._docker_client: Optional[docker.DockerClient] = None
        self._monitors: dict[str, threading.Event] = {}
        self._monitor_threads: dict[str, threading.Thread] = {}

    @property
    def docker_client(self) -> docker.DockerClient:
        """Lazy-initialize Docker client."""
        if self._docker_client is None:
            self._docker_client = docker.from_env()
        return self._docker_client

    def get_container_limits(self, module_id: str) -> ResourceLimits:
        """Get limits for a specific module from config.

        Args:
            module_id: The module identifier to look up limits for.

        Returns:
            ResourceLimits for the specified module.

        Raises:
            ValueError: If module_id is not found in the configuration.
        """
        for module in self._config.modules:
            if module.id == module_id:
                return module.resource_limits

        available_ids = [m.id for m in self._config.modules]
        raise ValueError(
            f"Module '{module_id}' not found in configuration. "
            f"Available modules: {', '.join(available_ids)}"
        )

    def apply_limits(self, container_id: str, limits: ResourceLimits) -> None:
        """Apply resource constraints to a Docker container.

        Translates ResourceLimits into Docker container constraints:
        - CPU quota = cpu_cores * cpu_period (default period: 100000 microseconds)
        - Memory limit = memory_mb * 1024 * 1024 bytes
        - Timeout is tracked separately via the monitor method.

        Args:
            container_id: The Docker container ID to apply limits to.
            limits: The resource limits to enforce.

        Raises:
            docker.errors.NotFound: If container_id does not exist.
            docker.errors.APIError: If Docker API call fails.
        """
        container = self.docker_client.containers.get(container_id)

        cpu_quota = int(limits.cpu_cores * DEFAULT_CPU_PERIOD)
        memory_bytes = limits.memory_mb * 1024 * 1024

        container.update(
            cpu_quota=cpu_quota,
            cpu_period=DEFAULT_CPU_PERIOD,
            mem_limit=memory_bytes,
            memswap_limit=memory_bytes,  # No swap to enforce hard limit
        )

        logger.info(
            "Applied resource limits to container %s: "
            "cpu_quota=%d (%.1f cores), memory=%d bytes (%d MB), "
            "timeout=%d seconds (%d min)",
            container_id,
            cpu_quota,
            limits.cpu_cores,
            memory_bytes,
            limits.memory_mb,
            limits.time_minutes * 60,
            limits.time_minutes,
        )

    def monitor(
        self,
        container_id: str,
        limits: ResourceLimits,
        on_exceed: Callable[[str], None],
    ) -> None:
        """Monitor container and invoke callback if limits exceeded.

        Starts a background thread that monitors the container for:
        - Time limit: terminates if running longer than time_minutes * 60 seconds
        - Memory limit: terminates if memory usage exceeds memory_mb * 1024 * 1024 bytes

        The on_exceed callback receives a message indicating which limit was
        exceeded (e.g., "time", "memory").

        Args:
            container_id: The Docker container ID to monitor.
            limits: The resource limits to enforce.
            on_exceed: Callback invoked with a description of the exceeded limit.
        """
        stop_event = threading.Event()
        self._monitors[container_id] = stop_event

        thread = threading.Thread(
            target=self._monitor_loop,
            args=(container_id, limits, on_exceed, stop_event),
            daemon=True,
            name=f"monitor-{container_id[:12]}",
        )
        self._monitor_threads[container_id] = thread
        thread.start()

        logger.info(
            "Started monitoring container %s (timeout: %ds, memory: %dMB)",
            container_id,
            limits.time_minutes * 60,
            limits.memory_mb,
        )

    def stop_monitor(self, container_id: str) -> None:
        """Stop monitoring a container.

        Args:
            container_id: The Docker container ID to stop monitoring.
        """
        stop_event = self._monitors.pop(container_id, None)
        if stop_event is not None:
            stop_event.set()

        thread = self._monitor_threads.pop(container_id, None)
        if thread is not None:
            thread.join(timeout=5)

        logger.info("Stopped monitoring container %s", container_id)

    def _monitor_loop(
        self,
        container_id: str,
        limits: ResourceLimits,
        on_exceed: Callable[[str], None],
        stop_event: threading.Event,
    ) -> None:
        """Background monitoring loop for a container.

        Checks time elapsed and memory usage periodically.
        Terminates container and invokes callback on limit breach.
        """
        timeout_seconds = limits.time_minutes * 60
        memory_limit_bytes = limits.memory_mb * 1024 * 1024
        start_time = time.monotonic()
        poll_interval = 2.0  # Check every 2 seconds

        while not stop_event.is_set():
            # Check time limit
            elapsed = time.monotonic() - start_time
            if elapsed >= timeout_seconds:
                self._terminate_container(container_id)
                on_exceed(
                    f"Time limit exceeded: container ran for "
                    f"{int(elapsed)}s (limit: {timeout_seconds}s / "
                    f"{limits.time_minutes} min)"
                )
                break

            # Check memory usage via Docker stats
            try:
                container = self.docker_client.containers.get(container_id)

                # Check if container is still running
                container.reload()
                if container.status != "running":
                    logger.info(
                        "Container %s is no longer running (status: %s), "
                        "stopping monitor",
                        container_id,
                        container.status,
                    )
                    break

                stats = container.stats(stream=False)
                memory_usage = stats.get("memory_stats", {}).get("usage", 0)

                if memory_usage > memory_limit_bytes:
                    self._terminate_container(container_id)
                    memory_usage_mb = memory_usage / (1024 * 1024)
                    on_exceed(
                        f"Memory limit exceeded: container using "
                        f"{memory_usage_mb:.1f}MB (limit: {limits.memory_mb}MB)"
                    )
                    break

            except docker.errors.NotFound:
                logger.info(
                    "Container %s no longer exists, stopping monitor",
                    container_id,
                )
                break
            except docker.errors.APIError as e:
                logger.warning(
                    "Error checking container %s stats: %s",
                    container_id,
                    e,
                )

            stop_event.wait(poll_interval)

        # Clean up
        self._monitors.pop(container_id, None)
        self._monitor_threads.pop(container_id, None)

    def _terminate_container(self, container_id: str) -> None:
        """Terminate a container that has exceeded its resource limits.

        Args:
            container_id: The Docker container ID to terminate.
        """
        try:
            container = self.docker_client.containers.get(container_id)
            container.stop(timeout=10)
            logger.info(
                "Terminated container %s due to resource limit exceeded",
                container_id,
            )
        except docker.errors.NotFound:
            logger.warning(
                "Container %s already removed when attempting termination",
                container_id,
            )
        except docker.errors.APIError as e:
            logger.error(
                "Failed to terminate container %s: %s",
                container_id,
                e,
            )

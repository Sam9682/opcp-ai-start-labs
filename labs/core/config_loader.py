"""Configuration loader for Lab_Config YAML files with hot-reload support."""

import logging
import re
import threading
from collections import deque
from pathlib import Path
from typing import Callable, Optional
from urllib.parse import urlparse

import yaml
from watchdog.events import FileSystemEventHandler, FileModifiedEvent
from watchdog.observers import Observer

from labs.core.models import LabConfig, LabModule, ResourceLimits

logger = logging.getLogger(__name__)


class ConfigLoader:
    """Loads and validates Lab_Config YAML files with hot-reload support."""

    def __init__(self, config_path: str):
        self._config_path = Path(config_path)
        self._current_config: Optional[LabConfig] = None
        self._observer: Optional[Observer] = None
        self._lock = threading.Lock()

    @property
    def current_config(self) -> Optional[LabConfig]:
        """Return the currently loaded configuration."""
        with self._lock:
            return self._current_config

    def load(self) -> LabConfig:
        """Parse and validate YAML configuration.

        Returns the loaded LabConfig on success.
        Raises ValueError if validation fails.
        Raises FileNotFoundError if config file does not exist.
        """
        if not self._config_path.exists():
            raise FileNotFoundError(
                f"Configuration file not found: {self._config_path}"
            )

        raw_text = self._config_path.read_text(encoding="utf-8")

        try:
            raw_config = yaml.safe_load(raw_text)
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML syntax: {e}")

        if not isinstance(raw_config, dict):
            raise ValueError("Configuration must be a YAML mapping at the top level")

        valid, errors = self.validate(raw_config)
        if not valid:
            raise ValueError(
                f"Configuration validation failed: {'; '.join(errors)}"
            )

        config = self._build_config(raw_config)

        # Check endpoint reachability and log warnings (non-blocking)
        self._check_endpoints(config)

        with self._lock:
            self._current_config = config

        logger.info("Configuration loaded successfully from %s", self._config_path)
        return config

    def validate(self, raw_config: dict) -> tuple[bool, list[str]]:
        """Validate config structure, ranges, DAG integrity.

        Returns (valid, errors) where valid is True if no errors found.
        """
        errors: list[str] = []

        # Check required top-level keys
        for key in ("version", "modules", "endpoints", "global"):
            if key not in raw_config:
                errors.append(f"Missing required top-level key: '{key}'")

        if errors:
            return False, errors

        # Validate version
        if not isinstance(raw_config["version"], str):
            errors.append("'version' must be a string")

        # Validate modules
        errors.extend(self._validate_modules(raw_config.get("modules", [])))

        # Validate endpoints
        errors.extend(self._validate_endpoints(raw_config.get("endpoints", {})))

        # Validate global settings
        errors.extend(self._validate_global(raw_config.get("global", {})))

        return len(errors) == 0, errors

    def watch(self, callback: Callable[[LabConfig], None]) -> None:
        """Watch config file for changes, invoke callback on valid updates.

        The watcher runs in a background thread and applies valid changes
        within 10 seconds of file modification.
        """
        if self._observer is not None:
            logger.warning("File watcher already running")
            return

        handler = _ConfigFileHandler(self, callback)
        self._observer = Observer()
        self._observer.schedule(
            handler,
            str(self._config_path.parent),
            recursive=False,
        )
        self._observer.daemon = True
        self._observer.start()
        logger.info("Started watching configuration file: %s", self._config_path)

    def stop_watching(self) -> None:
        """Stop the file watcher."""
        if self._observer is not None:
            self._observer.stop()
            self._observer.join(timeout=5)
            self._observer = None
            logger.info("Stopped watching configuration file")

    def _validate_modules(self, modules: list) -> list[str]:
        """Validate the modules list."""
        errors: list[str] = []

        if not isinstance(modules, list):
            errors.append("'modules' must be a list")
            return errors

        if len(modules) < 1:
            errors.append("At least 1 module is required")
            return errors

        if len(modules) > 50:
            errors.append(
                f"Maximum 50 modules allowed, got {len(modules)}"
            )

        module_ids: set[str] = set()

        for i, module in enumerate(modules):
            prefix = f"modules[{i}]"

            if not isinstance(module, dict):
                errors.append(f"{prefix}: must be a mapping")
                continue

            # Required fields
            for field in ("id", "name", "order", "prerequisites",
                          "session_time_limit_minutes", "resource_limits"):
                if field not in module:
                    errors.append(f"{prefix}: missing required field '{field}'")

            if "id" not in module:
                continue

            module_id = module["id"]
            if not isinstance(module_id, str) or not module_id:
                errors.append(f"{prefix}: 'id' must be a non-empty string")
                continue

            if module_id in module_ids:
                errors.append(f"{prefix}: duplicate module id '{module_id}'")
            module_ids.add(module_id)

            # Validate order
            if "order" in module:
                order = module["order"]
                if not isinstance(order, int) or order < 1:
                    errors.append(
                        f"{prefix}: 'order' must be a positive integer"
                    )

            # Validate session_time_limit_minutes
            if "session_time_limit_minutes" in module:
                stl = module["session_time_limit_minutes"]
                if not isinstance(stl, (int, float)) or stl < 5 or stl > 480:
                    errors.append(
                        f"{prefix}: 'session_time_limit_minutes' must be "
                        f"between 5 and 480, got {stl}"
                    )

            # Validate resource_limits
            if "resource_limits" in module:
                errors.extend(
                    self._validate_resource_limits(
                        module["resource_limits"], prefix
                    )
                )

            # Validate prerequisites is a list of strings
            if "prerequisites" in module:
                prereqs = module["prerequisites"]
                if not isinstance(prereqs, list):
                    errors.append(
                        f"{prefix}: 'prerequisites' must be a list"
                    )
                else:
                    for prereq in prereqs:
                        if not isinstance(prereq, str):
                            errors.append(
                                f"{prefix}: prerequisite must be a string, "
                                f"got {type(prereq).__name__}"
                            )

        # Validate prerequisite references exist
        for i, module in enumerate(modules):
            if not isinstance(module, dict) or "prerequisites" not in module:
                continue
            prereqs = module.get("prerequisites", [])
            if not isinstance(prereqs, list):
                continue
            for prereq in prereqs:
                if isinstance(prereq, str) and prereq not in module_ids:
                    errors.append(
                        f"modules[{i}]: prerequisite '{prereq}' references "
                        f"undefined module"
                    )

        # Validate DAG integrity (no circular dependencies)
        cycle_errors = self._check_dag_integrity(modules)
        errors.extend(cycle_errors)

        return errors

    def _validate_resource_limits(
        self, limits: dict, prefix: str
    ) -> list[str]:
        """Validate resource_limits fields."""
        errors: list[str] = []

        if not isinstance(limits, dict):
            errors.append(f"{prefix}.resource_limits: must be a mapping")
            return errors

        # cpu_cores: 0.5 - 4.0
        if "cpu_cores" in limits:
            cpu = limits["cpu_cores"]
            if not isinstance(cpu, (int, float)) or cpu < 0.5 or cpu > 4.0:
                errors.append(
                    f"{prefix}.resource_limits.cpu_cores: must be between "
                    f"0.5 and 4.0, got {cpu}"
                )
        else:
            errors.append(
                f"{prefix}.resource_limits: missing required field 'cpu_cores'"
            )

        # memory_mb: 128 - 4096
        if "memory_mb" in limits:
            mem = limits["memory_mb"]
            if not isinstance(mem, (int, float)) or mem < 128 or mem > 4096:
                errors.append(
                    f"{prefix}.resource_limits.memory_mb: must be between "
                    f"128 and 4096, got {mem}"
                )
        else:
            errors.append(
                f"{prefix}.resource_limits: missing required field 'memory_mb'"
            )

        # time_minutes: 1 - 120
        if "time_minutes" in limits:
            time_min = limits["time_minutes"]
            if (not isinstance(time_min, (int, float))
                    or time_min < 1 or time_min > 120):
                errors.append(
                    f"{prefix}.resource_limits.time_minutes: must be between "
                    f"1 and 120, got {time_min}"
                )
        else:
            errors.append(
                f"{prefix}.resource_limits: missing required field "
                f"'time_minutes'"
            )

        return errors

    def _validate_endpoints(self, endpoints: dict) -> list[str]:
        """Validate endpoint URLs."""
        errors: list[str] = []

        if not isinstance(endpoints, dict):
            errors.append("'endpoints' must be a mapping")
            return errors

        url_pattern = re.compile(r'^https?://.+')

        for key, value in endpoints.items():
            if not isinstance(value, str):
                errors.append(
                    f"endpoints.{key}: must be a string"
                )
                continue

            # Only validate URL format for HTTP/HTTPS URLs (skip file paths)
            if value.startswith(("http://", "https://")):
                parsed = urlparse(value)
                if not parsed.scheme or not parsed.netloc:
                    errors.append(
                        f"endpoints.{key}: '{value}' is not a valid "
                        f"HTTP/HTTPS URL"
                    )
            elif value.startswith("/"):
                # Local file path - valid but no URL validation needed
                pass
            else:
                # Not a URL and not a file path - might be invalid
                if not url_pattern.match(value):
                    errors.append(
                        f"endpoints.{key}: '{value}' must be a valid "
                        f"HTTP/HTTPS URL or absolute file path"
                    )

        return errors

    def _validate_global(self, global_config: dict) -> list[str]:
        """Validate global configuration settings."""
        errors: list[str] = []

        if not isinstance(global_config, dict):
            errors.append("'global' must be a mapping")
            return errors

        # max_concurrent_containers: 1-100
        if "max_concurrent_containers" in global_config:
            mcc = global_config["max_concurrent_containers"]
            if not isinstance(mcc, (int, float)) or mcc < 1 or mcc > 100:
                errors.append(
                    f"global.max_concurrent_containers: must be between "
                    f"1 and 100, got {mcc}"
                )
        else:
            errors.append(
                "global: missing required field 'max_concurrent_containers'"
            )

        # memory_ceiling_mb: 128-65536
        if "memory_ceiling_mb" in global_config:
            mcm = global_config["memory_ceiling_mb"]
            if (not isinstance(mcm, (int, float))
                    or mcm < 128 or mcm > 65536):
                errors.append(
                    f"global.memory_ceiling_mb: must be between "
                    f"128 and 65536, got {mcm}"
                )
        else:
            errors.append(
                "global: missing required field 'memory_ceiling_mb'"
            )

        # cpu_ceiling_cores: 0.5-64
        if "cpu_ceiling_cores" in global_config:
            ccc = global_config["cpu_ceiling_cores"]
            if (not isinstance(ccc, (int, float))
                    or ccc < 0.5 or ccc > 64):
                errors.append(
                    f"global.cpu_ceiling_cores: must be between "
                    f"0.5 and 64, got {ccc}"
                )
        else:
            errors.append(
                "global: missing required field 'cpu_ceiling_cores'"
            )

        return errors

    def _check_dag_integrity(self, modules: list) -> list[str]:
        """Check for circular dependencies in module prerequisites.

        Uses Kahn's algorithm for topological sort to detect cycles.
        """
        errors: list[str] = []

        # Build adjacency list
        graph: dict[str, list[str]] = {}
        in_degree: dict[str, int] = {}

        for module in modules:
            if not isinstance(module, dict) or "id" not in module:
                continue
            module_id = module["id"]
            if module_id not in graph:
                graph[module_id] = []
                in_degree[module_id] = 0

        for module in modules:
            if not isinstance(module, dict):
                continue
            module_id = module.get("id")
            prereqs = module.get("prerequisites", [])
            if not isinstance(prereqs, list) or not module_id:
                continue

            for prereq in prereqs:
                if not isinstance(prereq, str) or prereq not in graph:
                    continue
                # Edge: prereq -> module_id (prereq must come before module)
                graph[prereq].append(module_id)
                in_degree[module_id] = in_degree.get(module_id, 0) + 1

        # Kahn's algorithm
        queue = deque(
            node for node, degree in in_degree.items() if degree == 0
        )
        sorted_count = 0

        while queue:
            node = queue.popleft()
            sorted_count += 1
            for neighbor in graph.get(node, []):
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        if sorted_count < len(graph):
            # Find modules involved in cycles
            cycle_modules = [
                node for node, degree in in_degree.items() if degree > 0
            ]
            errors.append(
                f"Circular prerequisite dependency detected involving "
                f"modules: {', '.join(sorted(cycle_modules))}"
            )

        return errors

    def _build_config(self, raw_config: dict) -> LabConfig:
        """Build a LabConfig object from validated raw config dict."""
        modules = []
        for mod in raw_config["modules"]:
            resource_limits = ResourceLimits(
                cpu_cores=float(mod["resource_limits"]["cpu_cores"]),
                memory_mb=int(mod["resource_limits"]["memory_mb"]),
                time_minutes=int(mod["resource_limits"]["time_minutes"]),
            )
            modules.append(LabModule(
                id=mod["id"],
                name=mod["name"],
                order=int(mod["order"]),
                prerequisites=list(mod.get("prerequisites", [])),
                session_time_limit_minutes=int(
                    mod["session_time_limit_minutes"]
                ),
                resource_limits=resource_limits,
            ))

        global_config = raw_config["global"]
        return LabConfig(
            version=raw_config["version"],
            modules=modules,
            endpoints=dict(raw_config["endpoints"]),
            max_concurrent_containers=int(
                global_config["max_concurrent_containers"]
            ),
            memory_ceiling_mb=int(global_config["memory_ceiling_mb"]),
            cpu_ceiling_cores=float(global_config["cpu_ceiling_cores"]),
        )

    def _check_endpoints(self, config: LabConfig) -> None:
        """Log warnings for unreachable endpoints (non-blocking).

        Per Req 16.6: Log warning for unreachable endpoints, continue operating.
        """
        import urllib.request
        import urllib.error

        for name, url in config.endpoints.items():
            if not url.startswith(("http://", "https://")):
                continue
            try:
                req = urllib.request.Request(url, method="HEAD")
                urllib.request.urlopen(req, timeout=5)
            except (urllib.error.URLError, OSError, ValueError) as e:
                logger.warning(
                    "Endpoint '%s' (%s) is unreachable: %s",
                    name, url, e
                )


class _ConfigFileHandler(FileSystemEventHandler):
    """Watchdog event handler for config file changes."""

    def __init__(
        self,
        loader: ConfigLoader,
        callback: Callable[[LabConfig], None],
    ):
        super().__init__()
        self._loader = loader
        self._callback = callback
        self._debounce_timer: Optional[threading.Timer] = None
        self._debounce_lock = threading.Lock()

    def on_modified(self, event):
        if event.is_directory:
            return

        # Check if the modified file is our config file
        modified_path = Path(event.src_path).resolve()
        config_path = self._loader._config_path.resolve()

        if modified_path != config_path:
            return

        # Debounce: wait 1 second before processing to handle
        # rapid successive writes (editors often save in multiple steps)
        with self._debounce_lock:
            if self._debounce_timer is not None:
                self._debounce_timer.cancel()
            self._debounce_timer = threading.Timer(
                1.0, self._reload_config
            )
            self._debounce_timer.start()

    def _reload_config(self) -> None:
        """Attempt to reload configuration after file change."""
        try:
            new_config = self._loader.load()
            self._callback(new_config)
            logger.info("Configuration hot-reloaded successfully")
        except (ValueError, FileNotFoundError) as e:
            # Reject invalid config, retain last valid config
            logger.error(
                "Configuration reload rejected - retaining previous "
                "valid configuration: %s", e
            )

#!/usr/bin/env python3
"""Lab environment setup utility.

Initializes a lab environment by checking prerequisites, preparing
the workspace, and starting required containers.

Usage:
    python -m labs.scripts.setup_lab --module install-bare-metal --student student-001
    python -m labs.scripts.setup_lab --module adding-applications --config labs/config/lab_config.yaml
"""

import argparse
import logging
import os
import shutil
import subprocess
import sys
from pathlib import Path

from labs.core.config_loader import ConfigLoader
from labs.core.credential_handler import CredentialHandler
from labs.core.models import LabConfig

logger = logging.getLogger(__name__)

DEFAULT_CONFIG_PATH = os.path.join("labs", "config", "lab_config.yaml")


def check_prerequisites() -> list[str]:
    """Check that required system prerequisites are available.

    Returns:
        List of error messages for missing prerequisites. Empty if all OK.
    """
    errors: list[str] = []

    # Check Python version
    if sys.version_info < (3, 9):
        errors.append(
            f"Python 3.9+ required, found {sys.version_info.major}."
            f"{sys.version_info.minor}"
        )

    # Check Docker availability
    if shutil.which("docker") is None:
        errors.append("Docker Engine not found. Install Docker to proceed.")
    else:
        try:
            result = subprocess.run(
                ["docker", "info"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode != 0:
                errors.append(
                    "Docker is installed but not running or accessible. "
                    "Ensure the Docker daemon is started."
                )
        except (subprocess.TimeoutExpired, OSError):
            errors.append("Failed to communicate with Docker daemon.")

    # Check docker-compose v2
    compose_found = False
    try:
        result = subprocess.run(
            ["docker", "compose", "version"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            compose_found = True
    except (subprocess.TimeoutExpired, OSError):
        pass

    if not compose_found:
        errors.append(
            "docker-compose v2 not found. "
            "Install Docker Compose plugin (docker compose)."
        )

    return errors


def prepare_workspace(module_id: str, config: LabConfig) -> Path:
    """Prepare the workspace directory for a lab module.

    Creates a temporary working directory for the lab session and
    validates that the module exists in the configuration.

    Args:
        module_id: The module identifier to set up.
        config: The loaded lab configuration.

    Returns:
        Path to the prepared workspace directory.

    Raises:
        ValueError: If the module_id is not found in config.
    """
    module = None
    for m in config.modules:
        if m.id == module_id:
            module = m
            break

    if module is None:
        available = [m.id for m in config.modules]
        raise ValueError(
            f"Module '{module_id}' not found in configuration. "
            f"Available modules: {', '.join(available)}"
        )

    # Create workspace directory
    workspace_dir = Path("labs") / "workspaces" / module_id
    workspace_dir.mkdir(parents=True, exist_ok=True)

    logger.info("Prepared workspace at: %s", workspace_dir)
    return workspace_dir


def start_containers(module_id: str, config: LabConfig) -> bool:
    """Start the required Docker containers for the lab module.

    Uses docker-compose to bring up the lab environment services.

    Args:
        module_id: The module identifier to start containers for.
        config: The loaded lab configuration.

    Returns:
        True if containers started successfully, False otherwise.
    """
    compose_file = Path("docker-compose.yml")
    if not compose_file.exists():
        logger.error("docker-compose.yml not found in project root.")
        return False

    try:
        result = subprocess.run(
            ["docker", "compose", "up", "-d"],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode != 0:
            logger.error(
                "Failed to start containers: %s", result.stderr.strip()
            )
            return False

        logger.info("Lab containers started successfully for module '%s'.", module_id)
        return True
    except subprocess.TimeoutExpired:
        logger.error("Container startup timed out after 120 seconds.")
        return False
    except OSError as e:
        logger.error("Failed to run docker compose: %s", e)
        return False


def setup_lab(
    module_id: str,
    student_id: str,
    config_path: str = DEFAULT_CONFIG_PATH,
    skip_containers: bool = False,
) -> int:
    """Run the full lab setup sequence.

    Steps:
    1. Check system prerequisites
    2. Load and validate configuration
    3. Prepare workspace directory
    4. Start Docker containers (unless skipped)

    Args:
        module_id: The module to set up.
        student_id: The student identifier.
        config_path: Path to the lab configuration YAML file.
        skip_containers: If True, skip Docker container startup.

    Returns:
        Exit code: 0 for success, non-zero for failure.
    """
    print(f"Setting up lab environment for module '{module_id}'...")
    print(f"Student: {student_id}")
    print()

    # Step 1: Check prerequisites
    print("[1/4] Checking prerequisites...")
    errors = check_prerequisites()
    if errors:
        print("  ERROR: Prerequisites not met:")
        for error in errors:
            print(f"    - {error}")
        return 1
    print("  OK: All prerequisites satisfied.")

    # Step 2: Load configuration
    print(f"[2/4] Loading configuration from '{config_path}'...")
    if not os.path.exists(config_path):
        print(f"  ERROR: Configuration file not found: {config_path}")
        return 1

    loader = ConfigLoader(config_path)
    try:
        config = loader.load()
    except Exception as e:
        print(f"  ERROR: Failed to load configuration: {e}")
        return 1
    print("  OK: Configuration loaded and validated.")

    # Step 3: Prepare workspace
    print(f"[3/4] Preparing workspace for module '{module_id}'...")
    try:
        workspace = prepare_workspace(module_id, config)
    except ValueError as e:
        print(f"  ERROR: {e}")
        return 1
    print(f"  OK: Workspace ready at '{workspace}'.")

    # Step 4: Start containers
    if skip_containers:
        print("[4/4] Skipping container startup (--skip-containers).")
    else:
        print("[4/4] Starting lab containers...")
        if not start_containers(module_id, config):
            print("  ERROR: Failed to start containers.")
            return 1
        print("  OK: Containers running.")

    print()
    print(f"Lab environment ready for module '{module_id}'.")
    print(f"Workspace: {workspace}")
    return 0


def main() -> None:
    """CLI entry point for lab setup."""
    parser = argparse.ArgumentParser(
        description="Set up a lab environment for a specific module.",
        prog="setup_lab",
    )
    parser.add_argument(
        "--module",
        required=True,
        help="Module ID to set up (e.g., 'install-bare-metal').",
    )
    parser.add_argument(
        "--student",
        default="default-student",
        help="Student identifier (default: 'default-student').",
    )
    parser.add_argument(
        "--config",
        default=DEFAULT_CONFIG_PATH,
        help=f"Path to lab config YAML (default: '{DEFAULT_CONFIG_PATH}').",
    )
    parser.add_argument(
        "--skip-containers",
        action="store_true",
        help="Skip Docker container startup.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging output.",
    )

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    exit_code = setup_lab(
        module_id=args.module,
        student_id=args.student,
        config_path=args.config,
        skip_containers=args.skip_containers,
    )
    sys.exit(exit_code)


if __name__ == "__main__":
    main()

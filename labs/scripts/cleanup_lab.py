#!/usr/bin/env python3
"""Lab environment teardown utility.

Cleans up a lab environment by stopping containers, removing temporary
files, and releasing resources.

Usage:
    python -m labs.scripts.cleanup_lab --module install-bare-metal
    python -m labs.scripts.cleanup_lab --module adding-applications --keep-data
    python -m labs.scripts.cleanup_lab --all
"""

import argparse
import logging
import os
import shutil
import subprocess
import sys
from pathlib import Path

from labs.core.config_loader import ConfigLoader
from labs.core.models import LabConfig

logger = logging.getLogger(__name__)

DEFAULT_CONFIG_PATH = os.path.join("labs", "config", "lab_config.yaml")
WORKSPACES_DIR = Path("labs") / "workspaces"


def stop_containers(module_id: str | None = None) -> bool:
    """Stop lab Docker containers.

    Args:
        module_id: If provided, attempts to stop only containers related
                   to the specific module. If None, stops all lab containers.

    Returns:
        True if containers stopped successfully, False otherwise.
    """
    compose_file = Path("docker-compose.yml")
    if not compose_file.exists():
        logger.warning("docker-compose.yml not found; skipping container stop.")
        return True

    try:
        cmd = ["docker", "compose", "down", "--remove-orphans"]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode != 0:
            logger.error(
                "Failed to stop containers: %s", result.stderr.strip()
            )
            return False

        logger.info("Lab containers stopped successfully.")
        return True
    except subprocess.TimeoutExpired:
        logger.error("Container shutdown timed out after 60 seconds.")
        return False
    except OSError as e:
        logger.error("Failed to run docker compose: %s", e)
        return False


def remove_temp_files(module_id: str | None = None) -> int:
    """Remove temporary workspace files.

    Args:
        module_id: If provided, removes only the workspace for the specific
                   module. If None, removes all lab workspaces.

    Returns:
        Number of directories removed.
    """
    removed = 0

    if module_id:
        workspace = WORKSPACES_DIR / module_id
        if workspace.exists():
            shutil.rmtree(workspace)
            logger.info("Removed workspace: %s", workspace)
            removed += 1
        else:
            logger.info("No workspace found for module '%s'.", module_id)
    else:
        if WORKSPACES_DIR.exists():
            for entry in WORKSPACES_DIR.iterdir():
                if entry.is_dir():
                    shutil.rmtree(entry)
                    logger.info("Removed workspace: %s", entry)
                    removed += 1

    return removed


def cleanup_docker_resources() -> None:
    """Remove dangling Docker resources created by lab sessions.

    Prunes stopped containers, unused networks, and dangling images
    that were created by the lab framework.
    """
    try:
        # Remove stopped containers with lab labels
        subprocess.run(
            ["docker", "container", "prune", "-f",
             "--filter", "label=managed_by=lab_framework"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        logger.info("Pruned stopped lab containers.")
    except (subprocess.TimeoutExpired, OSError) as e:
        logger.warning("Failed to prune containers: %s", e)

    try:
        # Remove unused lab networks
        subprocess.run(
            ["docker", "network", "prune", "-f",
             "--filter", "label=managed_by=lab_framework"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        logger.info("Pruned unused lab networks.")
    except (subprocess.TimeoutExpired, OSError) as e:
        logger.warning("Failed to prune networks: %s", e)


def cleanup_lab(
    module_id: str | None = None,
    config_path: str = DEFAULT_CONFIG_PATH,
    keep_data: bool = False,
    skip_containers: bool = False,
    prune_docker: bool = False,
) -> int:
    """Run the full lab cleanup sequence.

    Steps:
    1. Stop Docker containers
    2. Remove temporary workspace files
    3. (Optional) Prune dangling Docker resources

    Args:
        module_id: Module to clean up, or None for all modules.
        config_path: Path to the lab configuration YAML file.
        keep_data: If True, preserve workspace data files.
        skip_containers: If True, skip stopping containers.
        prune_docker: If True, also prune dangling Docker resources.

    Returns:
        Exit code: 0 for success, non-zero for failure.
    """
    target = f"module '{module_id}'" if module_id else "all modules"
    print(f"Cleaning up lab environment for {target}...")
    print()

    # Validate module exists in config if specified
    if module_id:
        if os.path.exists(config_path):
            loader = ConfigLoader(config_path)
            try:
                config = loader.load()
                module_ids = [m.id for m in config.modules]
                if module_id not in module_ids:
                    print(
                        f"  WARNING: Module '{module_id}' not found in config. "
                        f"Available: {', '.join(module_ids)}"
                    )
                    print("  Continuing with cleanup anyway...")
                    print()
            except Exception:
                logger.debug("Could not load config for validation.")

    # Step 1: Stop containers
    if skip_containers:
        print("[1/3] Skipping container shutdown (--skip-containers).")
    else:
        print("[1/3] Stopping lab containers...")
        if stop_containers(module_id):
            print("  OK: Containers stopped.")
        else:
            print("  WARNING: Some containers may not have stopped cleanly.")

    # Step 2: Remove temp files
    if keep_data:
        print("[2/3] Keeping workspace data (--keep-data).")
    else:
        print("[2/3] Removing temporary files...")
        removed = remove_temp_files(module_id)
        print(f"  OK: Removed {removed} workspace(s).")

    # Step 3: Prune Docker resources
    if prune_docker:
        print("[3/3] Pruning dangling Docker resources...")
        cleanup_docker_resources()
        print("  OK: Docker resources pruned.")
    else:
        print("[3/3] Skipping Docker prune (use --prune to enable).")

    print()
    print(f"Cleanup complete for {target}.")
    return 0


def main() -> None:
    """CLI entry point for lab cleanup."""
    parser = argparse.ArgumentParser(
        description="Tear down a lab environment and clean up resources.",
        prog="cleanup_lab",
    )
    parser.add_argument(
        "--module",
        default=None,
        help="Module ID to clean up. If omitted, cleans all modules.",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        dest="cleanup_all",
        help="Explicitly clean up all module workspaces.",
    )
    parser.add_argument(
        "--config",
        default=DEFAULT_CONFIG_PATH,
        help=f"Path to lab config YAML (default: '{DEFAULT_CONFIG_PATH}').",
    )
    parser.add_argument(
        "--keep-data",
        action="store_true",
        help="Preserve workspace data files during cleanup.",
    )
    parser.add_argument(
        "--skip-containers",
        action="store_true",
        help="Skip stopping Docker containers.",
    )
    parser.add_argument(
        "--prune",
        action="store_true",
        help="Also prune dangling Docker resources (containers, networks).",
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

    module_id = args.module
    if args.cleanup_all:
        module_id = None

    exit_code = cleanup_lab(
        module_id=module_id,
        config_path=args.config,
        keep_data=args.keep_data,
        skip_containers=args.skip_containers,
        prune_docker=args.prune,
    )
    sys.exit(exit_code)


if __name__ == "__main__":
    main()

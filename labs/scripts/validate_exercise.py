#!/usr/bin/env python3
"""Exercise validation utility.

Runs validation on a specific exercise, checking assertions and
displaying pass/fail results for each step.

Usage:
    python -m labs.scripts.validate_exercise --module install-bare-metal --exercise 01_system_prereqs
    python -m labs.scripts.validate_exercise --module adding-applications --exercise 02_rest_api --verbose
"""

import argparse
import importlib
import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Optional

from labs.core.config_loader import ConfigLoader
from labs.core.models import LabConfig, ExerciseStatus
from labs.core.validators import ExerciseValidator, ExerciseValidationResult

logger = logging.getLogger(__name__)

DEFAULT_CONFIG_PATH = os.path.join("labs", "config", "lab_config.yaml")


class LocalPlatformClient:
    """A local platform client stub for offline validation.

    Used when the AI-Powered-Store platform is not available.
    Returns empty responses for all queries.
    """

    def query(self, endpoint: str, params: Optional[dict] = None) -> dict:
        """Return an empty response for local validation."""
        logger.debug("Local platform query: %s (params: %s)", endpoint, params)
        return {}


def load_exercise_steps(module_id: str, exercise_id: str) -> Optional[list[dict]]:
    """Load exercise step definitions from a JSON file or module.

    Looks for exercise definitions in the following locations:
    1. labs/modules/{module_id}/exercises/{exercise_id}.json
    2. labs/modules/{module_id}/exercises/{exercise_id}.py (as importable module)

    Args:
        module_id: The module containing the exercise.
        exercise_id: The exercise identifier.

    Returns:
        List of step dicts with assertions, or None if not found.
    """
    # Try JSON definition first
    json_path = (
        Path("labs") / "modules" / module_id / "exercises" / f"{exercise_id}.json"
    )
    if json_path.exists():
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict) and "steps" in data:
                return data["steps"]
            if isinstance(data, list):
                return data
        except (json.JSONDecodeError, OSError) as e:
            logger.error("Failed to load exercise JSON: %s", e)
            return None

    # Try Python module
    py_path = (
        Path("labs") / "modules" / module_id / "exercises" / f"{exercise_id}.py"
    )
    if py_path.exists():
        try:
            module_path = f"labs.modules.{module_id}.exercises.{exercise_id}"
            mod = importlib.import_module(module_path)
            if hasattr(mod, "get_steps"):
                return mod.get_steps()
            if hasattr(mod, "STEPS"):
                return mod.STEPS
        except (ImportError, AttributeError) as e:
            logger.error("Failed to import exercise module: %s", e)
            return None

    return None


def display_results(result: ExerciseValidationResult) -> None:
    """Display validation results in a human-readable format.

    Args:
        result: The exercise validation result to display.
    """
    status_icon = "✓" if result.passed else "✗"
    status_text = "PASSED" if result.passed else "FAILED"

    print()
    print(f"{'='*60}")
    print(f"  Exercise: {result.exercise_id}")
    print(f"  Result:   {status_icon} {status_text}")
    print(f"{'='*60}")
    print()

    if result.step_results:
        print("  Step Results:")
        print(f"  {'-'*56}")
        for i, step_result in enumerate(result.step_results, 1):
            icon = "✓" if step_result.passed else "✗"
            print(f"  {icon} [{i}] {step_result.step_name}")
            print(f"        {step_result.message}")
            if not step_result.passed and step_result.details:
                expected = step_result.details.get("expected")
                actual = step_result.details.get("actual")
                if expected is not None:
                    print(f"        Expected: {expected!r}")
                if actual is not None:
                    print(f"        Actual:   {actual!r}")
            print()

    total = len(result.step_results)
    passed = sum(1 for r in result.step_results if r.passed)
    print(f"  Summary: {passed}/{total} steps passed.")
    print()


def validate_exercise(
    module_id: str,
    exercise_id: str,
    config_path: str = DEFAULT_CONFIG_PATH,
    steps_json: Optional[str] = None,
) -> int:
    """Run validation for a specific exercise.

    Args:
        module_id: The module containing the exercise.
        exercise_id: The exercise to validate.
        config_path: Path to the lab configuration YAML file.
        steps_json: Optional JSON string containing step definitions.
                    If provided, overrides file-based step loading.

    Returns:
        Exit code: 0 if all checks pass, 1 if any check fails, 2 on error.
    """
    print(f"Validating exercise '{exercise_id}' in module '{module_id}'...")

    # Load configuration
    if os.path.exists(config_path):
        loader = ConfigLoader(config_path)
        try:
            config = loader.load()
            # Verify module exists
            module_ids = [m.id for m in config.modules]
            if module_id not in module_ids:
                print(
                    f"  WARNING: Module '{module_id}' not in config. "
                    f"Available: {', '.join(module_ids)}"
                )
        except Exception as e:
            print(f"  WARNING: Could not load config: {e}")
    else:
        print(f"  INFO: Config not found at '{config_path}', using defaults.")

    # Load exercise steps
    steps: Optional[list[dict]] = None

    if steps_json:
        try:
            steps = json.loads(steps_json)
        except json.JSONDecodeError as e:
            print(f"  ERROR: Invalid JSON for --steps: {e}")
            return 2
    else:
        steps = load_exercise_steps(module_id, exercise_id)

    if steps is None:
        print(
            f"  ERROR: No exercise definition found for "
            f"'{exercise_id}' in module '{module_id}'."
        )
        print(f"  Looked in: labs/modules/{module_id}/exercises/")
        print(f"  Expected: {exercise_id}.json or {exercise_id}.py")
        return 2

    if not steps:
        print("  WARNING: Exercise has no steps defined.")
        return 0

    # Run validation
    platform_client = LocalPlatformClient()
    validator = ExerciseValidator(platform_client)

    print(f"  Running {len(steps)} validation step(s)...")
    start_time = time.monotonic()
    result = validator.validate_exercise(exercise_id, steps)
    elapsed = time.monotonic() - start_time

    # Display results
    display_results(result)
    print(f"  Validation completed in {elapsed:.2f}s.")

    return 0 if result.passed else 1


def main() -> None:
    """CLI entry point for exercise validation."""
    parser = argparse.ArgumentParser(
        description="Validate a specific lab exercise against its assertions.",
        prog="validate_exercise",
    )
    parser.add_argument(
        "--module",
        required=True,
        help="Module ID containing the exercise (e.g., 'install-bare-metal').",
    )
    parser.add_argument(
        "--exercise",
        required=True,
        help="Exercise ID to validate (e.g., '01_system_prereqs').",
    )
    parser.add_argument(
        "--config",
        default=DEFAULT_CONFIG_PATH,
        help=f"Path to lab config YAML (default: '{DEFAULT_CONFIG_PATH}').",
    )
    parser.add_argument(
        "--steps",
        default=None,
        help=(
            "JSON string with step definitions. Overrides file-based loading. "
            "Example: '[{\"name\":\"check\",\"actual\":\"ok\","
            "\"assertion\":{\"type\":\"equality\",\"expected\":\"ok\"}}]'"
        ),
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

    exit_code = validate_exercise(
        module_id=args.module,
        exercise_id=args.exercise,
        config_path=args.config,
        steps_json=args.steps,
    )
    sys.exit(exit_code)


if __name__ == "__main__":
    main()

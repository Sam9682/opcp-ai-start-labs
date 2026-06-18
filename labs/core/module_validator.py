"""Module structure validator for Lab_Module directories.

Validates that each Lab_Module directory contains the required components
(README.md, exercises/, solutions/, setup/) and that README.md contains
required sections (title, objective, prerequisite list, exercise table).
"""

import logging
import re
from pathlib import Path

logger = logging.getLogger(__name__)

# Required subdirectories for each Lab_Module
REQUIRED_SUBDIRS = ["exercises", "solutions", "setup"]

# Required file in each Lab_Module
REQUIRED_FILES = ["README.md"]

# Required sections in README.md
REQUIRED_README_SECTIONS = ["title", "objective", "prerequisite list", "exercise table"]


def validate_module(module_path: str | Path) -> list[str]:
    """Validate a single Lab_Module directory for required components.

    Checks for:
    - Required subdirectories: exercises/, solutions/, setup/
    - Required files: README.md
    - README.md content: title, objective, prerequisite list, exercise table

    Args:
        module_path: Path to the Lab_Module directory.

    Returns:
        A list of warning messages. Empty list means all validations passed.
    """
    module_path = Path(module_path)
    warnings: list[str] = []

    if not module_path.is_dir():
        warnings.append(f"Module path '{module_path}' does not exist or is not a directory")
        return warnings

    module_name = module_path.name

    # Check required subdirectories
    for subdir in REQUIRED_SUBDIRS:
        subdir_path = module_path / subdir
        if not subdir_path.is_dir():
            warnings.append(
                f"Module '{module_name}' is missing required subdirectory: {subdir}/"
            )

    # Check required files
    for filename in REQUIRED_FILES:
        file_path = module_path / filename
        if not file_path.is_file():
            warnings.append(
                f"Module '{module_name}' is missing required file: {filename}"
            )

    # Validate README.md content if it exists
    readme_path = module_path / "README.md"
    if readme_path.is_file():
        readme_warnings = _validate_readme_content(readme_path, module_name)
        warnings.extend(readme_warnings)

    return warnings


def validate_all_modules(modules_dir: str | Path) -> dict[str, list[str]]:
    """Validate all Lab_Module directories in the modules directory.

    Args:
        modules_dir: Path to the directory containing Lab_Module directories.

    Returns:
        A dictionary mapping module names to their lists of warnings.
        Modules with no warnings are included with empty lists.
    """
    modules_dir = Path(modules_dir)
    results: dict[str, list[str]] = {}

    if not modules_dir.is_dir():
        logger.warning("Modules directory '%s' does not exist or is not a directory", modules_dir)
        return results

    for item in sorted(modules_dir.iterdir()):
        # Skip non-directories and Python package files
        if not item.is_dir() or item.name.startswith((".", "__")):
            continue

        module_warnings = validate_module(item)
        results[item.name] = module_warnings

        # Log warnings for each module
        for warning in module_warnings:
            logger.warning(warning)

    return results


def _validate_readme_content(readme_path: Path, module_name: str) -> list[str]:
    """Validate that README.md contains required sections.

    Required sections:
    - Title: A markdown heading (# Title)
    - Objective: A section describing the objective
    - Prerequisite list: A list of prerequisites
    - Exercise table: A markdown table of exercises

    Args:
        readme_path: Path to the README.md file.
        module_name: Name of the module (for warning messages).

    Returns:
        A list of warning messages for missing sections.
    """
    warnings: list[str] = []

    try:
        content = readme_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as e:
        warnings.append(
            f"Module '{module_name}' README.md could not be read: {e}"
        )
        return warnings

    # Check for title (any markdown heading at level 1)
    if not _has_title(content):
        warnings.append(
            f"Module '{module_name}' README.md is missing required section: title"
        )

    # Check for objective section
    if not _has_objective(content):
        warnings.append(
            f"Module '{module_name}' README.md is missing required section: objective"
        )

    # Check for prerequisite list
    if not _has_prerequisite_list(content):
        warnings.append(
            f"Module '{module_name}' README.md is missing required section: prerequisite list"
        )

    # Check for exercise table
    if not _has_exercise_table(content):
        warnings.append(
            f"Module '{module_name}' README.md is missing required section: exercise table"
        )

    return warnings


def _has_title(content: str) -> bool:
    """Check if content has a markdown level-1 heading (title)."""
    return bool(re.search(r"^#\s+\S", content, re.MULTILINE))


def _has_objective(content: str) -> bool:
    """Check if content has an objective section.

    Looks for a heading containing 'objective' (case-insensitive)
    or a paragraph that starts with 'Objective:' or 'objective:'.
    """
    # Check for heading with 'objective' keyword
    if re.search(r"^#{1,6}\s+.*objective", content, re.MULTILINE | re.IGNORECASE):
        return True
    # Check for bold or labeled objective line
    if re.search(r"^\*{0,2}objective\*{0,2}\s*:", content, re.MULTILINE | re.IGNORECASE):
        return True
    return False


def _has_prerequisite_list(content: str) -> bool:
    """Check if content has a prerequisite list.

    Looks for a heading or label containing 'prerequisite' followed by
    a markdown list (lines starting with - or *).
    """
    # Check for a prerequisite heading/label
    prereq_match = re.search(
        r"^#{1,6}\s+.*prerequisite|^\*{0,2}prerequisite\*{0,2}\s*:",
        content,
        re.MULTILINE | re.IGNORECASE,
    )
    if not prereq_match:
        return False

    # Check that a list follows (within the next few lines after the heading)
    after_heading = content[prereq_match.end():]
    # Look for list items (- item or * item) within the next ~500 chars
    snippet = after_heading[:500]
    return bool(re.search(r"^\s*[-*]\s+\S", snippet, re.MULTILINE))


def _has_exercise_table(content: str) -> bool:
    """Check if content has a markdown table of exercises.

    Looks for a markdown table (lines with | separators and a separator row
    with dashes).
    """
    # Match a markdown table: at least a header row and separator row with pipes
    # e.g. | Col1 | Col2 |
    #      |------|------|
    return bool(
        re.search(
            r"^\|.+\|.*\n\|[\s\-:|]+\|",
            content,
            re.MULTILINE,
        )
    )

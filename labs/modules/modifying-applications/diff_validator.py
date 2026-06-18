"""Diff validation for the Modifying Applications module.

Validates that AI Developer agent-produced diffs:
- Apply cleanly to the target file without merge conflicts
- Contain only syntactically correct code
- Produce a valid modified file
"""

import re
import subprocess
import tempfile
import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class DiffValidationError:
    """Represents a single validation error for a diff."""

    category: str  # "merge_conflict" | "syntax_error" | "empty_diff" | "format_error"
    message: str
    suggestion: Optional[str] = None


@dataclass
class DiffValidationResult:
    """Result of diff validation."""

    valid: bool
    errors: list[DiffValidationError]
    patched_content: Optional[str] = None


def validate_diff_format(diff_text: str) -> list[DiffValidationError]:
    """Validate that a diff string is well-formed unified diff format.

    Args:
        diff_text: The unified diff text to validate.

    Returns:
        List of format errors found, empty if valid.
    """
    errors: list[DiffValidationError] = []

    if not diff_text or not diff_text.strip():
        errors.append(DiffValidationError(
            category="empty_diff",
            message="Diff is empty or contains only whitespace.",
            suggestion="Re-invoke the AI Developer agent with a more specific prompt.",
        ))
        return errors

    lines = diff_text.strip().split("\n")

    # Check for basic unified diff markers
    has_minus_prefix = any(line.startswith("---") for line in lines)
    has_plus_prefix = any(line.startswith("+++") for line in lines)
    has_hunk_header = any(line.startswith("@@") for line in lines)

    if not (has_minus_prefix and has_plus_prefix and has_hunk_header):
        errors.append(DiffValidationError(
            category="format_error",
            message="Diff does not appear to be in valid unified diff format.",
            suggestion="Ensure the AI Developer agent outputs in unified diff format (---/+++/@@ markers).",
        ))

    return errors


def apply_diff(original_content: str, diff_text: str) -> DiffValidationResult:
    """Attempt to apply a unified diff to original file content.

    Args:
        original_content: The original file content to patch.
        diff_text: The unified diff to apply.

    Returns:
        DiffValidationResult indicating success/failure and patched content.
    """
    errors: list[DiffValidationError] = []

    # First validate the diff format
    format_errors = validate_diff_format(diff_text)
    if format_errors:
        return DiffValidationResult(valid=False, errors=format_errors)

    # Attempt to apply the diff using patch command
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            original_path = os.path.join(tmpdir, "original.py")
            diff_path = os.path.join(tmpdir, "changes.patch")
            output_path = os.path.join(tmpdir, "original.py")

            with open(original_path, "w") as f:
                f.write(original_content)

            with open(diff_path, "w") as f:
                f.write(diff_text)

            # Try to apply the patch
            result = subprocess.run(
                ["patch", "--forward", "--no-backup-if-mismatch",
                 original_path, diff_path],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode != 0:
                # Check for specific failure reasons
                stderr = result.stderr + result.stdout
                if "FAILED" in stderr or "reject" in stderr.lower():
                    errors.append(DiffValidationError(
                        category="merge_conflict",
                        message="Diff does not apply cleanly to the target file.",
                        suggestion="Try a more specific modification prompt or update the target file reference.",
                    ))
                else:
                    errors.append(DiffValidationError(
                        category="merge_conflict",
                        message=f"Patch application failed: {stderr.strip()}",
                        suggestion="Verify the diff references the correct file and line numbers.",
                    ))
                return DiffValidationResult(valid=False, errors=errors)

            # Read the patched content
            with open(output_path, "r") as f:
                patched_content = f.read()

            return DiffValidationResult(
                valid=True,
                errors=[],
                patched_content=patched_content,
            )

    except FileNotFoundError:
        # patch command not available, fall back to manual check
        errors.append(DiffValidationError(
            category="format_error",
            message="The 'patch' utility is not available in this environment.",
            suggestion="Install patch utility or verify diff manually.",
        ))
        return DiffValidationResult(valid=False, errors=errors)

    except subprocess.TimeoutExpired:
        errors.append(DiffValidationError(
            category="merge_conflict",
            message="Patch application timed out.",
            suggestion="The diff may be too large or contain infinite loops in replacement.",
        ))
        return DiffValidationResult(valid=False, errors=errors)


def check_syntax(code: str, language: str = "python") -> DiffValidationResult:
    """Check that code is syntactically correct for the specified language.

    Args:
        code: The code content to check.
        language: The programming language ("python" supported).

    Returns:
        DiffValidationResult with syntax check outcome.
    """
    errors: list[DiffValidationError] = []

    if language == "python":
        try:
            compile(code, "<ai-developer-output>", "exec")
        except SyntaxError as e:
            errors.append(DiffValidationError(
                category="syntax_error",
                message=f"Syntax error at line {e.lineno}: {e.msg}",
                suggestion="Ask the AI Developer agent to fix the syntax error in the generated code.",
            ))
            return DiffValidationResult(valid=False, errors=errors)
    else:
        # For non-Python languages, we can only do basic checks
        pass

    return DiffValidationResult(valid=True, errors=[], patched_content=code)


def validate_modification(
    original_content: str,
    diff_text: str,
    language: str = "python",
) -> DiffValidationResult:
    """Full validation of an AI Developer agent modification.

    Validates that:
    1. The diff is well-formed
    2. The diff applies cleanly to the original content
    3. The resulting code is syntactically correct

    Args:
        original_content: Original file content.
        diff_text: The unified diff produced by the AI Developer agent.
        language: Programming language for syntax checking.

    Returns:
        DiffValidationResult with complete validation outcome.
    """
    # Step 1: Apply the diff
    apply_result = apply_diff(original_content, diff_text)
    if not apply_result.valid:
        return apply_result

    # Step 2: Check syntax of the patched content
    patched_content = apply_result.patched_content
    if patched_content and language == "python":
        syntax_result = check_syntax(patched_content, language)
        if not syntax_result.valid:
            return syntax_result

    return DiffValidationResult(
        valid=True,
        errors=[],
        patched_content=patched_content,
    )

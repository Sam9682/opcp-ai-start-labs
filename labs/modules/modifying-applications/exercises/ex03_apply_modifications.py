"""Exercise 3: Apply Modifications.

Approve and apply the AI-generated diff to the target application
source code, producing the modified file.
"""

from typing import Optional

from labs.templates.exercise_base import Exercise
from labs.modules.modifying_applications.diff_validator import (
    validate_modification,
    DiffValidationResult,
)


class ApplyModificationsExercise(Exercise):
    """Approve and apply AI-generated code modifications."""

    @property
    def exercise_id(self) -> str:
        return "03_apply_modifications"

    @property
    def name(self) -> str:
        return "Apply Modifications"

    @property
    def description(self) -> str:
        return (
            "Approve and apply the AI-generated diff to the target "
            "application source code. The diff must apply cleanly and "
            "produce syntactically correct code."
        )

    @property
    def timeout_minutes(self) -> int:
        return 10

    @property
    def prerequisites(self) -> list[str]:
        return ["02_review_changes"]

    def setup(self) -> None:
        """No setup required for apply exercise."""
        pass

    def execute(self, submission: dict) -> dict:
        """Apply the approved diff to the target file.

        Args:
            submission: Dict with keys:
                - original_content: Original source file content
                - diff_text: The unified diff to apply
                - target_file: Path of the target file
                - language: Programming language (default: python)
                - approved: Boolean indicating learner has reviewed and approved

        Returns:
            Dict with application result and the modified content.
        """
        original_content = submission.get("original_content", "")
        diff_text = submission.get("diff_text", "")
        target_file = submission.get("target_file", "")
        language = submission.get("language", "python")
        approved = submission.get("approved", False)

        if not original_content:
            return {
                "status": "error",
                "message": "Field 'original_content' is required.",
                "applied": False,
            }
        if not diff_text:
            return {
                "status": "error",
                "message": "Field 'diff_text' is required.",
                "applied": False,
                "suggestion": "Re-invoke the AI Developer agent to generate a new diff.",
            }
        if not target_file:
            return {
                "status": "error",
                "message": "Field 'target_file' is required.",
                "applied": False,
            }
        if not approved:
            return {
                "status": "error",
                "message": "Changes must be reviewed and approved before applying.",
                "applied": False,
            }

        # Full validation: format + apply + syntax
        result = validate_modification(original_content, diff_text, language)

        if not result.valid:
            error_details = [
                {
                    "category": e.category,
                    "message": e.message,
                    "suggestion": e.suggestion,
                }
                for e in result.errors
            ]
            suggestions = [e.suggestion for e in result.errors if e.suggestion]
            return {
                "status": "apply_failed",
                "applied": False,
                "errors": error_details,
                "suggestion": suggestions[0] if suggestions else (
                    "Try re-invoking the AI Developer agent with a more specific prompt."
                ),
            }

        return {
            "status": "applied",
            "applied": True,
            "target_file": target_file,
            "modified_content": result.patched_content,
            "original_content": original_content,
        }

    def validate(self, result: dict) -> list[dict]:
        """Validate that the modification was applied successfully.

        Checks:
        1. Changes were approved
        2. Diff applied cleanly to the target file
        3. Modified content is present and non-empty
        """
        checks = []

        status = result.get("status", "unknown")
        if status == "error":
            message = result.get("message", "Unknown error")
            suggestion = result.get("suggestion", "")
            feedback = f"Application failed: {message}"
            if suggestion:
                feedback += f" Suggestion: {suggestion}"
            checks.append({
                "name": "apply_input",
                "passed": False,
                "feedback": feedback,
                "expected": "applied",
                "actual": "error",
            })
            return checks

        # Check 1: Application status
        applied = result.get("applied", False)
        checks.append({
            "name": "diff_application",
            "passed": applied,
            "feedback": (
                "Diff applied cleanly to the target file."
                if applied
                else "Diff failed to apply to the target file."
            ),
            "expected": "applied",
            "actual": "applied" if applied else "failed",
        })

        if not applied:
            # Report errors and suggestion
            errors = result.get("errors", [])
            suggestion = result.get("suggestion", "")
            error_msg = "; ".join(e.get("message", "") for e in errors)
            feedback = f"Failure reason: {error_msg}"
            if suggestion:
                feedback += f" Suggestion: {suggestion}"
            checks.append({
                "name": "failure_feedback",
                "passed": False,
                "feedback": feedback,
                "expected": "clean application",
                "actual": "merge conflict or syntax error",
            })
            return checks

        # Check 2: Target file is specified
        target_file = result.get("target_file", "")
        checks.append({
            "name": "target_file",
            "passed": bool(target_file),
            "feedback": (
                f"Target file: {target_file}"
                if target_file
                else "No target file specified."
            ),
            "expected": "non-empty path",
            "actual": target_file or "(empty)",
        })

        # Check 3: Modified content is present
        modified_content = result.get("modified_content", "")
        checks.append({
            "name": "modified_content",
            "passed": bool(modified_content),
            "feedback": (
                "Modified content generated successfully."
                if modified_content
                else "No modified content produced."
            ),
            "expected": "non-empty content",
            "actual": f"{len(modified_content)} characters" if modified_content else "(empty)",
        })

        return checks

    def teardown(self) -> None:
        """No cleanup needed for apply exercise."""
        pass

    def get_hints(self) -> list[str]:
        return [
            "Make sure you have reviewed and approved the changes (set approved=True).",
            "If the diff doesn't apply cleanly, the original file may have changed.",
            "Re-invoke the AI Developer agent with the current file content.",
            "Keep modifications focused on a single concern for cleaner diffs.",
        ]

    def get_instructions(self) -> Optional[str]:
        return (
            "Apply the approved AI-generated modifications:\n\n"
            "1. Confirm you have reviewed the diff (Exercise 2)\n"
            "2. Set 'approved: true' to indicate approval\n"
            "3. Provide the original file content and diff text\n"
            "4. The system will:\n"
            "   - Validate the diff format\n"
            "   - Apply the patch to the original content\n"
            "   - Verify the result is syntactically correct\n"
            "   - Return the modified file content\n\n"
            "If application fails, an error message and alternative\n"
            "prompt suggestion will be provided."
        )

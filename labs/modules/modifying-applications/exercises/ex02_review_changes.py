"""Exercise 2: Review Proposed Changes.

Analyze the AI Developer agent's generated diff for correctness,
syntactic validity, and clean application to the target file.
"""

from typing import Optional

from labs.templates.exercise_base import Exercise
from labs.modules.modifying_applications.diff_validator import (
    validate_diff_format,
    apply_diff,
    check_syntax,
    DiffValidationResult,
)


class ReviewChangesExercise(Exercise):
    """Review the AI Developer agent's proposed code changes."""

    @property
    def exercise_id(self) -> str:
        return "02_review_changes"

    @property
    def name(self) -> str:
        return "Review Proposed Changes"

    @property
    def description(self) -> str:
        return (
            "Analyze the generated diff for correctness, syntactic validity, "
            "and clean application to the target file. Confirm the diff "
            "applies without merge conflicts and contains valid code."
        )

    @property
    def timeout_minutes(self) -> int:
        return 10

    @property
    def prerequisites(self) -> list[str]:
        return ["01_invoke_agent"]

    def setup(self) -> None:
        """No setup required for review exercise."""
        pass

    def execute(self, submission: dict) -> dict:
        """Review the proposed diff against the original file content.

        Args:
            submission: Dict with keys:
                - original_content: The original source file content
                - diff_text: The unified diff produced by the AI Developer agent
                - language: Programming language of the target file (default: python)

        Returns:
            Dict with review results including format, apply, and syntax checks.
        """
        original_content = submission.get("original_content", "")
        diff_text = submission.get("diff_text", "")
        language = submission.get("language", "python")

        if not original_content:
            return {
                "status": "error",
                "message": "Field 'original_content' is required.",
                "format_valid": False,
                "applies_cleanly": False,
                "syntax_valid": False,
            }
        if not diff_text:
            return {
                "status": "error",
                "message": "Field 'diff_text' is required.",
                "format_valid": False,
                "applies_cleanly": False,
                "syntax_valid": False,
                "suggestion": "Re-invoke the AI Developer agent with a clearer prompt.",
            }

        # Step 1: Validate diff format
        format_errors = validate_diff_format(diff_text)
        if format_errors:
            suggestions = [e.suggestion for e in format_errors if e.suggestion]
            return {
                "status": "review_complete",
                "format_valid": False,
                "format_errors": [
                    {"category": e.category, "message": e.message}
                    for e in format_errors
                ],
                "applies_cleanly": False,
                "syntax_valid": False,
                "suggestion": suggestions[0] if suggestions else None,
            }

        # Step 2: Attempt to apply the diff
        apply_result = apply_diff(original_content, diff_text)
        if not apply_result.valid:
            suggestions = [e.suggestion for e in apply_result.errors if e.suggestion]
            return {
                "status": "review_complete",
                "format_valid": True,
                "applies_cleanly": False,
                "apply_errors": [
                    {"category": e.category, "message": e.message}
                    for e in apply_result.errors
                ],
                "syntax_valid": False,
                "suggestion": suggestions[0] if suggestions else None,
            }

        # Step 3: Check syntax of patched content
        patched_content = apply_result.patched_content or ""
        syntax_result = check_syntax(patched_content, language)
        if not syntax_result.valid:
            suggestions = [e.suggestion for e in syntax_result.errors if e.suggestion]
            return {
                "status": "review_complete",
                "format_valid": True,
                "applies_cleanly": True,
                "syntax_valid": False,
                "syntax_errors": [
                    {"category": e.category, "message": e.message}
                    for e in syntax_result.errors
                ],
                "patched_content": patched_content,
                "suggestion": suggestions[0] if suggestions else None,
            }

        return {
            "status": "review_complete",
            "format_valid": True,
            "applies_cleanly": True,
            "syntax_valid": True,
            "patched_content": patched_content,
            "suggestion": None,
        }

    def validate(self, result: dict) -> list[dict]:
        """Validate that the diff review passed all checks.

        Checks:
        1. Diff is in valid unified diff format
        2. Diff applies cleanly without merge conflicts
        3. Resulting code is syntactically correct
        """
        checks = []

        status = result.get("status", "unknown")
        if status == "error":
            message = result.get("message", "Unknown error")
            checks.append({
                "name": "review_input",
                "passed": False,
                "feedback": f"Review failed: {message}",
                "expected": "review_complete",
                "actual": "error",
            })
            return checks

        # Check 1: Diff format validity
        format_valid = result.get("format_valid", False)
        checks.append({
            "name": "diff_format",
            "passed": format_valid,
            "feedback": (
                "Diff is in valid unified diff format."
                if format_valid
                else "Diff is not in valid unified diff format."
            ),
            "expected": "valid unified diff",
            "actual": "valid" if format_valid else "invalid",
        })

        # Check 2: Clean application
        applies_cleanly = result.get("applies_cleanly", False)
        checks.append({
            "name": "clean_application",
            "passed": applies_cleanly,
            "feedback": (
                "Diff applies cleanly to the target file without merge conflicts."
                if applies_cleanly
                else "Diff does not apply cleanly - merge conflicts detected."
            ),
            "expected": "applies cleanly",
            "actual": "clean" if applies_cleanly else "conflicts",
        })

        # Check 3: Syntax correctness
        syntax_valid = result.get("syntax_valid", False)
        checks.append({
            "name": "syntax_correctness",
            "passed": syntax_valid,
            "feedback": (
                "Resulting code is syntactically correct."
                if syntax_valid
                else "Resulting code contains syntax errors."
            ),
            "expected": "syntactically correct",
            "actual": "valid" if syntax_valid else "syntax errors",
        })

        # If any check failed and there is a suggestion, add it
        suggestion = result.get("suggestion")
        if suggestion and not all(c["passed"] for c in checks):
            checks.append({
                "name": "alternative_suggestion",
                "passed": True,
                "feedback": f"Suggestion: {suggestion}",
            })

        return checks

    def teardown(self) -> None:
        """No cleanup needed for review exercise."""
        pass

    def get_hints(self) -> list[str]:
        return [
            "A valid unified diff must contain '---', '+++', and '@@' markers.",
            "The diff must reference the correct line numbers in the original file.",
            "If the diff doesn't apply cleanly, the line context may have changed.",
            "Syntax errors in the patched code indicate the AI agent made a mistake.",
        ]

    def get_instructions(self) -> Optional[str]:
        return (
            "Review the AI Developer agent's proposed changes:\n\n"
            "1. Examine the unified diff produced by the agent\n"
            "2. Verify it references the correct file and line numbers\n"
            "3. Check that the changes match your modification request\n"
            "4. The validator will automatically check:\n"
            "   - Diff format is valid unified diff\n"
            "   - Diff applies cleanly to the original file\n"
            "   - Resulting code is syntactically correct\n\n"
            "If validation fails, the system will suggest alternative prompts\n"
            "to try with the AI Developer agent."
        )

"""Assessment engine for evaluating exercise submissions."""

from labs.core.models import AssessmentResult, CheckResult


class AssessmentEngine:
    """Evaluates exercise submissions against expected outcomes.

    The engine compares a submission dict against an expected dict,
    producing per-check results and an overall pass/fail status.
    """

    def evaluate(
        self, exercise_id: str, submission: dict, expected: dict
    ) -> AssessmentResult:
        """Run all checks for an exercise.

        Compares each key in `expected` against the corresponding value
        in `submission`. Returns pass/fail with per-check details.

        Args:
            exercise_id: Identifier for the exercise being assessed.
            submission: The learner's submitted key-value results.
            expected: The expected key-value outcomes to check against.

        Returns:
            AssessmentResult with overall status, list of checks, and feedback.
        """
        checks: list[CheckResult] = []

        for check_name, expected_value in expected.items():
            actual_value = submission.get(check_name)
            passed = actual_value == expected_value

            if passed:
                feedback = f"Check '{check_name}' passed."
            else:
                feedback = (
                    f"Check '{check_name}' failed: "
                    f"expected {expected_value!r}, got {actual_value!r}."
                )

            checks.append(
                CheckResult(
                    name=check_name,
                    passed=passed,
                    feedback=feedback,
                    expected=repr(expected_value),
                    actual=repr(actual_value),
                )
            )

        # If expected was empty, add a structural check to ensure non-empty checks
        if not checks:
            checks.append(
                CheckResult(
                    name="submission_received",
                    passed=True,
                    feedback=f"Exercise '{exercise_id}' submission received (no specific checks defined).",
                )
            )

        all_passed = all(check.passed for check in checks)
        status = "pass" if all_passed else "fail"

        if all_passed:
            feedback_summary = (
                f"Exercise '{exercise_id}': All {len(checks)} check(s) passed."
            )
        else:
            failed_names = [c.name for c in checks if not c.passed]
            feedback_summary = (
                f"Exercise '{exercise_id}': {len(failed_names)} of {len(checks)} "
                f"check(s) failed — {', '.join(failed_names)}."
            )

        return AssessmentResult(
            status=status,
            checks=checks,
            feedback=feedback_summary,
        )

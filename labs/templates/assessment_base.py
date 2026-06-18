"""Base Assessment template class for module authors to extend.

Module authors create custom assessment strategies by subclassing
the Assessment abstract base class. This allows per-module or
per-exercise customization of how submissions are evaluated while
maintaining a consistent interface with the core AssessmentEngine.

Example usage:
    from labs.templates.assessment_base import Assessment

    class DockerHealthAssessment(Assessment):
        @property
        def assessment_id(self) -> str:
            return "docker_health_check"

        @property
        def name(self) -> str:
            return "Docker Service Health Assessment"

        @property
        def description(self) -> str:
            return "Verify all Docker services report healthy status."

        def define_checks(self, expected: dict) -> list[dict]:
            return [
                {"name": "flask_healthy", "type": "equality", "field": "flask_status"},
                {"name": "postgres_healthy", "type": "equality", "field": "pg_status"},
                {"name": "nginx_healthy", "type": "equality", "field": "nginx_status"},
            ]

        def evaluate_check(self, check: dict, submission: dict, expected: dict) -> dict:
            field = check["field"]
            actual = submission.get(field, "unknown")
            expected_val = expected.get(field, "healthy")
            passed = actual == expected_val
            return {
                "name": check["name"],
                "passed": passed,
                "feedback": f"{check['name']}: {'passed' if passed else 'failed'}",
                "expected": expected_val,
                "actual": actual,
            }

        def generate_feedback(self, check_results: list[dict]) -> str:
            passed = sum(1 for c in check_results if c["passed"])
            total = len(check_results)
            return f"{passed}/{total} services healthy."
"""

from abc import ABC, abstractmethod
from typing import Optional

from labs.core.models import AssessmentResult, CheckResult


class Assessment(ABC):
    """Abstract base class for custom assessment strategies.

    Module authors subclass this to define how exercise submissions
    are evaluated. The assessment lifecycle is: define_checks ->
    evaluate_check (per check) -> generate_feedback.

    The run() method orchestrates the full evaluation and returns
    an AssessmentResult compatible with the core framework.
    """

    @property
    @abstractmethod
    def assessment_id(self) -> str:
        """Unique identifier for this assessment."""
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable assessment name."""
        ...

    @property
    @abstractmethod
    def description(self) -> str:
        """Brief description of what this assessment evaluates."""
        ...

    @abstractmethod
    def define_checks(self, expected: dict) -> list[dict]:
        """Define the list of checks to perform.

        Args:
            expected: The expected outcomes for the exercise.

        Returns:
            A list of check specification dicts. Each dict should
            contain at minimum a 'name' key identifying the check.
            Additional keys are assessment-specific.
        """
        ...

    @abstractmethod
    def evaluate_check(
        self, check: dict, submission: dict, expected: dict
    ) -> dict:
        """Evaluate a single check against the submission.

        Args:
            check: A check specification dict from define_checks().
            submission: The learner's submitted data.
            expected: The expected outcomes for the exercise.

        Returns:
            A dict containing:
                - name (str): Check identifier
                - passed (bool): Whether the check passed
                - feedback (str): Human-readable feedback
                - expected (str, optional): Expected value
                - actual (str, optional): Actual value
        """
        ...

    @abstractmethod
    def generate_feedback(self, check_results: list[dict]) -> str:
        """Generate an overall feedback summary from check results.

        Args:
            check_results: List of result dicts from evaluate_check().

        Returns:
            A human-readable summary string for the learner.
        """
        ...

    def pre_evaluate(self, submission: dict, expected: dict) -> Optional[str]:
        """Optional pre-evaluation hook for early validation.

        Override to perform preliminary checks before running the
        full assessment (e.g., verify submission format).

        Args:
            submission: The learner's submitted data.
            expected: The expected outcomes.

        Returns:
            None if pre-evaluation passes, or an error message string
            if the submission should be rejected before evaluation.
        """
        return None

    def run(self, exercise_id: str, submission: dict, expected: dict) -> AssessmentResult:
        """Execute the full assessment and return a framework-compatible result.

        This method orchestrates the assessment lifecycle:
        1. pre_evaluate() — optional early rejection
        2. define_checks() — determine what to check
        3. evaluate_check() — evaluate each check
        4. generate_feedback() — produce summary

        Args:
            exercise_id: Identifier of the exercise being assessed.
            submission: The learner's submitted data.
            expected: The expected outcomes.

        Returns:
            AssessmentResult compatible with the core framework.
        """
        # Pre-evaluation hook
        pre_error = self.pre_evaluate(submission, expected)
        if pre_error is not None:
            return AssessmentResult(
                status="fail",
                checks=[
                    CheckResult(
                        name="pre_evaluation",
                        passed=False,
                        feedback=pre_error,
                    )
                ],
                feedback=pre_error,
            )

        # Define and run checks
        check_specs = self.define_checks(expected)
        check_results: list[dict] = []

        for check_spec in check_specs:
            result = self.evaluate_check(check_spec, submission, expected)
            check_results.append(result)

        # Convert to framework CheckResult objects
        checks = [
            CheckResult(
                name=r["name"],
                passed=r["passed"],
                feedback=r["feedback"],
                expected=r.get("expected"),
                actual=r.get("actual"),
            )
            for r in check_results
        ]

        # Ensure non-empty checks list
        if not checks:
            checks = [
                CheckResult(
                    name="assessment_complete",
                    passed=True,
                    feedback=f"Assessment '{self.assessment_id}' completed (no specific checks defined).",
                )
            ]

        all_passed = all(c.passed for c in checks)
        status = "pass" if all_passed else "fail"
        feedback = self.generate_feedback(check_results)

        return AssessmentResult(
            status=status,
            checks=checks,
            feedback=feedback,
        )

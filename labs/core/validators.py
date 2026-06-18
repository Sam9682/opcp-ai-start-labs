"""Exercise validation for the Lab Framework.

Validates individual exercise steps against JSON assertions,
supporting equality and containment checks.
"""

from typing import Protocol, Any, Optional

from labs.core.models import ValidationResult, ExerciseStatus


class PlatformClient(Protocol):
    """Protocol defining the interface for platform interactions.

    Concrete implementations will query the AI-Powered-Store platform
    to retrieve actual state for validation purposes.
    """

    def query(self, endpoint: str, params: Optional[dict] = None) -> dict:
        """Query the platform and return the response as a dict."""
        ...


class ExerciseValidator:
    """Validates individual exercise steps against JSON assertions.

    Supports two assertion types:
    - equality: actual value must equal expected value
    - containment: actual value must contain expected substring
    """

    def __init__(self, platform_client: PlatformClient) -> None:
        self.platform_client = platform_client

    def validate_step(self, step: dict, assertion: dict) -> ValidationResult:
        """Check a single step against its expected outcome.

        Args:
            step: The step result containing at minimum an 'actual' value
                  or a 'name' identifying the step.
            assertion: A dict describing the expected outcome with keys:
                - type: "equality" or "containment"
                - expected: the expected value (or substring for containment)
                - field (optional): the field within step to check;
                  defaults to "actual"

        Returns:
            ValidationResult with pass/fail status and descriptive message.
        """
        step_name = step.get("name", "unnamed_step")
        assertion_type = assertion.get("type", "equality")
        expected = assertion.get("expected")
        field = assertion.get("field", "actual")
        actual = step.get(field)

        if assertion_type == "equality":
            passed = actual == expected
            if passed:
                message = f"Step '{step_name}': equality assertion passed."
            else:
                message = (
                    f"Step '{step_name}': equality assertion failed. "
                    f"Expected {expected!r}, got {actual!r}."
                )
        elif assertion_type == "containment":
            if actual is None or expected is None:
                passed = False
                message = (
                    f"Step '{step_name}': containment assertion failed. "
                    f"Actual or expected value is None."
                )
            else:
                actual_str = str(actual)
                expected_str = str(expected)
                passed = expected_str in actual_str
                if passed:
                    message = (
                        f"Step '{step_name}': containment assertion passed. "
                        f"Found {expected_str!r} in actual value."
                    )
                else:
                    message = (
                        f"Step '{step_name}': containment assertion failed. "
                        f"Expected {expected_str!r} to be contained in {actual_str!r}."
                    )
        else:
            passed = False
            message = (
                f"Step '{step_name}': unknown assertion type '{assertion_type}'."
            )

        return ValidationResult(
            step_name=step_name,
            passed=passed,
            message=message,
            details={
                "assertion_type": assertion_type,
                "expected": expected,
                "actual": actual,
            },
        )

    def validate_exercise(
        self, exercise_id: str, steps: list[dict]
    ) -> "ExerciseValidationResult":
        """Validate all steps in an exercise sequentially.

        Each step dict must contain at minimum:
        - The step data (with 'name' and 'actual' or other field)
        - An 'assertion' key containing the assertion dict

        Args:
            exercise_id: Identifier of the exercise being validated.
            steps: List of step dicts, each containing step data and
                   an 'assertion' key with the assertion specification.

        Returns:
            ExerciseValidationResult with overall pass/fail and per-step results.
        """
        results: list[ValidationResult] = []
        all_passed = True

        for step in steps:
            assertion = step.get("assertion", {})
            result = self.validate_step(step, assertion)
            results.append(result)
            if not result.passed:
                all_passed = False

        return ExerciseValidationResult(
            exercise_id=exercise_id,
            passed=all_passed,
            step_results=results,
        )


class ExerciseValidationResult:
    """Result of validating all steps in an exercise."""

    def __init__(
        self,
        exercise_id: str,
        passed: bool,
        step_results: list[ValidationResult],
    ) -> None:
        self.exercise_id = exercise_id
        self.passed = passed
        self.step_results = step_results

    @property
    def status(self) -> ExerciseStatus:
        """Return the exercise status based on validation outcome."""
        return ExerciseStatus.PASS if self.passed else ExerciseStatus.FAIL

    @property
    def summary(self) -> str:
        """Human-readable summary of validation results."""
        total = len(self.step_results)
        passed_count = sum(1 for r in self.step_results if r.passed)
        return (
            f"Exercise '{self.exercise_id}': {passed_count}/{total} steps passed."
        )

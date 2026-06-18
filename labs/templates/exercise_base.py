"""Base Exercise template class for module authors to extend.

Module authors create new lab exercises by subclassing the Exercise
abstract base class and implementing the required methods. This ensures
a consistent interface across all lab modules while allowing flexibility
in exercise-specific logic.

Example usage:
    from labs.templates.exercise_base import Exercise

    class SystemPrereqsExercise(Exercise):
        @property
        def exercise_id(self) -> str:
            return "01_system_prereqs"

        @property
        def name(self) -> str:
            return "System Prerequisites Verification"

        @property
        def description(self) -> str:
            return "Verify Ubuntu 22.04/24.04 and required packages."

        def setup(self) -> None:
            # Prepare the exercise environment
            pass

        def execute(self, submission: dict) -> dict:
            # Run the exercise logic
            return {"os_version": submission.get("os_version")}

        def validate(self, result: dict) -> list[dict]:
            checks = []
            checks.append({
                "name": "os_version_check",
                "passed": result.get("os_version") in ("22.04", "24.04"),
                "feedback": "OS version must be Ubuntu 22.04 or 24.04.",
            })
            return checks

        def teardown(self) -> None:
            # Clean up after the exercise
            pass
"""

from abc import ABC, abstractmethod
from typing import Optional


class Exercise(ABC):
    """Abstract base class for lab exercises.

    Module authors subclass this to define individual exercises within
    a lab module. Each exercise has a lifecycle: setup -> execute ->
    validate -> teardown.

    Attributes:
        exercise_id: Unique identifier for the exercise within its module.
        name: Human-readable name displayed to the learner.
        description: Brief description of the exercise objective.
    """

    @property
    @abstractmethod
    def exercise_id(self) -> str:
        """Unique identifier for this exercise within its module."""
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable exercise name."""
        ...

    @property
    @abstractmethod
    def description(self) -> str:
        """Brief description of the exercise objective."""
        ...

    @property
    def timeout_minutes(self) -> int:
        """Maximum time allowed for this exercise in minutes.

        Override to set a custom timeout. Defaults to 30 minutes.
        """
        return 30

    @property
    def prerequisites(self) -> list[str]:
        """List of exercise IDs that must be completed before this one.

        Override to specify intra-module exercise dependencies.
        Defaults to an empty list (no prerequisites).
        """
        return []

    @abstractmethod
    def setup(self) -> None:
        """Prepare the exercise environment.

        Called before execute(). Use this to provision resources,
        create files, or configure the container environment.

        Raises:
            RuntimeError: If setup fails and the exercise cannot proceed.
        """
        ...

    @abstractmethod
    def execute(self, submission: dict) -> dict:
        """Run the exercise logic with the learner's submission.

        Args:
            submission: Key-value data provided by the learner or
                        collected from the exercise environment.

        Returns:
            A dict containing the exercise result data to be validated.

        Raises:
            RuntimeError: If execution fails unexpectedly.
        """
        ...

    @abstractmethod
    def validate(self, result: dict) -> list[dict]:
        """Validate the exercise result against expected outcomes.

        Args:
            result: The dict returned by execute().

        Returns:
            A list of check dicts, each containing:
                - name (str): Check identifier
                - passed (bool): Whether the check passed
                - feedback (str): Human-readable feedback message
                - expected (str, optional): Expected value description
                - actual (str, optional): Actual value found
        """
        ...

    @abstractmethod
    def teardown(self) -> None:
        """Clean up after the exercise completes.

        Called after validate(), regardless of pass/fail outcome.
        Use this to remove temporary files, release resources, etc.
        """
        ...

    def get_hints(self) -> list[str]:
        """Return optional hints for learners who are stuck.

        Override to provide progressive hints. Defaults to no hints.
        """
        return []

    def get_instructions(self) -> Optional[str]:
        """Return detailed instructions displayed to the learner.

        Override to provide exercise-specific instructions beyond
        the description. Defaults to None (use description only).
        """
        return None

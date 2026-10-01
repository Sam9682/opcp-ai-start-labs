"""Exercise 3: Name the stopping criterion.

The learner identifies which stopping criterion ended the run and the step at
which it fired.
"""

import importlib
from typing import Optional

from labs.templates.exercise_base import Exercise

_trace = importlib.import_module(
    "labs.modules.trace-reading.setup.sample_trace"
)


class StoppingCriterionExercise(Exercise):
    """Identify the stopping criterion that ended the agent run."""

    @property
    def exercise_id(self) -> str:
        return "03_stopping_criterion"

    @property
    def name(self) -> str:
        return "Name the Stopping Criterion"

    @property
    def description(self) -> str:
        return (
            "Identify which stopping criterion ended the run and the step at "
            "which it fired."
        )

    @property
    def timeout_minutes(self) -> int:
        return 15

    def setup(self) -> None:
        pass

    def execute(self, submission: dict) -> dict:
        """Check the named stopping criterion and the firing step.

        Args:
            submission: Dict with keys:
                - stopping_criterion: Name/category of the criterion.
                - fired_at_step: Step id where the run halted.

        Returns:
            Dict describing correctness of the criterion and step.
        """
        criterion = str(
            submission.get("stopping_criterion", "")
        ).strip().lower().replace(" ", "_")
        fired_at = str(submission.get("fired_at_step", "")).strip().lower()

        criterion_ok = criterion in _trace.STOPPING_CRITERION_ALIASES
        step_ok = fired_at == _trace.GUARDRAIL_STEP_ID

        return {
            "submitted_criterion": criterion,
            "criterion_correct": criterion_ok,
            "canonical_criterion": _trace.STOPPING_CRITERION,
            "submitted_step": fired_at,
            "step_correct": step_ok,
            "canonical_step": _trace.GUARDRAIL_STEP_ID,
        }

    def validate(self, result: dict) -> list[dict]:
        checks = []

        checks.append({
            "name": "stopping_criterion_identified",
            "passed": result.get("criterion_correct", False),
            "feedback": (
                "Correct — the run stopped because the same error repeated "
                "three times (an error-threshold criterion)."
                if result.get("criterion_correct")
                else "Not quite. The agent hit the same failure repeatedly; "
                "which stopping-criterion category covers that?"
            ),
            "expected": result.get("canonical_criterion", ""),
            "actual": result.get("submitted_criterion", "") or "(none)",
        })

        checks.append({
            "name": "firing_step_identified",
            "passed": result.get("step_correct", False),
            "feedback": (
                "Correct — the run halted at the step where the guardrail "
                "tripped."
                if result.get("step_correct")
                else "The firing step is not correct. Find where the run was "
                "halted."
            ),
            "expected": result.get("canonical_step", ""),
            "actual": result.get("submitted_step", "") or "(none)",
        })

        return checks

    def teardown(self) -> None:
        pass

    def get_hints(self) -> list[str]:
        return [
            "The agent did not reach its goal, so it was not a 'goal achieved' "
            "stop.",
            "Look for a repeated, identical failure.",
            "The stopping-criteria lesson lists error threshold as a category.",
            "The firing step is the one that explicitly halts the run.",
        ]

    def get_instructions(self) -> Optional[str]:
        return (
            "Name the stopping criterion and where it fired:\n\n"
            "1. Review why the run ended.\n"
            "2. Submit the criterion and firing step:\n"
            "   {\n"
            '     "stopping_criterion": "error_threshold",\n'
            '     "fired_at_step": "s14"\n'
            "   }\n"
        )

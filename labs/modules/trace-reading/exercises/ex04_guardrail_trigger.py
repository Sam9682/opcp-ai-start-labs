"""Exercise 4: Spot the guardrail trigger.

The learner identifies the guardrail layer that fired and what action it
prevented, connecting the trace to the five-layer guardrail model.
"""

import importlib
from typing import Optional

from labs.templates.exercise_base import Exercise

_trace = importlib.import_module(
    "labs.modules.trace-reading.setup.sample_trace"
)


class GuardrailTriggerExercise(Exercise):
    """Identify the guardrail layer that fired and the action it prevented."""

    @property
    def exercise_id(self) -> str:
        return "04_guardrail_trigger"

    @property
    def name(self) -> str:
        return "Spot the Guardrail Trigger"

    @property
    def description(self) -> str:
        return (
            "Identify the guardrail layer that fired in the trace and the "
            "action it prevented the agent from taking."
        )

    @property
    def timeout_minutes(self) -> int:
        return 15

    def setup(self) -> None:
        pass

    def execute(self, submission: dict) -> dict:
        """Check the identified guardrail layer and prevented action.

        Args:
            submission: Dict with keys:
                - guardrail_layer: Which of the five guardrail layers fired.
                - prevented_action: What the guardrail stopped (free text;
                  must reference a further deploy/retry).

        Returns:
            Dict describing correctness.
        """
        layer = str(
            submission.get("guardrail_layer", "")
        ).strip().lower().replace(" ", "_")
        prevented = str(submission.get("prevented_action", "")).strip().lower()

        layer_ok = layer in _trace.GUARDRAIL_LAYER_ALIASES
        # The guardrail stopped another deploy/retry attempt.
        prevented_ok = (
            ("deploy" in prevented or "retry" in prevented
             or "attempt" in prevented)
            and len(prevented) >= 5
        )

        return {
            "submitted_layer": layer,
            "layer_correct": layer_ok,
            "canonical_layer": _trace.GUARDRAIL_LAYER,
            "prevented_action": prevented,
            "prevented_correct": prevented_ok,
        }

    def validate(self, result: dict) -> list[dict]:
        checks = []

        checks.append({
            "name": "guardrail_layer_identified",
            "passed": result.get("layer_correct", False),
            "feedback": (
                "Correct — an operational-limits guardrail (an error/retry "
                "ceiling) fired."
                if result.get("layer_correct")
                else "Not quite. A cap on repeated failures belongs to one of "
                "the five guardrail layers — which one bounds operational "
                "behavior like retries and iterations?"
            ),
            "expected": result.get("canonical_layer", ""),
            "actual": result.get("submitted_layer", "") or "(none)",
        })

        checks.append({
            "name": "prevented_action_identified",
            "passed": result.get("prevented_correct", False),
            "feedback": (
                "Correct — the guardrail prevented another deploy/retry "
                "attempt."
                if result.get("prevented_correct")
                else "Describe what the guardrail stopped. It blocked a "
                "further action the agent was about to repeat."
            ),
            "expected": "prevented a further deploy/retry attempt",
            "actual": result.get("prevented_action", "") or "(none)",
        })

        return checks

    def teardown(self) -> None:
        pass

    def get_hints(self) -> list[str]:
        return [
            "The five guardrail layers: permissions, operational limits, human "
            "approval, observability, kill switch.",
            "A cap on repeated errors or retries is an operational limit.",
            "Ask what the agent would have done next if the guardrail had not "
            "fired.",
            "The final observe step states what was halted.",
        ]

    def get_instructions(self) -> Optional[str]:
        return (
            "Spot the guardrail that fired:\n\n"
            "1. Find the step where the run was halted.\n"
            "2. Submit the guardrail layer and the action it prevented:\n"
            "   {\n"
            '     "guardrail_layer": "operational_limits",\n'
            '     "prevented_action": "another deploy_app retry"\n'
            "   }\n"
        )

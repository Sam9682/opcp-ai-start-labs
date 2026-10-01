"""Exercise 1: Label the loop phases.

The learner annotates each trace step as "think", "act", or "observe". The
exercise scores the annotation against the trace's phase key.
"""

import importlib
from typing import Optional

from labs.templates.exercise_base import Exercise

_trace = importlib.import_module(
    "labs.modules.trace-reading.setup.sample_trace"
)

VALID_PHASES = {"think", "act", "observe"}


class LabelPhasesExercise(Exercise):
    """Annotate each trace step with its Think/Act/Observe phase."""

    @property
    def exercise_id(self) -> str:
        return "01_label_phases"

    @property
    def name(self) -> str:
        return "Label the Loop Phases"

    @property
    def description(self) -> str:
        return (
            "Annotate each step of the agent execution trace as think, act, "
            "or observe to show you can read the Think → Act → Observe loop."
        )

    @property
    def timeout_minutes(self) -> int:
        return 20

    def setup(self) -> None:
        pass

    def execute(self, submission: dict) -> dict:
        """Score the learner's per-step phase labels.

        Args:
            submission: Dict with key:
                - labels: Dict of {step_id: phase_label}.

        Returns:
            Dict describing correct/incorrect labels and coverage.
        """
        labels = submission.get("labels", {}) or {}
        key = _trace.phase_key()

        normalized = {
            sid: str(v).strip().lower() for sid, v in labels.items()
        }
        invalid = {
            sid: v for sid, v in normalized.items() if v not in VALID_PHASES
        }
        missing = [sid for sid in key if sid not in normalized]
        correct = {
            sid for sid, v in normalized.items()
            if sid in key and v == key[sid]
        }
        incorrect = {
            sid: {"got": normalized[sid], "expected": key[sid]}
            for sid in key
            if sid in normalized and normalized[sid] != key[sid]
        }

        return {
            "total_steps": len(key),
            "num_correct": len(correct),
            "invalid_labels": invalid,
            "missing_steps": missing,
            "incorrect": incorrect,
        }

    def validate(self, result: dict) -> list[dict]:
        checks = []

        invalid = result.get("invalid_labels", {})
        checks.append({
            "name": "labels_are_valid",
            "passed": len(invalid) == 0,
            "feedback": (
                "All labels use think/act/observe."
                if not invalid
                else f"Invalid labels on steps: {', '.join(invalid)}. "
                "Use only think, act, or observe."
            ),
            "expected": "think | act | observe",
            "actual": ", ".join(invalid) if invalid else "all valid",
        })

        missing = result.get("missing_steps", [])
        checks.append({
            "name": "all_steps_labeled",
            "passed": len(missing) == 0,
            "feedback": (
                "Every step was labeled."
                if not missing
                else f"Missing labels for steps: {', '.join(missing)}"
            ),
            "expected": "all steps labeled",
            "actual": f"{len(missing)} missing",
        })

        total = result.get("total_steps", 0)
        correct = result.get("num_correct", 0)
        checks.append({
            "name": "all_phases_correct",
            "passed": total > 0 and correct == total,
            "feedback": (
                f"All {total} phase labels correct."
                if correct == total
                else f"{correct}/{total} phase labels correct. Review the "
                "incorrect steps and the Think → Act → Observe lesson."
            ),
            "expected": f"{total}/{total} correct",
            "actual": f"{correct}/{total} correct",
        })

        return checks

    def teardown(self) -> None:
        pass

    def get_hints(self) -> list[str]:
        return [
            "A 'think' step is the agent reasoning about what to do next.",
            "An 'act' step is a tool call (e.g. list_apps, deploy_app).",
            "An 'observe' step records the result of a tool call or an event.",
            "A guardrail firing is an observed event, not an action by the agent.",
        ]

    def get_instructions(self) -> Optional[str]:
        return (
            "Label every step of the trace:\n\n"
            "1. Read each step in setup/sample_trace.py (learner_view()).\n"
            "2. Submit a label for each step id:\n"
            "   {\n"
            '     "labels": {"s1": "think", "s2": "act", "s3": "observe", ...}\n'
            "   }\n"
            "3. Use only think, act, or observe. Every step must be labeled."
        )

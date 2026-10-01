"""Exercise 2: Identify the tools.

The learner lists the opcp-explorer tools the agent invoked, in order. The
exercise checks the ordered list against the trace.
"""

import importlib
from typing import Optional

from labs.templates.exercise_base import Exercise

_trace = importlib.import_module(
    "labs.modules.trace-reading.setup.sample_trace"
)


class IdentifyToolsExercise(Exercise):
    """Identify the ordered sequence of tools the agent invoked."""

    @property
    def exercise_id(self) -> str:
        return "02_identify_tools"

    @property
    def name(self) -> str:
        return "Identify the Tools"

    @property
    def description(self) -> str:
        return (
            "List the opcp-explorer tools the agent invoked, in the order they "
            "appear in the trace."
        )

    @property
    def timeout_minutes(self) -> int:
        return 15

    def setup(self) -> None:
        pass

    def execute(self, submission: dict) -> dict:
        """Compare the learner's ordered tool list to the trace.

        Args:
            submission: Dict with keys:
                - tools_in_order: List of tool names in invocation order.

        Returns:
            Dict describing exact-order and set correctness.
        """
        submitted = [
            str(t).strip() for t in submission.get("tools_in_order", []) or []
        ]
        expected_order = _trace.tools_in_order()
        expected_distinct = _trace.distinct_tools()

        return {
            "submitted": submitted,
            "expected_order": expected_order,
            "order_matches": submitted == expected_order,
            "distinct_matches": set(submitted) == expected_distinct,
            "expected_distinct": sorted(expected_distinct),
        }

    def validate(self, result: dict) -> list[dict]:
        checks = []

        distinct_ok = result.get("distinct_matches", False)
        checks.append({
            "name": "all_tools_identified",
            "passed": distinct_ok,
            "feedback": (
                "You identified exactly the tools the agent used."
                if distinct_ok
                else "The set of tools is not correct. Expected: "
                + ", ".join(result.get("expected_distinct", []))
            ),
            "expected": ", ".join(result.get("expected_distinct", [])),
            "actual": ", ".join(sorted(set(result.get("submitted", [])))),
        })

        order_ok = result.get("order_matches", False)
        checks.append({
            "name": "tools_in_correct_order",
            "passed": order_ok,
            "feedback": (
                "The invocation order matches the trace, including the "
                "repeated deploy_app retries."
                if order_ok
                else "The order (with repeats) does not match. The agent "
                "retried the failing call several times."
            ),
            "expected": " → ".join(result.get("expected_order", [])),
            "actual": " → ".join(result.get("submitted", [])),
        })

        return checks

    def teardown(self) -> None:
        pass

    def get_hints(self) -> list[str]:
        return [
            "Only 'act' steps invoke tools.",
            "List the tools in the exact order they appear.",
            "The agent retried a failing tool — include each repeat.",
            "Observed events (like a guardrail firing) are not tool calls.",
        ]

    def get_instructions(self) -> Optional[str]:
        return (
            "List the tools the agent invoked, in order:\n\n"
            "1. Scan the trace for act steps.\n"
            "2. Submit the tool names in invocation order, including repeats:\n"
            "   {\n"
            '     "tools_in_order": ["list_apps", "deploy_app", "deploy_app", '
            '"deploy_app"]\n'
            "   }\n"
        )

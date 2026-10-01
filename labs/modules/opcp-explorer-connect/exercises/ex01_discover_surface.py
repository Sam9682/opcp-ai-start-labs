"""Exercise 1: Discover the opcp-explorer tool surface.

Enumerate the operations opcp-explorer exposes to an agent across its three
interfaces (API, CLI, MCP). The learner selects an interface and the set of
tools their agent will use; the exercise validates the selection against the
simulated platform surface.
"""

import importlib
from typing import Optional

from labs.templates.exercise_base import Exercise

# The module directory name contains hyphens, which are not valid in a dotted
# import path for `from ... import`. Load the sibling setup fixture with
# importlib using the literal (hyphenated) package path instead.
_sim = importlib.import_module(
    "labs.modules.opcp-explorer-connect.setup.simulated_platform"
)


class DiscoverSurfaceExercise(Exercise):
    """Discover and select tools from the opcp-explorer surface."""

    @property
    def exercise_id(self) -> str:
        return "01_discover_surface"

    @property
    def name(self) -> str:
        return "Discover the Tool Surface"

    @property
    def description(self) -> str:
        return (
            "Enumerate the API/CLI/MCP operations opcp-explorer exposes as "
            "agent tools and select the interface and tools your agent will use."
        )

    @property
    def timeout_minutes(self) -> int:
        return 15

    def setup(self) -> None:
        """No provisioning needed; the surface is a static fixture."""
        pass

    def execute(self, submission: dict) -> dict:
        """Resolve the chosen interface and selected tools.

        Args:
            submission: Dict with keys:
                - interface: One of "api", "cli", "mcp".
                - selected_tools: List of tool names the agent will use.

        Returns:
            Dict describing the resolved selection against the surface.
        """
        interface = submission.get("interface", "")
        selected = submission.get("selected_tools", []) or []

        available = _sim.list_tools()
        unknown = [t for t in selected if t not in available]
        resolved = []
        for name in selected:
            tool = _sim.get_tool(name)
            if tool is not None:
                resolved.append({
                    "name": name,
                    "invocation": tool.get(interface),
                    "required_scopes": tool.get("required_scopes", []),
                })

        return {
            "status": "resolved",
            "interface": interface,
            "available_tools": available,
            "selected_tools": selected,
            "unknown_tools": unknown,
            "resolved": resolved,
        }

    def validate(self, result: dict) -> list[dict]:
        """Validate the interface choice and tool selection."""
        checks = []

        interface = result.get("interface", "")
        checks.append({
            "name": "valid_interface",
            "passed": interface in _sim.INTERFACES,
            "feedback": (
                f"Interface '{interface}' is valid."
                if interface in _sim.INTERFACES
                else f"Interface must be one of {', '.join(_sim.INTERFACES)}."
            ),
            "expected": " | ".join(_sim.INTERFACES),
            "actual": interface or "(none)",
        })

        selected = result.get("selected_tools", [])
        checks.append({
            "name": "selected_at_least_one_tool",
            "passed": len(selected) >= 1,
            "feedback": (
                "At least one tool selected."
                if selected
                else "Select at least one tool from the surface."
            ),
            "expected": ">= 1 tool",
            "actual": str(len(selected)),
        })

        unknown = result.get("unknown_tools", [])
        checks.append({
            "name": "no_unknown_tools",
            "passed": len(unknown) == 0,
            "feedback": (
                "All selected tools exist on the platform surface."
                if not unknown
                else f"Unknown tools selected: {', '.join(unknown)}"
            ),
            "expected": "all tools known",
            "actual": ", ".join(unknown) if unknown else "none",
        })

        # Every resolved tool must have a concrete invocation for the interface.
        resolved = result.get("resolved", [])
        missing_invocation = [
            r["name"] for r in resolved if not r.get("invocation")
        ]
        checks.append({
            "name": "invocations_resolved",
            "passed": len(resolved) > 0 and not missing_invocation,
            "feedback": (
                "Every selected tool resolved to an invocation for the "
                "chosen interface."
                if resolved and not missing_invocation
                else "Some tools have no invocation for the chosen interface: "
                + ", ".join(missing_invocation)
            ),
            "expected": "invocation for each tool",
            "actual": (
                "all resolved" if not missing_invocation else
                ", ".join(missing_invocation)
            ),
        })

        return checks

    def teardown(self) -> None:
        pass

    def get_hints(self) -> list[str]:
        return [
            "opcp-explorer exposes the same operations across API, CLI, and MCP.",
            "A deploy agent typically needs list_apps, deploy_app, start_app, "
            "and app_status.",
            "Pick exactly one interface for the agent's tool calls.",
            "Tool names must match the platform surface exactly.",
        ]

    def get_instructions(self) -> Optional[str]:
        return (
            "Discover the opcp-explorer tool surface and choose your agent's "
            "tools:\n\n"
            "1. The platform exposes operations across three interfaces: "
            "api, cli, mcp.\n"
            "2. Submit the interface your agent will use and the tools it needs:\n"
            "   {\n"
            '     "interface": "api",\n'
            '     "selected_tools": ["list_apps", "deploy_app", "app_status"]\n'
            "   }\n"
            "3. Every selected tool must exist on the surface and resolve to a "
            "concrete invocation for your chosen interface."
        )

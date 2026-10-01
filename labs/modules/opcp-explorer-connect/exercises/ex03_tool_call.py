"""Exercise 3: Perform a basic tool call.

Build and execute a basic opcp-explorer operation (list or deploy) and read
the result. In simulated mode the call is served by the built-in fixture; in
live mode the exercise validates the call is well-formed and marks it for
out-of-container execution via the app/adapter layer.
"""

import importlib
from typing import Optional

from labs.templates.exercise_base import Exercise

_sim = importlib.import_module(
    "labs.modules.opcp-explorer-connect.setup.simulated_platform"
)


class ToolCallExercise(Exercise):
    """Construct and run a basic opcp-explorer tool call."""

    @property
    def exercise_id(self) -> str:
        return "03_tool_call"

    @property
    def name(self) -> str:
        return "Perform a Basic Tool Call"

    @property
    def description(self) -> str:
        return (
            "Build an opcp-explorer tool call (e.g. list_apps or deploy_app), "
            "execute it against the simulated platform, and read the result. "
            "Opt into live_mode to target a running instance."
        )

    @property
    def timeout_minutes(self) -> int:
        return 20

    def setup(self) -> None:
        pass

    def execute(self, submission: dict) -> dict:
        """Build the tool call and resolve its result.

        Args:
            submission: Dict with keys:
                - tool: Tool name (must exist on the surface).
                - interface: One of "api", "cli", "mcp".
                - params: Dict of parameters for the tool.
                - live_mode: Optional bool (default False).
                - base_url: Required only when live_mode is True.

        Returns:
            Dict with the constructed request and, in simulated mode, the
            simulated response. In live mode, the request is marked for
            out-of-container execution instead of being run here.
        """
        tool_name = submission.get("tool", "")
        interface = submission.get("interface", "")
        params = submission.get("params", {}) or {}
        live_mode = bool(submission.get("live_mode", False))
        base_url = submission.get("base_url", "")

        tool = _sim.get_tool(tool_name)
        if tool is None:
            return {
                "status": "error",
                "message": f"Unknown tool '{tool_name}'.",
                "tool": tool_name,
                "interface": interface,
            }

        if interface not in _sim.INTERFACES:
            return {
                "status": "error",
                "message": f"Unknown interface '{interface}'.",
                "tool": tool_name,
                "interface": interface,
            }

        # Required params present?
        required_params = tool.get("params", [])
        missing_params = [p for p in required_params if not params.get(p)]

        request = {
            "tool": tool_name,
            "interface": interface,
            "invocation": tool.get(interface),
            "params": params,
        }

        if missing_params:
            return {
                "status": "error",
                "message": f"Missing params: {', '.join(missing_params)}",
                "request": request,
                "missing_params": missing_params,
            }

        if live_mode:
            # Container has no network; hand the call to the adapter layer.
            return {
                "status": "deferred_to_live_adapter",
                "request": request,
                "base_url": base_url,
                "response": None,
            }

        response = _sim.simulate_call(tool_name, params)
        return {
            "status": "executed",
            "request": request,
            "response": response,
        }

    def validate(self, result: dict) -> list[dict]:
        checks = []

        status = result.get("status", "")
        if status == "error":
            checks.append({
                "name": "tool_call_constructed",
                "passed": False,
                "feedback": f"Tool call invalid: {result.get('message', '')}",
                "expected": "executed | deferred_to_live_adapter",
                "actual": "error",
            })
            return checks

        request = result.get("request", {})
        checks.append({
            "name": "invocation_resolved",
            "passed": bool(request.get("invocation")),
            "feedback": (
                "The tool resolved to a concrete invocation."
                if request.get("invocation")
                else "No invocation resolved for the chosen interface."
            ),
            "expected": "non-empty invocation",
            "actual": str(request.get("invocation") or "(none)"),
        })

        if status == "deferred_to_live_adapter":
            base_url = result.get("base_url", "")
            ok = base_url.startswith(("http://", "https://"))
            checks.append({
                "name": "live_call_well_formed",
                "passed": ok,
                "feedback": (
                    "Live call is well-formed and deferred to the adapter "
                    "layer for out-of-container execution."
                    if ok
                    else "Live call needs a base_url starting with http(s)://."
                ),
                "expected": "http(s) base_url + deferred",
                "actual": base_url or "(none)",
            })
            return checks

        # Simulated execution path: a readable response must come back.
        response = result.get("response", {}) or {}
        checks.append({
            "name": "response_received",
            "passed": response.get("status") == "ok",
            "feedback": (
                "Received a successful response from the simulated platform."
                if response.get("status") == "ok"
                else f"Unexpected response status: {response.get('status')}"
            ),
            "expected": "status == ok",
            "actual": str(response.get("status")),
        })

        # The agent must be able to read a meaningful field from the result.
        readable = (
            "apps" in response
            or "state" in response
            or "health" in response
        )
        checks.append({
            "name": "result_is_readable",
            "passed": readable,
            "feedback": (
                "The response carries a field the agent can act on "
                "(apps/state/health)."
                if readable
                else "The response has no actionable field to observe."
            ),
            "expected": "apps | state | health present",
            "actual": ", ".join(response.keys()) if response else "(empty)",
        })

        return checks

    def teardown(self) -> None:
        pass

    def get_hints(self) -> list[str]:
        return [
            "Start simple: list_apps needs no params.",
            "deploy_app requires repo_url and app_name.",
            "The interface must match the one you discovered in exercise 1.",
            "In simulated mode the platform returns a canned but realistic "
            "response you can read.",
        ]

    def get_instructions(self) -> Optional[str]:
        return (
            "Perform a basic opcp-explorer tool call:\n\n"
            "1. Pick a tool and interface, and supply any required params:\n"
            "   {\n"
            '     "tool": "deploy_app",\n'
            '     "interface": "api",\n'
            '     "params": {"repo_url": "https://git/acme/app", '
            '"app_name": "acme"}\n'
            "   }\n"
            "2. In simulated mode the platform returns a response — observe "
            "its state/health fields.\n"
            "3. To target a running instance, set \"live_mode\": true and "
            "\"base_url\"; the call is deferred to the adapter layer because "
            "the exercise container has no network."
        )

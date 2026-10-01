"""Exercise 2: Authenticate with a scoped token.

Construct a least-privilege authentication context for the agent. The learner
provides a token reference (never a raw secret), the scopes the agent needs,
and — in live mode — the connection parameters. The exercise validates that the
requested scopes are known, cover the tools the agent will call, and follow the
principle of least privilege.
"""

import importlib
from typing import Optional

from labs.templates.exercise_base import Exercise

_sim = importlib.import_module(
    "labs.modules.opcp-explorer-connect.setup.simulated_platform"
)


class AuthenticateExercise(Exercise):
    """Build a scoped, least-privilege auth context for the agent."""

    @property
    def exercise_id(self) -> str:
        return "02_authenticate"

    @property
    def name(self) -> str:
        return "Authenticate with a Scoped Token"

    @property
    def description(self) -> str:
        return (
            "Construct a least-privilege authentication context for the agent "
            "using a token reference and the minimal set of scopes required by "
            "the tools it will call."
        )

    @property
    def timeout_minutes(self) -> int:
        return 15

    def setup(self) -> None:
        pass

    def _required_scopes_for(self, tools: list[str]) -> set:
        needed = set()
        for name in tools:
            tool = _sim.get_tool(name)
            if tool:
                needed.update(tool.get("required_scopes", []))
        return needed

    def execute(self, submission: dict) -> dict:
        """Build the authentication context.

        Args:
            submission: Dict with keys:
                - token_ref: Reference to a secret (env var / secret name),
                  NOT a raw token value.
                - requested_scopes: List of scope strings.
                - tools: Tools the agent intends to call (to check coverage).
                - live_mode: Optional bool (default False).
                - base_url: Required only when live_mode is True.

        Returns:
            Dict describing the resolved auth context.
        """
        token_ref = submission.get("token_ref", "")
        requested = set(submission.get("requested_scopes", []) or [])
        tools = submission.get("tools", []) or []
        live_mode = bool(submission.get("live_mode", False))
        base_url = submission.get("base_url", "")

        needed = self._required_scopes_for(tools)
        unknown_scopes = sorted(requested - _sim.KNOWN_SCOPES)
        missing_scopes = sorted(needed - requested)
        excess_scopes = sorted(requested - needed)

        # Detect a raw token mistakenly passed instead of a reference.
        looks_like_raw_secret = (
            len(token_ref) >= 20 and " " not in token_ref
            and not token_ref.isupper()
            and not token_ref.startswith(("env:", "secret:", "$"))
        )

        return {
            "status": "built",
            "token_ref": token_ref,
            "looks_like_raw_secret": looks_like_raw_secret,
            "requested_scopes": sorted(requested),
            "needed_scopes": sorted(needed),
            "unknown_scopes": unknown_scopes,
            "missing_scopes": missing_scopes,
            "excess_scopes": excess_scopes,
            "live_mode": live_mode,
            "base_url": base_url,
        }

    def validate(self, result: dict) -> list[dict]:
        checks = []

        token_ref = result.get("token_ref", "")
        checks.append({
            "name": "token_reference_present",
            "passed": bool(token_ref),
            "feedback": (
                "A token reference was provided."
                if token_ref
                else "Provide a token reference (env var or secret name)."
            ),
            "expected": "non-empty token_ref",
            "actual": token_ref or "(none)",
        })

        checks.append({
            "name": "no_raw_secret",
            "passed": not result.get("looks_like_raw_secret", False),
            "feedback": (
                "Token is passed by reference, not as a raw secret."
                if not result.get("looks_like_raw_secret", False)
                else "Do not pass a raw token value. Use a reference such as "
                "'env:OPCP_TOKEN' or 'secret:opcp-token'."
            ),
            "expected": "token reference",
            "actual": "raw-looking value" if result.get(
                "looks_like_raw_secret") else "reference",
        })

        unknown = result.get("unknown_scopes", [])
        checks.append({
            "name": "scopes_known",
            "passed": len(unknown) == 0,
            "feedback": (
                "All requested scopes are recognized by the platform."
                if not unknown
                else f"Unknown scopes requested: {', '.join(unknown)}"
            ),
            "expected": "all scopes known",
            "actual": ", ".join(unknown) if unknown else "none",
        })

        missing = result.get("missing_scopes", [])
        checks.append({
            "name": "scopes_cover_tools",
            "passed": len(missing) == 0,
            "feedback": (
                "Requested scopes cover every tool the agent will call."
                if not missing
                else f"Missing scopes for selected tools: {', '.join(missing)}"
            ),
            "expected": "coverage of all tool scopes",
            "actual": ", ".join(missing) if missing else "complete",
        })

        excess = result.get("excess_scopes", [])
        checks.append({
            "name": "least_privilege",
            "passed": len(excess) == 0,
            "feedback": (
                "No excess scopes — least privilege respected."
                if not excess
                else f"Excess scopes beyond what the tools need: "
                f"{', '.join(excess)}. Remove them for least privilege."
            ),
            "expected": "no scopes beyond tool needs",
            "actual": ", ".join(excess) if excess else "minimal",
        })

        # Live-mode connection parameters must be present and well-formed.
        if result.get("live_mode", False):
            base_url = result.get("base_url", "")
            ok = base_url.startswith(("http://", "https://"))
            checks.append({
                "name": "live_connection_params",
                "passed": ok,
                "feedback": (
                    "Live base_url is well-formed."
                    if ok
                    else "live_mode requires a base_url starting with http:// "
                    "or https://."
                ),
                "expected": "http(s) base_url",
                "actual": base_url or "(none)",
            })

        return checks

    def teardown(self) -> None:
        pass

    def get_hints(self) -> list[str]:
        return [
            "Pass the token by reference (e.g. 'env:OPCP_TOKEN'), never the "
            "raw value.",
            "Request exactly the scopes the selected tools require — no more.",
            "list_apps/app_status need apps:read; deploy needs apps:write and "
            "deploy:execute.",
            "In live mode, include a base_url like https://opcp.example.com.",
        ]

    def get_instructions(self) -> Optional[str]:
        return (
            "Build a least-privilege authentication context:\n\n"
            "1. Submit a token reference, the scopes you need, and the tools "
            "you will call:\n"
            "   {\n"
            '     "token_ref": "env:OPCP_TOKEN",\n'
            '     "requested_scopes": ["apps:read", "apps:write", '
            '"deploy:execute"],\n'
            '     "tools": ["list_apps", "deploy_app", "app_status"]\n'
            "   }\n"
            "2. For a live connection, also set \"live_mode\": true and "
            "\"base_url\": \"https://opcp.example.com\".\n"
            "3. The validator checks that scopes are known, cover your tools, "
            "and carry no excess privilege."
        )

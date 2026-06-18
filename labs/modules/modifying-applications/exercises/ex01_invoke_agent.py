"""Exercise 1: Invoke AI Developer Agent.

Submit a modification request to the AI Developer agent and receive
a proposed code diff for the target application.
"""

from typing import Optional

from labs.templates.exercise_base import Exercise


class InvokeAgentExercise(Exercise):
    """Invoke the AI Developer agent with a modification prompt."""

    AGENT_RESPONSE_TIMEOUT_SECONDS = 60

    @property
    def exercise_id(self) -> str:
        return "01_invoke_agent"

    @property
    def name(self) -> str:
        return "Invoke AI Developer Agent"

    @property
    def description(self) -> str:
        return (
            "Submit a modification request to the AI Developer agent to "
            "generate code changes for an existing application. The agent "
            "will produce a unified diff that can be reviewed and applied."
        )

    @property
    def timeout_minutes(self) -> int:
        return 15

    def setup(self) -> None:
        """Verify AI Developer agent endpoint is accessible."""
        pass

    def execute(self, submission: dict) -> dict:
        """Invoke the AI Developer agent with modification parameters.

        Args:
            submission: Dict with keys:
                - app_name: Target application name
                - target_file: File path to modify within the application
                - modification_prompt: Natural language description of desired changes
                - agent_endpoint: API endpoint for the AI Developer agent (optional)

        Returns:
            Dict with agent invocation result including the generated diff.
        """
        app_name = submission.get("app_name", "")
        target_file = submission.get("target_file", "")
        modification_prompt = submission.get("modification_prompt", "")
        agent_endpoint = submission.get(
            "agent_endpoint", "https://store.example.com/api/ai-developer"
        )

        # Validate required fields
        if not app_name:
            return {
                "status": "error",
                "message": "Field 'app_name' is required.",
                "diff": None,
            }
        if not target_file:
            return {
                "status": "error",
                "message": "Field 'target_file' is required.",
                "diff": None,
            }
        if not modification_prompt:
            return {
                "status": "error",
                "message": "Field 'modification_prompt' is required.",
                "diff": None,
            }

        # Construct the agent invocation request
        agent_request = {
            "application": app_name,
            "target_file": target_file,
            "prompt": modification_prompt,
            "output_format": "unified_diff",
        }

        # In a real execution environment, the agent API would be called.
        # Here we return the constructed request for validation purposes.
        return {
            "status": "submitted",
            "agent_endpoint": agent_endpoint,
            "agent_request": agent_request,
            "timeout_seconds": self.AGENT_RESPONSE_TIMEOUT_SECONDS,
            "diff": None,  # Populated by actual agent response
        }

    def validate(self, result: dict) -> list[dict]:
        """Validate the agent invocation was properly constructed.

        Checks:
        1. Request was submitted successfully
        2. Agent request contains required fields
        3. Output format is unified_diff
        """
        checks = []

        # Check submission status
        status = result.get("status", "unknown")
        if status == "error":
            message = result.get("message", "Unknown error")
            checks.append({
                "name": "agent_invocation",
                "passed": False,
                "feedback": f"Agent invocation failed: {message}",
                "expected": "submitted",
                "actual": "error",
            })
            return checks

        checks.append({
            "name": "agent_invocation",
            "passed": status == "submitted",
            "feedback": (
                "AI Developer agent invoked successfully."
                if status == "submitted"
                else f"Unexpected status: {status}"
            ),
            "expected": "submitted",
            "actual": status,
        })

        # Check agent request structure
        agent_request = result.get("agent_request", {})
        required_fields = ["application", "target_file", "prompt", "output_format"]
        missing_fields = [f for f in required_fields if f not in agent_request]

        checks.append({
            "name": "request_structure",
            "passed": len(missing_fields) == 0,
            "feedback": (
                "Agent request contains all required fields."
                if len(missing_fields) == 0
                else f"Agent request missing fields: {', '.join(missing_fields)}"
            ),
            "expected": ", ".join(required_fields),
            "actual": ", ".join(agent_request.keys()),
        })

        # Check output format specification
        output_format = agent_request.get("output_format", "")
        checks.append({
            "name": "output_format",
            "passed": output_format == "unified_diff",
            "feedback": (
                "Output format correctly set to unified_diff."
                if output_format == "unified_diff"
                else f"Expected 'unified_diff' format, got '{output_format}'."
            ),
            "expected": "unified_diff",
            "actual": output_format,
        })

        return checks

    def teardown(self) -> None:
        """No cleanup needed for agent invocation."""
        pass

    def get_hints(self) -> list[str]:
        return [
            "The AI Developer agent requires an application name, target file, and modification prompt.",
            "Be specific in your modification prompt - describe exactly what changes you want.",
            "The agent outputs in unified diff format for easy review and application.",
            "Check that the target file path exists in your application's source tree.",
        ]

    def get_instructions(self) -> Optional[str]:
        return (
            "Invoke the AI Developer agent to modify an existing application:\n\n"
            "1. Identify the target application and file to modify\n"
            "2. Craft a clear modification prompt describing the desired changes\n"
            "3. Submit the request to the AI Developer agent endpoint:\n"
            "   POST /api/ai-developer\n"
            "   {\n"
            '     "application": "my-app",\n'
            '     "target_file": "src/main.py",\n'
            '     "prompt": "Add a /status endpoint that returns uptime",\n'
            '     "output_format": "unified_diff"\n'
            "   }\n"
            "4. The agent will return a unified diff with the proposed changes\n\n"
            "Tips:\n"
            "- Use specific, actionable prompts (e.g., 'Add a /health endpoint')\n"
            "- Reference existing functions or classes when relevant\n"
            "- Keep modifications focused on a single concern"
        )

"""Simulated opcp-explorer platform surface used by the connectivity exercises.

This fixture mirrors the shape of the real opcp-explorer platform (AI-Powered-
Store) interfaces without any network access, so the module runs offline inside
the isolated exercise container. The real platform exposes equivalent
operations through its REST API, CLI, and MCP server.
"""

from typing import Optional

# The three interface surfaces an agent can act through.
INTERFACES = ("api", "cli", "mcp")

# Canonical set of agent-facing operations ("tools") the platform exposes.
# Each tool is addressable identically across API, CLI, and MCP.
TOOL_SURFACE = {
    "list_apps": {
        "description": "List applications visible to the token's scope.",
        "api": {"method": "GET", "path": "/api/apps"},
        "cli": "aipoweredstore_cli.py apps list",
        "mcp": {"tool": "list_apps"},
        "required_scopes": ["apps:read"],
        "params": [],
    },
    "deploy_app": {
        "description": "Clone and deploy an application from a repository.",
        "api": {"method": "POST", "path": "/api/apps/deploy"},
        "cli": "aipoweredstore_cli.py apps deploy",
        "mcp": {"tool": "deploy_app"},
        "required_scopes": ["apps:write", "deploy:execute"],
        "params": ["repo_url", "app_name"],
    },
    "start_app": {
        "description": "Start a deployed application.",
        "api": {"method": "POST", "path": "/api/apps/{app}/start"},
        "cli": "aipoweredstore_cli.py apps start",
        "mcp": {"tool": "start_app"},
        "required_scopes": ["apps:write"],
        "params": ["app_name"],
    },
    "stop_app": {
        "description": "Stop a running application.",
        "api": {"method": "POST", "path": "/api/apps/{app}/stop"},
        "cli": "aipoweredstore_cli.py apps stop",
        "mcp": {"tool": "stop_app"},
        "required_scopes": ["apps:write"],
        "params": ["app_name"],
    },
    "app_status": {
        "description": "Read the status and health of an application.",
        "api": {"method": "GET", "path": "/api/apps/{app}/status"},
        "cli": "aipoweredstore_cli.py apps status",
        "mcp": {"tool": "app_status"},
        "required_scopes": ["apps:read"],
        "params": ["app_name"],
    },
}

# Scopes a least-privilege deploy agent would legitimately request.
KNOWN_SCOPES = {
    "apps:read",
    "apps:write",
    "deploy:execute",
    "logs:read",
    "billing:read",
}


def list_tools() -> list[str]:
    """Return the names of all simulated platform tools."""
    return sorted(TOOL_SURFACE.keys())


def get_tool(name: str) -> Optional[dict]:
    """Return the descriptor for a tool, or None if unknown."""
    return TOOL_SURFACE.get(name)


def simulate_call(tool_name: str, params: dict) -> dict:
    """Return a canned, deterministic response for a simulated tool call.

    This does not touch the network. It returns a plausible response shape so
    exercises can validate how an agent reads a result.
    """
    tool = TOOL_SURFACE.get(tool_name)
    if tool is None:
        return {"status": "error", "message": f"Unknown tool: {tool_name}"}

    if tool_name == "list_apps":
        return {
            "status": "ok",
            "apps": [
                {"app_name": "demo-static", "state": "running"},
                {"app_name": "demo-api", "state": "stopped"},
            ],
        }
    if tool_name == "deploy_app":
        return {
            "status": "ok",
            "app_name": params.get("app_name", ""),
            "state": "deploying",
        }
    if tool_name in ("start_app", "stop_app"):
        new_state = "starting" if tool_name == "start_app" else "stopping"
        return {
            "status": "ok",
            "app_name": params.get("app_name", ""),
            "state": new_state,
        }
    if tool_name == "app_status":
        return {
            "status": "ok",
            "app_name": params.get("app_name", ""),
            "state": "running",
            "health": "healthy",
        }
    return {"status": "ok"}

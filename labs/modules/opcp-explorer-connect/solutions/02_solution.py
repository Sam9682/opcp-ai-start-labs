"""Reference solution for Exercise 2: Authenticate with a Scoped Token.

Least-privilege context for the deploy agent: a token reference (not a raw
secret) and exactly the scopes the selected tools require.
"""


def submission() -> dict:
    return {
        "token_ref": "env:OPCP_TOKEN",
        "requested_scopes": ["apps:read", "apps:write", "deploy:execute"],
        "tools": ["list_apps", "deploy_app", "start_app", "app_status"],
        "live_mode": False,
    }

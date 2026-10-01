"""Reference solution for Exercise 3: Perform a Basic Tool Call.

Deploy an application through the REST API in simulated mode and read the
returned state.
"""


def submission() -> dict:
    return {
        "tool": "deploy_app",
        "interface": "api",
        "params": {
            "repo_url": "https://github.com/training/demo-app",
            "app_name": "demo-app",
        },
        "live_mode": False,
    }

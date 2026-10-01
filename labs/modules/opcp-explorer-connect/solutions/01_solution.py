"""Reference solution for Exercise 1: Discover the Tool Surface.

A deploy-and-verify agent uses the REST API and needs to list, deploy, start,
and check the status of applications.
"""


def submission() -> dict:
    return {
        "interface": "api",
        "selected_tools": [
            "list_apps",
            "deploy_app",
            "start_app",
            "app_status",
        ],
    }

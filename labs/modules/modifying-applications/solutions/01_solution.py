"""Reference solution for Exercise 01: Invoke AI Developer Agent.

Demonstrates the correct approach to invoking the AI Developer agent
with a modification request for an existing application.
"""


def get_solution() -> dict:
    """Return the reference solution submission for invoking the AI Developer agent.

    Returns:
        A dict representing a valid submission that passes all checks.
    """
    return {
        "app_name": "my-training-app",
        "target_file": "src/main.py",
        "modification_prompt": "Add a /status endpoint that returns the application uptime in seconds",
        "agent_endpoint": "https://store.example.com/api/ai-developer",
    }


def get_expected_request() -> dict:
    """Return the expected agent request structure for reference.

    Returns:
        The agent request dict that should be constructed.
    """
    return {
        "application": "my-training-app",
        "target_file": "src/main.py",
        "prompt": "Add a /status endpoint that returns the application uptime in seconds",
        "output_format": "unified_diff",
    }


def get_example_diff() -> str:
    """Return an example diff that the agent might produce.

    Returns:
        A sample unified diff for reference.
    """
    return (
        "--- a/src/main.py\n"
        "+++ b/src/main.py\n"
        "@@ -1,5 +1,12 @@\n"
        "+import time\n"
        " from flask import Flask, jsonify\n"
        " \n"
        " app = Flask(__name__)\n"
        "+_start_time = time.time()\n"
        " \n"
        " @app.route('/health')\n"
        " def health():\n"
        "     return jsonify({'status': 'healthy'})\n"
        "+\n"
        "+@app.route('/status')\n"
        "+def status():\n"
        "+    uptime = int(time.time() - _start_time)\n"
        "+    return jsonify({'uptime_seconds': uptime})\n"
    )

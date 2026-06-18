"""Reference solution for Exercise 02: Review Proposed Changes.

Demonstrates the correct approach to reviewing an AI Developer agent's
proposed diff for format validity, clean application, and syntax correctness.
"""


def get_solution() -> dict:
    """Return the reference solution submission for reviewing changes.

    Returns:
        A dict representing a valid submission that passes all checks.
    """
    return {
        "original_content": get_original_file(),
        "diff_text": get_valid_diff(),
        "language": "python",
    }


def get_original_file() -> str:
    """Return the original file content used for the review exercise.

    Returns:
        The original source file content.
    """
    return (
        "from flask import Flask, jsonify\n"
        "\n"
        "app = Flask(__name__)\n"
        "\n"
        "@app.route('/health')\n"
        "def health():\n"
        "    return jsonify({'status': 'healthy'})\n"
    )


def get_valid_diff() -> str:
    """Return a valid unified diff that applies cleanly and is syntactically correct.

    Returns:
        A unified diff string.
    """
    return (
        "--- a/src/main.py\n"
        "+++ b/src/main.py\n"
        "@@ -1,7 +1,14 @@\n"
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


def get_expected_result() -> dict:
    """Return the expected review result for a valid diff.

    Returns:
        The expected result dict from the review exercise.
    """
    return {
        "status": "review_complete",
        "format_valid": True,
        "applies_cleanly": True,
        "syntax_valid": True,
        "suggestion": None,
    }

"""Reference solution for Exercise 03: Apply Modifications.

Demonstrates the correct approach to approving and applying an
AI-generated diff to the target application source code.
"""


def get_solution() -> dict:
    """Return the reference solution submission for applying modifications.

    Returns:
        A dict representing a valid submission that passes all checks.
    """
    return {
        "original_content": get_original_file(),
        "diff_text": get_valid_diff(),
        "target_file": "src/main.py",
        "language": "python",
        "approved": True,
    }


def get_original_file() -> str:
    """Return the original file content before modification.

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
    """Return the diff to apply.

    Returns:
        A unified diff string that applies cleanly.
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
    """Return the expected result after successful application.

    Returns:
        The expected result dict with applied status and modified content.
    """
    return {
        "status": "applied",
        "applied": True,
        "target_file": "src/main.py",
        "modified_content": (
            "import time\n"
            "from flask import Flask, jsonify\n"
            "\n"
            "app = Flask(__name__)\n"
            "_start_time = time.time()\n"
            "\n"
            "@app.route('/health')\n"
            "def health():\n"
            "    return jsonify({'status': 'healthy'})\n"
            "\n"
            "@app.route('/status')\n"
            "def status():\n"
            "    uptime = int(time.time() - _start_time)\n"
            "    return jsonify({'uptime_seconds': uptime})\n"
        ),
    }

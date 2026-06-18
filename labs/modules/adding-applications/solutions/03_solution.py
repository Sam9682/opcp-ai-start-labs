"""Reference solution for Exercise 3: Web Interface Application Registration.

Demonstrates the correct approach to registering an application
using the platform web interface.
"""


def get_solution() -> dict:
    """Return the reference solution submission for web registration.

    Returns:
        A dict representing a valid submission that passes all checks.
    """
    return {
        "name": "web-registered-app",
        "description": "Application registered via the web interface during lab exercise",
        "git_url": "https://github.com/training/web-app",
        "docker_image": "training/web-app:latest",
        "web_url": "https://store.example.com",
    }


def get_steps() -> list[str]:
    """Return the step-by-step instructions for web registration.

    Returns:
        List of steps the learner should follow.
    """
    return [
        "1. Open https://store.example.com in your browser",
        "2. Log in with your platform credentials",
        "3. Navigate to Applications in the sidebar menu",
        "4. Click 'Add New Application'",
        "5. Fill in the form:",
        "   - Name: web-registered-app",
        "   - Description: Application registered via the web interface during lab exercise",
        "   - Git URL: https://github.com/training/web-app",
        "   - Docker Image: training/web-app:latest",
        "6. Click 'Register' to submit the form",
        "7. Verify the application appears in the Applications list",
    ]

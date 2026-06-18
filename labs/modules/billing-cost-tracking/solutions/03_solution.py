"""Reference solution for Exercise 3: Set Budget Alerts.

Demonstrates the correct approach to configuring a budget alert
threshold and verifying that the alert triggers within 30 seconds
when simulated usage exceeds the threshold.
"""


def get_solution() -> dict:
    """Return the reference solution submission for setting budget alerts.

    Returns:
        A dict representing a valid submission that passes all checks.
    """
    return {
        "api_endpoint": "http://localhost:5000",
        "auth_token": "your-api-token",
        "alert_name": "lab-budget-alert",
        "threshold_amount": 50.00,
        "notification_email": "learner@example.com",
        "simulate_overage": True,
    }


def get_curl_commands() -> list[str]:
    """Return the curl commands for configuring and testing a budget alert.

    Returns:
        List of curl command strings for each step.
    """
    return [
        # Create the alert
        (
            "curl -X POST http://localhost:5000/api/billing/alerts "
            "-H 'Authorization: Bearer your-api-token' "
            "-H 'Content-Type: application/json' "
            "-d '{\"name\": \"lab-budget-alert\", "
            "\"threshold_amount\": 50.00, "
            "\"notification_email\": \"learner@example.com\"}'"
        ),
        # Simulate overage
        (
            "curl -X POST http://localhost:5000/api/billing/simulate-overage "
            "-H 'Authorization: Bearer your-api-token' "
            "-H 'Content-Type: application/json' "
            "-d '{\"alert_id\": \"<alert_id_from_step_1>\", \"amount\": 75.00}'"
        ),
        # Check alert status
        (
            "curl -X GET http://localhost:5000/api/billing/alerts/<alert_id>/status "
            "-H 'Authorization: Bearer your-api-token'"
        ),
    ]


def get_verification_steps() -> list[str]:
    """Return step-by-step instructions for budget alert verification.

    Returns:
        List of steps the learner should follow.
    """
    return [
        "1. Configure a budget alert with a threshold amount (e.g., $50.00)",
        "2. Set simulate_overage=True to trigger the alert test",
        "3. The system simulates usage at 1.5× the threshold ($75.00)",
        "4. Wait for the alert to trigger (polled every 2 seconds)",
        "5. Verify the alert triggers within 30 seconds",
        "6. If billing service is unavailable:",
        "   - Report the connection error",
        "   - Show last known alert state",
        "   - Include data age (time since last successful retrieval)",
    ]

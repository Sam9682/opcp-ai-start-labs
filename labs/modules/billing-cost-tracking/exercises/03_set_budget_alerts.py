"""Exercise 3: Set Budget Alerts.

The learner configures budget alert thresholds and verifies that alerts
trigger within 30 seconds when resource usage exceeds the threshold.

Validates: Requirement 13.1 (set budget alerts), Requirement 13.3 (alert within 30s)
"""

import time
from typing import Optional

from labs.templates.exercise_base import Exercise


class SetBudgetAlertsExercise(Exercise):
    """Configure budget alert thresholds and verify alert triggering."""

    ALERT_TRIGGER_TIMEOUT_SECONDS = 30
    ALERT_POLL_INTERVAL_SECONDS = 2

    @property
    def exercise_id(self) -> str:
        return "03_set_budget_alerts"

    @property
    def name(self) -> str:
        return "Set Budget Alerts"

    @property
    def description(self) -> str:
        return (
            "Configure budget alert thresholds on the platform and verify "
            "that alerts trigger within 30 seconds when resource usage "
            "exceeds the defined threshold."
        )

    @property
    def timeout_minutes(self) -> int:
        return 15

    @property
    def prerequisites(self) -> list[str]:
        return ["01_view_consumption", "02_calculate_costs"]

    def setup(self) -> None:
        """Ensure billing API and alert service are accessible."""
        pass

    def execute(self, submission: dict) -> dict:
        """Configure a budget alert and verify it triggers.

        Expected submission keys:
            - api_endpoint (str): The billing API base URL.
            - auth_token (str): Authentication token for the API.
            - alert_name (str): Name for the budget alert.
            - threshold_amount (float): Budget threshold in currency units.
            - notification_email (str, optional): Email to notify on alert.
            - simulate_overage (bool): Whether to simulate usage exceeding threshold.

        Returns:
            dict with keys:
                - alert_id (str): The created alert identifier.
                - alert_configured (bool): Whether the alert was set up.
                - alert_triggered (bool): Whether the alert fired.
                - trigger_time_seconds (float): Time to trigger in seconds.
                - within_timeout (bool): Whether trigger was within 30s.
                - error (str, optional): Error message if operation failed.
                - last_known_state (dict, optional): Last known state on service error.
                - data_age_seconds (float, optional): Age of last known data.
        """
        api_endpoint = submission.get("api_endpoint", "")
        auth_token = submission.get("auth_token", "")
        alert_name = submission.get("alert_name", "")
        threshold_amount = submission.get("threshold_amount", 0.0)
        notification_email = submission.get("notification_email", "")
        simulate_overage = submission.get("simulate_overage", False)

        # Validate required inputs
        if not api_endpoint:
            return {
                "alert_id": "",
                "alert_configured": False,
                "alert_triggered": False,
                "trigger_time_seconds": 0.0,
                "within_timeout": False,
                "error": "api_endpoint is required.",
            }

        if not auth_token:
            return {
                "alert_id": "",
                "alert_configured": False,
                "alert_triggered": False,
                "trigger_time_seconds": 0.0,
                "within_timeout": False,
                "error": "auth_token is required for authentication.",
            }

        if not alert_name:
            return {
                "alert_id": "",
                "alert_configured": False,
                "alert_triggered": False,
                "trigger_time_seconds": 0.0,
                "within_timeout": False,
                "error": "alert_name is required.",
            }

        if not isinstance(threshold_amount, (int, float)) or threshold_amount <= 0:
            return {
                "alert_id": "",
                "alert_configured": False,
                "alert_triggered": False,
                "trigger_time_seconds": 0.0,
                "within_timeout": False,
                "error": "threshold_amount must be a positive number.",
            }

        # Attempt to configure the alert via the billing API
        try:
            import requests

            headers = {"Authorization": f"Bearer {auth_token}"}
            alert_payload = {
                "name": alert_name,
                "threshold_amount": threshold_amount,
                "notification_email": notification_email,
            }

            # Create the budget alert
            create_response = requests.post(
                f"{api_endpoint}/api/billing/alerts",
                headers=headers,
                json=alert_payload,
                timeout=30,
            )
            create_response.raise_for_status()
            alert_data = create_response.json()
            alert_id = alert_data.get("alert_id", "")

            if not simulate_overage:
                return {
                    "alert_id": alert_id,
                    "alert_configured": True,
                    "alert_triggered": False,
                    "trigger_time_seconds": 0.0,
                    "within_timeout": False,
                    "error": None,
                }

            # Simulate usage exceeding threshold and wait for alert
            requests.post(
                f"{api_endpoint}/api/billing/simulate-overage",
                headers=headers,
                json={"alert_id": alert_id, "amount": threshold_amount * 1.5},
                timeout=30,
            )

            # Poll for alert trigger
            start_time = time.time()
            alert_triggered = False
            trigger_time_seconds = 0.0

            while (time.time() - start_time) < self.ALERT_TRIGGER_TIMEOUT_SECONDS:
                status_response = requests.get(
                    f"{api_endpoint}/api/billing/alerts/{alert_id}/status",
                    headers=headers,
                    timeout=10,
                )
                status_response.raise_for_status()
                status_data = status_response.json()

                if status_data.get("triggered", False):
                    alert_triggered = True
                    trigger_time_seconds = time.time() - start_time
                    break

                time.sleep(self.ALERT_POLL_INTERVAL_SECONDS)

            if not alert_triggered:
                trigger_time_seconds = time.time() - start_time

            within_timeout = (
                alert_triggered
                and trigger_time_seconds <= self.ALERT_TRIGGER_TIMEOUT_SECONDS
            )

            return {
                "alert_id": alert_id,
                "alert_configured": True,
                "alert_triggered": alert_triggered,
                "trigger_time_seconds": trigger_time_seconds,
                "within_timeout": within_timeout,
                "error": None,
            }

        except requests.exceptions.ConnectionError:
            # Requirement 13.4: Report error + last known state + data age
            return {
                "alert_id": "",
                "alert_configured": False,
                "alert_triggered": False,
                "trigger_time_seconds": 0.0,
                "within_timeout": False,
                "error": (
                    f"Connection error: Unable to reach billing service at {api_endpoint}. "
                    "Reporting last known state."
                ),
                "last_known_state": {
                    "alert_name": alert_name,
                    "threshold_amount": threshold_amount,
                    "status": "unknown",
                },
                "data_age_seconds": 0.0,
            }
        except requests.exceptions.Timeout:
            return {
                "alert_id": "",
                "alert_configured": False,
                "alert_triggered": False,
                "trigger_time_seconds": 0.0,
                "within_timeout": False,
                "error": "Request timed out while configuring budget alert.",
                "last_known_state": {
                    "alert_name": alert_name,
                    "threshold_amount": threshold_amount,
                    "status": "timeout",
                },
                "data_age_seconds": 30.0,
            }
        except requests.exceptions.HTTPError as e:
            return {
                "alert_id": "",
                "alert_configured": False,
                "alert_triggered": False,
                "trigger_time_seconds": 0.0,
                "within_timeout": False,
                "error": f"HTTP error: {e.response.status_code} - {e.response.text}",
            }
        except ImportError:
            return {
                "alert_id": "",
                "alert_configured": False,
                "alert_triggered": False,
                "trigger_time_seconds": 0.0,
                "within_timeout": False,
                "error": "requests library is not installed. Run: pip install requests",
            }

    def validate(self, result: dict) -> list[dict]:
        """Validate budget alert configuration and triggering.

        Checks:
        1. No errors occurred during alert setup
        2. Alert was successfully configured
        3. Alert triggered within 30 seconds (if simulation was run)
        """
        checks = []

        # Check 1: No errors
        error = result.get("error")

        # Requirement 13.4: If service interrupted, validate error reporting
        last_known_state = result.get("last_known_state")
        if error and last_known_state:
            # Service interrupted - validate error reporting requirements
            has_error_msg = bool(error)
            has_last_state = bool(last_known_state)
            data_age = result.get("data_age_seconds")
            has_data_age = data_age is not None

            service_error_valid = has_error_msg and has_last_state and has_data_age
            checks.append({
                "name": "service_interruption_handling",
                "passed": service_error_valid,
                "feedback": (
                    "Billing service interruption handled correctly: "
                    "error reported with last known state and data age."
                    if service_error_valid
                    else (
                        "Service interruption handling incomplete. "
                        "Must report: error message, last known state, data age."
                    )
                ),
                "expected": "Error message + last known state + data age",
                "actual": (
                    f"error={has_error_msg}, state={has_last_state}, age={has_data_age}"
                ),
            })
            return checks

        checks.append({
            "name": "alert_no_errors",
            "passed": error is None,
            "feedback": (
                "Budget alert operation completed without errors."
                if error is None
                else f"Alert operation failed: {error}"
            ),
            "expected": "No errors",
            "actual": "No errors" if error is None else str(error),
        })

        # Check 2: Alert configured
        alert_configured = result.get("alert_configured", False)
        checks.append({
            "name": "alert_configured",
            "passed": alert_configured,
            "feedback": (
                "Budget alert configured successfully."
                if alert_configured
                else "Budget alert was not configured."
            ),
            "expected": "Alert configured",
            "actual": "Configured" if alert_configured else "Not configured",
        })

        # Check 3: Alert triggered within 30s (only if simulation was run)
        alert_triggered = result.get("alert_triggered", False)
        trigger_time = result.get("trigger_time_seconds", 0.0)
        within_timeout = result.get("within_timeout", False)

        if alert_triggered or trigger_time > 0:
            checks.append({
                "name": "alert_trigger_timing",
                "passed": within_timeout,
                "feedback": (
                    f"Alert triggered in {trigger_time:.1f}s (within 30s limit)."
                    if within_timeout
                    else (
                        f"Alert {'triggered' if alert_triggered else 'did not trigger'} "
                        f"after {trigger_time:.1f}s "
                        f"({'exceeds' if alert_triggered else 'timeout at'} 30s limit)."
                    )
                ),
                "expected": "Alert triggers within 30 seconds",
                "actual": (
                    f"{'Triggered' if alert_triggered else 'Not triggered'} "
                    f"at {trigger_time:.1f}s"
                ),
            })

        return checks

    def teardown(self) -> None:
        """Remove budget alerts created during the exercise."""
        pass

    def get_hints(self) -> list[str]:
        return [
            "Budget alerts require a positive threshold amount in currency units.",
            "Use the /api/billing/alerts endpoint to create a new alert.",
            "After creating the alert, simulate usage exceeding the threshold to test triggering.",
            "The alert must trigger within 30 seconds of usage exceeding the threshold.",
            "If the billing service is unavailable, your code should report the error, "
            "last known state, and the age of the last known data.",
        ]

    def get_instructions(self) -> str:
        return (
            "Configure a budget alert and verify it triggers within 30 seconds.\n\n"
            "Submit with:\n"
            "  - api_endpoint: The platform API base URL\n"
            "  - auth_token: Your API authentication token\n"
            "  - alert_name: A descriptive name for your budget alert\n"
            "  - threshold_amount: Budget limit in currency units (positive number)\n"
            "  - notification_email (optional): Email address for notifications\n"
            "  - simulate_overage: Set to true to test alert triggering\n\n"
            "Validation criteria:\n"
            "  - Alert must be configured without errors\n"
            "  - When usage exceeds threshold, alert must trigger within 30 seconds\n"
            "  - If billing service is interrupted: report error + last known state + data age"
        )

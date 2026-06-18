"""Exercise 4: Generate Usage Reports.

The learner generates a comprehensive usage report that includes
resource name, consumption quantity, unit cost, and total cost for
each billed resource.

Validates: Requirement 13.1 (generate reports), Requirement 13.5 (report completeness)
"""

import time
from typing import Optional

from labs.templates.exercise_base import Exercise
from labs.modules.billing_cost_tracking.billing_utils import (
    validate_report_completeness,
    validate_report_entry,
    within_tolerance,
    REPORT_REQUIRED_FIELDS,
)


class GenerateReportsExercise(Exercise):
    """Generate a comprehensive usage report with full billing details."""

    @property
    def exercise_id(self) -> str:
        return "04_generate_reports"

    @property
    def name(self) -> str:
        return "Generate Usage Reports"

    @property
    def description(self) -> str:
        return (
            "Generate a comprehensive usage report containing resource name, "
            "consumption quantity, unit cost, and total cost for each billed "
            "resource. Validate report completeness and cost accuracy."
        )

    @property
    def timeout_minutes(self) -> int:
        return 20

    @property
    def prerequisites(self) -> list[str]:
        return ["01_view_consumption", "02_calculate_costs"]

    def setup(self) -> None:
        """Ensure billing API is accessible for report generation."""
        pass

    def execute(self, submission: dict) -> dict:
        """Generate a usage report from submitted data or API query.

        Expected submission keys:
            - api_endpoint (str, optional): The billing API base URL.
            - auth_token (str, optional): Authentication token for the API.
            - report_entries (list[dict]): Learner-compiled report entries, each with:
                - resource_name (str): Name of the resource.
                - quantity (float): Consumption quantity.
                - unit_cost (float): Cost per unit.
                - total_cost (float): Computed total cost (quantity × unit_cost).
            - report_period (str, optional): Period for the report (e.g., '2024-01').

        Returns:
            dict with keys:
                - report (list[dict]): The validated report entries.
                - report_complete (bool): Whether all entries have required fields.
                - total_entries (int): Number of entries in the report.
                - valid_entries (int): Number of entries passing validation.
                - grand_total (float): Sum of all total_cost values.
                - cost_accuracy (list[dict]): Per-entry cost accuracy checks.
                - error (str, optional): Error message if generation failed.
                - last_known_state (dict, optional): Last known state on service error.
                - data_age_seconds (float, optional): Age of last known data.
        """
        api_endpoint = submission.get("api_endpoint", "")
        auth_token = submission.get("auth_token", "")
        report_entries = submission.get("report_entries", [])
        report_period = submission.get("report_period", "")

        if not report_entries and not api_endpoint:
            return {
                "report": [],
                "report_complete": False,
                "total_entries": 0,
                "valid_entries": 0,
                "grand_total": 0.0,
                "cost_accuracy": [],
                "error": "Either report_entries or api_endpoint must be provided.",
            }

        # If API endpoint provided and no manual entries, fetch from API
        if api_endpoint and auth_token and not report_entries:
            try:
                import requests

                headers = {"Authorization": f"Bearer {auth_token}"}
                params = {}
                if report_period:
                    params["period"] = report_period

                response = requests.get(
                    f"{api_endpoint}/api/billing/report",
                    headers=headers,
                    params=params,
                    timeout=30,
                )
                response.raise_for_status()
                api_data = response.json()
                report_entries = api_data.get("entries", [])

            except requests.exceptions.ConnectionError:
                # Requirement 13.4: Report error + last known state + data age
                return {
                    "report": [],
                    "report_complete": False,
                    "total_entries": 0,
                    "valid_entries": 0,
                    "grand_total": 0.0,
                    "cost_accuracy": [],
                    "error": (
                        f"Connection error: Unable to reach billing service at "
                        f"{api_endpoint}. Reporting last known state."
                    ),
                    "last_known_state": {
                        "report_period": report_period,
                        "status": "unavailable",
                        "entries_cached": 0,
                    },
                    "data_age_seconds": 0.0,
                }
            except requests.exceptions.Timeout:
                return {
                    "report": [],
                    "report_complete": False,
                    "total_entries": 0,
                    "valid_entries": 0,
                    "grand_total": 0.0,
                    "cost_accuracy": [],
                    "error": "Request timed out while generating report.",
                    "last_known_state": {
                        "report_period": report_period,
                        "status": "timeout",
                        "entries_cached": 0,
                    },
                    "data_age_seconds": 30.0,
                }
            except requests.exceptions.HTTPError as e:
                return {
                    "report": [],
                    "report_complete": False,
                    "total_entries": 0,
                    "valid_entries": 0,
                    "grand_total": 0.0,
                    "cost_accuracy": [],
                    "error": (
                        f"HTTP error: {e.response.status_code} - {e.response.text}"
                    ),
                }
            except ImportError:
                return {
                    "report": [],
                    "report_complete": False,
                    "total_entries": 0,
                    "valid_entries": 0,
                    "grand_total": 0.0,
                    "cost_accuracy": [],
                    "error": "requests library is not installed. Run: pip install requests",
                }

        # Validate report completeness
        completeness = validate_report_completeness(report_entries)

        # Calculate grand total and check cost accuracy per entry
        grand_total = 0.0
        cost_accuracy = []

        for entry in report_entries:
            quantity = entry.get("quantity", 0.0)
            unit_cost = entry.get("unit_cost", 0.0)
            reported_total = entry.get("total_cost", 0.0)

            if isinstance(quantity, (int, float)) and isinstance(unit_cost, (int, float)):
                expected_total = quantity * unit_cost
                is_accurate = within_tolerance(reported_total, expected_total)
            else:
                expected_total = 0.0
                is_accurate = False

            grand_total += reported_total if isinstance(reported_total, (int, float)) else 0.0
            cost_accuracy.append({
                "resource_name": entry.get("resource_name", "unknown"),
                "reported_total": reported_total,
                "expected_total": expected_total,
                "accurate": is_accurate,
            })

        return {
            "report": report_entries,
            "report_complete": completeness["complete"],
            "total_entries": completeness["total_entries"],
            "valid_entries": completeness["valid_entries"],
            "grand_total": grand_total,
            "cost_accuracy": cost_accuracy,
            "error": None,
        }

    def validate(self, result: dict) -> list[dict]:
        """Validate the generated usage report.

        Checks:
        1. No errors occurred during report generation
        2. Report contains entries with all required fields (completeness)
        3. Each entry's total_cost matches quantity × unit_cost within 1% tolerance
        """
        checks = []

        # Check for service interruption handling (Req 13.4)
        error = result.get("error")
        last_known_state = result.get("last_known_state")

        if error and last_known_state:
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

        # Check 1: No errors
        checks.append({
            "name": "report_no_errors",
            "passed": error is None,
            "feedback": (
                "Usage report generated successfully."
                if error is None
                else f"Report generation failed: {error}"
            ),
            "expected": "No errors",
            "actual": "No errors" if error is None else str(error),
        })

        # Check 2: Report completeness - all required fields present
        report_complete = result.get("report_complete", False)
        total_entries = result.get("total_entries", 0)
        valid_entries = result.get("valid_entries", 0)

        checks.append({
            "name": "report_completeness",
            "passed": report_complete and total_entries > 0,
            "feedback": (
                f"Report is complete: {valid_entries}/{total_entries} entries "
                f"have all required fields (resource_name, quantity, unit_cost, total_cost)."
                if report_complete and total_entries > 0
                else (
                    f"Report incomplete: {valid_entries}/{total_entries} entries valid. "
                    f"Each entry must have: resource_name, quantity, unit_cost, total_cost."
                )
            ),
            "expected": "All entries have required fields",
            "actual": f"{valid_entries}/{total_entries} valid entries",
        })

        # Check 3: Cost accuracy within 1% tolerance
        cost_accuracy = result.get("cost_accuracy", [])
        if cost_accuracy:
            all_accurate = all(entry.get("accurate", False) for entry in cost_accuracy)
            inaccurate = [
                entry["resource_name"]
                for entry in cost_accuracy
                if not entry.get("accurate", False)
            ]

            checks.append({
                "name": "cost_accuracy",
                "passed": all_accurate,
                "feedback": (
                    "All resource costs are accurate (total_cost = quantity × unit_cost "
                    "within 1% tolerance)."
                    if all_accurate
                    else (
                        f"Cost inaccuracy detected in: {', '.join(inaccurate)}. "
                        f"Each total_cost must equal quantity × unit_cost within 1%."
                    )
                ),
                "expected": "All costs within 1% tolerance",
                "actual": (
                    "All accurate"
                    if all_accurate
                    else f"Inaccurate: {', '.join(inaccurate)}"
                ),
            })

        return checks

    def teardown(self) -> None:
        """No cleanup needed for report generation."""
        pass

    def get_hints(self) -> list[str]:
        return [
            "Each report entry must contain: resource_name, quantity, unit_cost, total_cost.",
            "total_cost should equal quantity × unit_cost for each resource.",
            "All costs are validated with a 1% tolerance for floating-point precision.",
            "Use the /api/billing/report endpoint to fetch resource data from the platform.",
            "If the billing service is unavailable, handle the error gracefully.",
        ]

    def get_instructions(self) -> str:
        return (
            "Generate a comprehensive usage report for billed resources.\n\n"
            "Submit with:\n"
            "  - report_entries: List of resource entries, each containing:\n"
            "      - resource_name: Name of the resource (e.g., 'cpu-cores')\n"
            "      - quantity: Consumption quantity (non-negative number)\n"
            "      - unit_cost: Cost per unit (non-negative number)\n"
            "      - total_cost: Computed total (quantity × unit_cost)\n"
            "  - api_endpoint (optional): Platform API URL to fetch billing data\n"
            "  - auth_token (optional): API authentication token\n"
            "  - report_period (optional): Period for the report (e.g., '2024-01')\n\n"
            "Validation criteria:\n"
            "  - Report must contain at least one entry\n"
            "  - Every entry must have all 4 required fields\n"
            "  - Each total_cost must match quantity × unit_cost within 1% tolerance\n\n"
            "Example entry:\n"
            "  {resource_name: 'cpu-cores', quantity: 10.0, unit_cost: 0.05, total_cost: 0.50}"
        )

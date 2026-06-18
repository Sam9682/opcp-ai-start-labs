"""Exercise 1: View Resource Consumption.

The learner queries the billing system to view current resource consumption
data for active containers, verifying that resource counts match active
containers' billing records within a 1% tolerance.

Validates: Requirement 13.1 (viewing consumption), Requirement 13.2 (resource count matching)
"""

import time
from typing import Optional

from labs.templates.exercise_base import Exercise


class ViewConsumptionExercise(Exercise):
    """Query and display current resource consumption data."""

    @property
    def exercise_id(self) -> str:
        return "01_view_consumption"

    @property
    def name(self) -> str:
        return "View Resource Consumption"

    @property
    def description(self) -> str:
        return (
            "Query the billing system to view current resource consumption data "
            "for active containers. Verify that resource counts match billing records "
            "within a 1% tolerance."
        )

    @property
    def timeout_minutes(self) -> int:
        return 15

    def setup(self) -> None:
        """Ensure the billing API endpoint is accessible."""
        pass

    def execute(self, submission: dict) -> dict:
        """Query the billing API for current resource consumption.

        Expected submission keys:
            - api_endpoint (str): The billing API base URL.
            - auth_token (str): Authentication token for the API.
            - resource_filter (str, optional): Filter by resource type (cpu, memory, storage, gpu).

        Returns:
            dict with keys:
                - resources (list[dict]): List of resource consumption entries.
                - active_container_count (int): Number of active containers found.
                - billing_record_count (int): Number of billing records returned.
                - query_timestamp (str): ISO timestamp of the query.
                - error (str, optional): Error message if the query failed.
        """
        api_endpoint = submission.get("api_endpoint", "")
        auth_token = submission.get("auth_token", "")
        resource_filter = submission.get("resource_filter", None)

        if not api_endpoint:
            return {
                "resources": [],
                "active_container_count": 0,
                "billing_record_count": 0,
                "query_timestamp": "",
                "error": "api_endpoint is required.",
            }

        if not auth_token:
            return {
                "resources": [],
                "active_container_count": 0,
                "billing_record_count": 0,
                "query_timestamp": "",
                "error": "auth_token is required for authentication.",
            }

        # Query the platform billing API
        try:
            import requests

            headers = {"Authorization": f"Bearer {auth_token}"}
            params = {}
            if resource_filter:
                params["type"] = resource_filter

            # Get active containers
            containers_response = requests.get(
                f"{api_endpoint}/api/containers",
                headers=headers,
                params={"status": "running"},
                timeout=30,
            )
            containers_response.raise_for_status()
            containers_data = containers_response.json()
            active_container_count = len(containers_data.get("containers", []))

            # Get billing records
            billing_response = requests.get(
                f"{api_endpoint}/api/billing/consumption",
                headers=headers,
                params=params,
                timeout=30,
            )
            billing_response.raise_for_status()
            billing_data = billing_response.json()

            resources = billing_data.get("resources", [])
            query_timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

            return {
                "resources": resources,
                "active_container_count": active_container_count,
                "billing_record_count": len(resources),
                "query_timestamp": query_timestamp,
                "error": None,
            }

        except requests.exceptions.ConnectionError:
            return {
                "resources": [],
                "active_container_count": 0,
                "billing_record_count": 0,
                "query_timestamp": "",
                "error": (
                    f"Connection error: Unable to reach billing service at {api_endpoint}. "
                    "Check network connectivity and ensure the platform is running."
                ),
            }
        except requests.exceptions.Timeout:
            return {
                "resources": [],
                "active_container_count": 0,
                "billing_record_count": 0,
                "query_timestamp": "",
                "error": "Request timed out after 30 seconds.",
            }
        except requests.exceptions.HTTPError as e:
            return {
                "resources": [],
                "active_container_count": 0,
                "billing_record_count": 0,
                "query_timestamp": "",
                "error": f"HTTP error: {e.response.status_code} - {e.response.text}",
            }
        except ImportError:
            return {
                "resources": [],
                "active_container_count": 0,
                "billing_record_count": 0,
                "query_timestamp": "",
                "error": "requests library is not installed. Run: pip install requests",
            }

    def validate(self, result: dict) -> list[dict]:
        """Validate the resource consumption query result.

        Checks:
        1. No errors occurred during the query
        2. Resource data was returned
        3. Resource count matches active containers within 1% tolerance
        """
        checks = []

        # Check 1: No query errors
        error = result.get("error")
        checks.append({
            "name": "query_no_errors",
            "passed": error is None,
            "feedback": (
                "Resource consumption query completed successfully."
                if error is None
                else f"Query failed: {error}"
            ),
            "expected": "No errors",
            "actual": "No errors" if error is None else str(error),
        })

        # Check 2: Resources returned
        resources = result.get("resources", [])
        checks.append({
            "name": "resources_returned",
            "passed": len(resources) > 0,
            "feedback": (
                f"Retrieved {len(resources)} resource consumption entries."
                if len(resources) > 0
                else "No resource consumption data returned."
            ),
            "expected": "> 0 resources",
            "actual": f"{len(resources)} resources",
        })

        # Check 3: Resource count matches within 1% tolerance
        active_count = result.get("active_container_count", 0)
        billing_count = result.get("billing_record_count", 0)

        if active_count > 0:
            tolerance = 0.01
            difference_ratio = abs(billing_count - active_count) / active_count
            within_tolerance = difference_ratio <= tolerance
        else:
            # If no active containers, billing should also be 0 or empty
            within_tolerance = billing_count == 0

        checks.append({
            "name": "resource_count_tolerance",
            "passed": within_tolerance,
            "feedback": (
                f"Resource count ({billing_count}) matches active containers "
                f"({active_count}) within 1% tolerance."
                if within_tolerance
                else (
                    f"Resource count mismatch: billing records ({billing_count}) "
                    f"vs active containers ({active_count}). "
                    f"Difference exceeds 1% tolerance."
                )
            ),
            "expected": f"Within 1% of {active_count}",
            "actual": str(billing_count),
        })

        return checks

    def teardown(self) -> None:
        """No cleanup needed for consumption queries."""
        pass

    def get_hints(self) -> list[str]:
        return [
            "Use the billing API endpoint at /api/billing/consumption to query resource data.",
            "Ensure your auth_token has billing read permissions.",
            "You can filter by resource type: cpu, memory, storage, or gpu.",
            "The resource count should match the number of active containers within 1%.",
        ]

    def get_instructions(self) -> str:
        return (
            "Query the AI-Powered-Store billing system to view current resource consumption.\n\n"
            "Submit with:\n"
            "  - api_endpoint: The platform API base URL (e.g., http://localhost:5000)\n"
            "  - auth_token: Your API authentication token\n"
            "  - resource_filter (optional): Filter by type - 'cpu', 'memory', 'storage', 'gpu'\n\n"
            "Validation criteria:\n"
            "  - The query must complete without errors\n"
            "  - Resource consumption data must be returned\n"
            "  - Resource count must match active containers within 1% tolerance"
        )

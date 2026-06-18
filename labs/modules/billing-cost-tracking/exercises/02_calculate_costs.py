"""Exercise 2: Calculate Expected Costs.

The learner applies cost calculation rules to a given resource set and
computes expected charges. The Exercise_Validator verifies that learner-
computed charges match system-computed charges within a 1% tolerance.

Validates: Requirement 13.1 (cost calculation), Requirement 13.6 (1% tolerance match)
"""

from labs.templates.exercise_base import Exercise


class CalculateCostsExercise(Exercise):
    """Apply cost calculation rules to compute expected charges."""

    @property
    def exercise_id(self) -> str:
        return "02_calculate_costs"

    @property
    def name(self) -> str:
        return "Calculate Expected Costs"

    @property
    def description(self) -> str:
        return (
            "Apply cost calculation rules to a given resource set and compute "
            "expected charges. Verify that your computed charges match the system's "
            "charges within a 1% tolerance."
        )

    @property
    def timeout_minutes(self) -> int:
        return 20

    @property
    def prerequisites(self) -> list[str]:
        return ["01_view_consumption"]

    def setup(self) -> None:
        """No special setup required for cost calculation."""
        pass

    def execute(self, submission: dict) -> dict:
        """Execute cost calculation for the given resource set.

        Expected submission keys:
            - resources (list[dict]): Resource entries, each with:
                - name (str): Resource name (e.g., 'cpu-cores', 'memory-gb', 'storage-gb')
                - quantity (float): Consumption quantity
                - unit_cost (float): Cost per unit
            - learner_total (float): The learner's calculated total cost.
            - api_endpoint (str, optional): Billing API for system calculation.
            - auth_token (str, optional): Auth token for API access.

        Returns:
            dict with keys:
                - resource_costs (list[dict]): Each resource with computed cost.
                - learner_total (float): The learner's submitted total.
                - system_total (float): The system-computed total.
                - within_tolerance (bool): Whether learner matches system within 1%.
                - tolerance_percentage (float): Actual percentage difference.
                - error (str, optional): Error message if calculation failed.
        """
        resources = submission.get("resources", [])
        learner_total = submission.get("learner_total", 0.0)
        api_endpoint = submission.get("api_endpoint", "")
        auth_token = submission.get("auth_token", "")

        if not resources:
            return {
                "resource_costs": [],
                "learner_total": learner_total,
                "system_total": 0.0,
                "within_tolerance": False,
                "tolerance_percentage": 100.0,
                "error": "No resources provided. Supply a list of resource entries.",
            }

        # Compute system total from the resource set
        resource_costs = []
        system_total = 0.0

        for resource in resources:
            name = resource.get("name", "unknown")
            quantity = resource.get("quantity", 0.0)
            unit_cost = resource.get("unit_cost", 0.0)

            if not isinstance(quantity, (int, float)) or quantity < 0:
                return {
                    "resource_costs": resource_costs,
                    "learner_total": learner_total,
                    "system_total": 0.0,
                    "within_tolerance": False,
                    "tolerance_percentage": 100.0,
                    "error": f"Invalid quantity for resource '{name}': must be a non-negative number.",
                }

            if not isinstance(unit_cost, (int, float)) or unit_cost < 0:
                return {
                    "resource_costs": resource_costs,
                    "learner_total": learner_total,
                    "system_total": 0.0,
                    "within_tolerance": False,
                    "tolerance_percentage": 100.0,
                    "error": f"Invalid unit_cost for resource '{name}': must be a non-negative number.",
                }

            total_cost = quantity * unit_cost
            system_total += total_cost
            resource_costs.append({
                "name": name,
                "quantity": quantity,
                "unit_cost": unit_cost,
                "total_cost": total_cost,
            })

        # If an API endpoint is provided, also query the system for verification
        if api_endpoint and auth_token:
            try:
                import requests

                headers = {"Authorization": f"Bearer {auth_token}"}
                response = requests.post(
                    f"{api_endpoint}/api/billing/calculate",
                    headers=headers,
                    json={"resources": resources},
                    timeout=30,
                )
                response.raise_for_status()
                api_data = response.json()
                system_total = api_data.get("total_cost", system_total)
            except Exception:
                # Fall back to local calculation if API is unavailable
                pass

        # Calculate tolerance
        if system_total > 0:
            tolerance_percentage = abs(learner_total - system_total) / system_total * 100
            within_tolerance = tolerance_percentage <= 1.0
        elif learner_total == 0.0:
            tolerance_percentage = 0.0
            within_tolerance = True
        else:
            tolerance_percentage = 100.0
            within_tolerance = False

        return {
            "resource_costs": resource_costs,
            "learner_total": learner_total,
            "system_total": system_total,
            "within_tolerance": within_tolerance,
            "tolerance_percentage": tolerance_percentage,
            "error": None,
        }

    def validate(self, result: dict) -> list[dict]:
        """Validate the cost calculation result.

        Checks:
        1. No errors occurred during calculation
        2. Resource costs were computed for all entries
        3. Learner-computed total matches system total within 1% tolerance
        """
        checks = []

        # Check 1: No calculation errors
        error = result.get("error")
        checks.append({
            "name": "calculation_no_errors",
            "passed": error is None,
            "feedback": (
                "Cost calculation completed successfully."
                if error is None
                else f"Calculation error: {error}"
            ),
            "expected": "No errors",
            "actual": "No errors" if error is None else str(error),
        })

        # Check 2: Resource costs computed
        resource_costs = result.get("resource_costs", [])
        checks.append({
            "name": "resource_costs_computed",
            "passed": len(resource_costs) > 0,
            "feedback": (
                f"Computed costs for {len(resource_costs)} resources."
                if len(resource_costs) > 0
                else "No resource costs were computed."
            ),
            "expected": "> 0 resource cost entries",
            "actual": f"{len(resource_costs)} entries",
        })

        # Check 3: Learner total within 1% tolerance of system total
        within_tolerance = result.get("within_tolerance", False)
        learner_total = result.get("learner_total", 0.0)
        system_total = result.get("system_total", 0.0)
        tolerance_pct = result.get("tolerance_percentage", 100.0)

        checks.append({
            "name": "cost_tolerance_match",
            "passed": within_tolerance,
            "feedback": (
                f"Learner total ({learner_total:.2f}) matches system total "
                f"({system_total:.2f}) within 1% tolerance "
                f"(actual difference: {tolerance_pct:.4f}%)."
                if within_tolerance
                else (
                    f"Learner total ({learner_total:.2f}) does not match system "
                    f"total ({system_total:.2f}). Difference: {tolerance_pct:.4f}% "
                    f"(exceeds 1% tolerance)."
                )
            ),
            "expected": f"Within 1% of {system_total:.2f}",
            "actual": f"{learner_total:.2f} (difference: {tolerance_pct:.4f}%)",
        })

        return checks

    def teardown(self) -> None:
        """No cleanup needed for cost calculations."""
        pass

    def get_hints(self) -> list[str]:
        return [
            "Total cost for each resource = quantity × unit_cost.",
            "Sum all resource totals to get the overall cost.",
            "Your calculated total must be within 1% of the system total to pass.",
            "Double-check units: CPU is in core-hours, memory in GB-hours, storage in GB-months.",
        ]

    def get_instructions(self) -> str:
        return (
            "Calculate the expected charges for a given resource set.\n\n"
            "Submit with:\n"
            "  - resources: List of resource entries, each containing:\n"
            "      - name: Resource name (e.g., 'cpu-cores', 'memory-gb')\n"
            "      - quantity: Consumption quantity\n"
            "      - unit_cost: Cost per unit\n"
            "  - learner_total: Your calculated total cost (sum of quantity × unit_cost)\n"
            "  - api_endpoint (optional): Platform API URL for system verification\n"
            "  - auth_token (optional): API authentication token\n\n"
            "Validation criteria:\n"
            "  - All resource costs must be computed correctly\n"
            "  - Your total must match the system calculation within 1% tolerance\n\n"
            "Example: If cpu-cores quantity=10, unit_cost=0.05, total_cost=0.50"
        )

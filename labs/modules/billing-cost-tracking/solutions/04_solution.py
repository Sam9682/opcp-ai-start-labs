"""Reference solution for Exercise 4: Generate Usage Reports.

Demonstrates the correct approach to generating a comprehensive
usage report containing resource name, consumption quantity, unit cost,
and total cost for each billed resource.
"""


def get_solution() -> dict:
    """Return the reference solution submission for generating reports.

    Returns:
        A dict representing a valid submission that passes all checks.
    """
    return {
        "report_entries": [
            {
                "resource_name": "cpu-cores",
                "quantity": 10.0,
                "unit_cost": 0.05,
                "total_cost": 0.50,
            },
            {
                "resource_name": "memory-gb",
                "quantity": 32.0,
                "unit_cost": 0.01,
                "total_cost": 0.32,
            },
            {
                "resource_name": "storage-gb",
                "quantity": 100.0,
                "unit_cost": 0.002,
                "total_cost": 0.20,
            },
            {
                "resource_name": "gpu-hours",
                "quantity": 5.0,
                "unit_cost": 1.50,
                "total_cost": 7.50,
            },
        ],
        "report_period": "2024-01",
    }


def get_report_format() -> str:
    """Explain the required report format.

    Returns:
        Human-readable description of the report field requirements.
    """
    return (
        "Each report entry must contain these 4 required fields:\n"
        "  - resource_name (str): Non-empty name of the resource\n"
        "  - quantity (float): Non-negative consumption quantity\n"
        "  - unit_cost (float): Non-negative cost per unit\n"
        "  - total_cost (float): Computed as quantity × unit_cost\n\n"
        "The total_cost for each entry is validated against\n"
        "quantity × unit_cost with a 1% tolerance."
    )


def get_verification_steps() -> list[str]:
    """Return step-by-step instructions for report generation.

    Returns:
        List of steps the learner should follow.
    """
    return [
        "1. Query the billing system for all billed resources in the reporting period",
        "2. For each resource, record:",
        "   - resource_name: The identifier of the resource",
        "   - quantity: How much was consumed",
        "   - unit_cost: The rate per unit",
        "   - total_cost: quantity × unit_cost",
        "3. Compile all entries into the report_entries list",
        "4. Submit the report for validation",
        "5. The validator checks:",
        "   - All entries have all 4 required fields",
        "   - Each total_cost = quantity × unit_cost (within 1%)",
        "   - No resources are omitted from the report",
    ]

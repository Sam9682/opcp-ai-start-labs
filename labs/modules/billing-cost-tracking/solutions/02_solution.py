"""Reference solution for Exercise 2: Calculate Expected Costs.

Demonstrates the correct approach to computing charges from a resource
set and verifying that computed totals match within 1% tolerance.
"""


def get_solution() -> dict:
    """Return the reference solution submission for cost calculation.

    Returns:
        A dict representing a valid submission that passes all checks.
    """
    resources = [
        {"name": "cpu-cores", "quantity": 10.0, "unit_cost": 0.05},
        {"name": "memory-gb", "quantity": 32.0, "unit_cost": 0.01},
        {"name": "storage-gb", "quantity": 100.0, "unit_cost": 0.002},
        {"name": "gpu-hours", "quantity": 5.0, "unit_cost": 1.50},
    ]

    # Correct total: 10*0.05 + 32*0.01 + 100*0.002 + 5*1.50 = 0.50 + 0.32 + 0.20 + 7.50 = 8.52
    learner_total = sum(r["quantity"] * r["unit_cost"] for r in resources)

    return {
        "resources": resources,
        "learner_total": learner_total,
    }


def get_calculation_steps() -> list[str]:
    """Return the step-by-step calculation instructions.

    Returns:
        List of steps explaining the cost calculation approach.
    """
    return [
        "1. For each resource entry, compute: total_cost = quantity × unit_cost",
        "   - cpu-cores:   10.0 × $0.05  = $0.50",
        "   - memory-gb:   32.0 × $0.01  = $0.32",
        "   - storage-gb: 100.0 × $0.002 = $0.20",
        "   - gpu-hours:    5.0 × $1.50  = $7.50",
        "2. Sum all resource costs to get learner_total:",
        "   $0.50 + $0.32 + $0.20 + $7.50 = $8.52",
        "3. Submit with your learner_total value",
        "4. The system will verify your total matches within 1% tolerance",
    ]


def get_tolerance_explanation() -> str:
    """Explain the 1% tolerance requirement.

    Returns:
        Human-readable explanation of the tolerance check.
    """
    return (
        "The tolerance check uses relative comparison:\n"
        "  |learner_total - system_total| / |system_total| <= 0.01\n\n"
        "For example, if system_total = $8.52:\n"
        "  Acceptable range: $8.52 ± 1% = $8.4348 to $8.6052\n"
        "  Any learner_total within this range passes."
    )

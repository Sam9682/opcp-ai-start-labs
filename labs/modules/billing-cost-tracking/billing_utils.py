"""Utility functions for the Billing and Cost Tracking lab module.

Provides reusable helpers for numeric tolerance comparison (1% tolerance)
and report field validation used across multiple exercises.

Validates: Requirements 13.2 (1% tolerance), 13.5 (report field completeness)
"""

from typing import Optional


# Required fields for a complete usage report entry
REPORT_REQUIRED_FIELDS = ("resource_name", "quantity", "unit_cost", "total_cost")


def within_tolerance(
    actual: float,
    expected: float,
    tolerance: float = 0.01,
) -> bool:
    """Check if actual value is within a percentage tolerance of expected.

    Uses relative tolerance: |actual - expected| / |expected| <= tolerance.
    If expected is zero, actual must also be zero for a match.

    Args:
        actual: The value to check.
        expected: The reference value.
        tolerance: Maximum allowed relative difference (default 1% = 0.01).

    Returns:
        True if actual is within the tolerance of expected.
    """
    if expected == 0.0:
        return actual == 0.0

    difference_ratio = abs(actual - expected) / abs(expected)
    return difference_ratio <= tolerance


def tolerance_percentage(actual: float, expected: float) -> float:
    """Calculate the percentage difference between actual and expected.

    Args:
        actual: The value to check.
        expected: The reference value.

    Returns:
        The percentage difference. Returns 0.0 if both are zero,
        100.0 if expected is zero but actual is not.
    """
    if expected == 0.0:
        return 0.0 if actual == 0.0 else 100.0

    return abs(actual - expected) / abs(expected) * 100


def validate_report_entry(entry: dict) -> tuple[bool, list[str]]:
    """Validate that a usage report entry contains all required fields.

    A complete report entry must have:
    - resource_name (str, non-empty)
    - quantity (numeric, >= 0)
    - unit_cost (numeric, >= 0)
    - total_cost (numeric, >= 0)

    Args:
        entry: A dict representing a single report line item.

    Returns:
        Tuple of (is_valid, list_of_missing_or_invalid_fields).
    """
    issues = []

    # Check resource_name
    resource_name = entry.get("resource_name")
    if not resource_name or not isinstance(resource_name, str) or not resource_name.strip():
        issues.append("resource_name")

    # Check quantity
    quantity = entry.get("quantity")
    if quantity is None or not isinstance(quantity, (int, float)) or quantity < 0:
        issues.append("quantity")

    # Check unit_cost
    unit_cost = entry.get("unit_cost")
    if unit_cost is None or not isinstance(unit_cost, (int, float)) or unit_cost < 0:
        issues.append("unit_cost")

    # Check total_cost
    total_cost = entry.get("total_cost")
    if total_cost is None or not isinstance(total_cost, (int, float)) or total_cost < 0:
        issues.append("total_cost")

    return (len(issues) == 0, issues)


def validate_report_completeness(report_entries: list[dict]) -> dict:
    """Validate that a full usage report has all required fields for each entry.

    Args:
        report_entries: List of report entry dicts.

    Returns:
        Dict with:
            - complete (bool): True if all entries are valid.
            - total_entries (int): Number of entries checked.
            - valid_entries (int): Number of fully valid entries.
            - issues (list[dict]): Details of entries with problems.
    """
    if not report_entries:
        return {
            "complete": False,
            "total_entries": 0,
            "valid_entries": 0,
            "issues": [{"index": 0, "fields": ["no entries provided"]}],
        }

    issues = []
    valid_count = 0

    for idx, entry in enumerate(report_entries):
        is_valid, missing_fields = validate_report_entry(entry)
        if is_valid:
            valid_count += 1
        else:
            issues.append({"index": idx, "fields": missing_fields})

    return {
        "complete": valid_count == len(report_entries),
        "total_entries": len(report_entries),
        "valid_entries": valid_count,
        "issues": issues,
    }

"""Property-based tests for the Billing and Cost Tracking lab module.

Feature: ai-store-labs, Property 16: Numeric Tolerance Comparison
Feature: ai-store-labs, Property 17: Usage Report Field Completeness

Validates: Requirements 13.2, 13.5, 13.6

These tests run entirely in-process with no Docker and no network access.
They exercise the billing module's relative-tolerance comparison
(within_tolerance) and the usage report completeness validator
(validate_report_completeness / validate_report_entry).

The billing module directory name contains hyphens, which are not valid in a
`from ... import` dotted path, so the module is loaded via importlib following
the convention used by the other module-specific tests in this package.
"""

import importlib
import math

from hypothesis import assume, given, settings
from hypothesis import strategies as st

# The module directory contains hyphens; load billing_utils via importlib.
_MODULE = "labs.modules.billing-cost-tracking"
billing_utils = importlib.import_module(f"{_MODULE}.billing_utils")

within_tolerance = billing_utils.within_tolerance
validate_report_entry = billing_utils.validate_report_entry
validate_report_completeness = billing_utils.validate_report_completeness
REPORT_REQUIRED_FIELDS = billing_utils.REPORT_REQUIRED_FIELDS

TOLERANCE = 0.01  # 1% relative tolerance


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

# Finite, well-behaved floating point values for the tolerance comparison.
# Bounded away from the extremes to keep the relative-difference arithmetic
# free of overflow and NaN surprises.
finite_values = st.floats(
    min_value=-1e9,
    max_value=1e9,
    allow_nan=False,
    allow_infinity=False,
)

# Non-zero reference values: the relative-tolerance branch divides by
# |expected|, so a separate strategy guarantees a meaningful denominator.
nonzero_expected = st.floats(
    min_value=-1e9,
    max_value=1e9,
    allow_nan=False,
    allow_infinity=False,
).filter(lambda x: abs(x) > 1e-6)


# Billed resources: a resource name paired with a non-negative quantity and
# unit cost. Resource names are non-empty and whitespace-stripped so each maps
# to a valid report entry.
resource_name_strategy = st.text(
    alphabet=st.characters(min_codepoint=97, max_codepoint=122),
    min_size=1,
    max_size=12,
)

billed_resource = st.fixed_dictionaries(
    {
        "name": resource_name_strategy,
        "quantity": st.floats(
            min_value=0.0, max_value=1e6, allow_nan=False, allow_infinity=False
        ),
        "unit_cost": st.floats(
            min_value=0.0, max_value=1e4, allow_nan=False, allow_infinity=False
        ),
    }
)

# A set of billed resources for a reporting period. Keyed by unique names so a
# "set" of resources has no accidental duplicates masking an omission.
billed_resource_set = st.lists(billed_resource, min_size=1, max_size=20).map(
    lambda items: list({r["name"]: r for r in items}.values())
)


def _generate_report(resources):
    """Build a usage report (one entry per resource) like exercise 4 does.

    Each entry carries the four required fields: resource name, consumption
    quantity, unit cost, and total cost (quantity * unit_cost).
    """
    return [
        {
            "resource_name": r["name"],
            "quantity": r["quantity"],
            "unit_cost": r["unit_cost"],
            "total_cost": r["quantity"] * r["unit_cost"],
        }
        for r in resources
    ]


# ---------------------------------------------------------------------------
# Property 16: Numeric Tolerance Comparison
# ---------------------------------------------------------------------------


@settings(max_examples=300)
@given(actual=finite_values, expected=nonzero_expected)
def test_tolerance_comparison_iff_relative_difference(actual, expected):
    """Feature: ai-store-labs, Property 16: Numeric Tolerance Comparison.

    Validates: Requirements 13.2, 13.6

    For any pair (expected, actual) with a non-zero expected, within_tolerance
    reports a match if and only if the relative difference
    |actual - expected| / |expected| is at most the 1% tolerance.
    """
    relative_difference = abs(actual - expected) / abs(expected)
    expected_match = relative_difference <= TOLERANCE

    assert within_tolerance(actual, expected, TOLERANCE) is expected_match


@settings(max_examples=200)
@given(expected=nonzero_expected, sign=st.sampled_from([-1.0, 1.0]))
def test_tolerance_boundary_is_inclusive(expected, sign):
    """Feature: ai-store-labs, Property 16: Numeric Tolerance Comparison.

    Validates: Requirements 13.2, 13.6

    A value sitting exactly on the 1% boundary
    (|actual - expected| / |expected| == tolerance) is reported as matching.
    The boundary actual is constructed as expected +/- tolerance * |expected|.
    """
    boundary_offset = TOLERANCE * abs(expected)
    actual = expected + sign * boundary_offset

    # The constructed actual lands exactly on (or, due to float rounding, at
    # most a hair past) the boundary. Only assert inclusivity for the cases
    # that remain within tolerance after floating-point rounding; the ratio is
    # recomputed the same way the implementation does.
    relative_difference = abs(actual - expected) / abs(expected)
    assume(relative_difference <= TOLERANCE)

    assert within_tolerance(actual, expected, TOLERANCE) is True


@settings(max_examples=200)
@given(actual=finite_values)
def test_tolerance_zero_expected_requires_zero_actual(actual):
    """Feature: ai-store-labs, Property 16: Numeric Tolerance Comparison.

    Validates: Requirements 13.2, 13.6

    When expected is zero, the relative comparison is undefined, so a match is
    reported if and only if actual is also exactly zero.
    """
    result = within_tolerance(actual, 0.0, TOLERANCE)
    assert result is (actual == 0.0)


# ---------------------------------------------------------------------------
# Property 17: Usage Report Field Completeness
# ---------------------------------------------------------------------------


@settings(max_examples=200)
@given(resources=billed_resource_set)
def test_report_contains_entry_for_each_resource(resources):
    """Feature: ai-store-labs, Property 17: Usage Report Field Completeness.

    Validates: Requirement 13.5

    For any set of billed resources within a reporting period, the generated
    report contains exactly one entry per resource with all four required
    fields populated, and no resource is omitted.
    """
    report = _generate_report(resources)

    # No resource is omitted: one entry per billed resource, same name set.
    assert len(report) == len(resources)
    reported_names = {entry["resource_name"] for entry in report}
    expected_names = {r["name"] for r in resources}
    assert reported_names == expected_names

    # Every entry carries all required fields with valid values.
    for entry in report:
        is_valid, issues = validate_report_entry(entry)
        assert is_valid, f"entry missing/invalid fields {issues}: {entry}"
        for field in REPORT_REQUIRED_FIELDS:
            assert field in entry

    # The aggregate completeness check agrees: the full report is complete.
    summary = validate_report_completeness(report)
    assert summary["complete"] is True
    assert summary["total_entries"] == len(resources)
    assert summary["valid_entries"] == len(resources)
    assert summary["issues"] == []


@settings(max_examples=200)
@given(resources=billed_resource_set, drop_index=st.integers(min_value=0))
def test_report_omitting_a_field_is_detected(resources, drop_index):
    """Feature: ai-store-labs, Property 17: Usage Report Field Completeness.

    Validates: Requirement 13.5

    If any required field is omitted from an entry, the completeness validator
    must flag the report as incomplete and name the missing field. This is the
    contrapositive of field completeness: a report lacking a required field is
    never reported as complete.
    """
    report = _generate_report(resources)

    # Pick a deterministic entry and a deterministic required field to drop.
    entry_idx = drop_index % len(report)
    field_to_drop = REPORT_REQUIRED_FIELDS[drop_index % len(REPORT_REQUIRED_FIELDS)]
    del report[entry_idx][field_to_drop]

    summary = validate_report_completeness(report)

    assert summary["complete"] is False
    # The flagged issue points at the entry and names the missing field.
    flagged = [i for i in summary["issues"] if i["index"] == entry_idx]
    assert flagged, f"missing field {field_to_drop} not flagged: {summary}"
    assert field_to_drop in flagged[0]["fields"]

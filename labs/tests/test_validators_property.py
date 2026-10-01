"""Property-based tests for ExerciseValidator.

Feature: ai-store-labs, Property 9: Exercise Step Assertion Evaluation
Validates: Requirements 3.7

Uses Hypothesis to verify that, for any step result and JSON assertion pair,
the ExerciseValidator reports passed=true if and only if the step result
satisfies all conditions in the assertion:
- equality: the actual value equals the expected value
- containment: the actual value contains the expected substring

These tests run without Docker or network access. The ExerciseValidator
takes a PlatformClient, which is mocked here; validate_step does not touch
the platform client, so a lightweight fake is sufficient.
"""

from hypothesis import given, settings, strategies as st

from labs.core.validators import ExerciseValidator


class FakePlatformClient:
    """Lightweight fake platform client (no network / Docker)."""

    def query(self, endpoint: str, params=None) -> dict:
        return {"status": "ok"}


def make_validator() -> ExerciseValidator:
    return ExerciseValidator(platform_client=FakePlatformClient())


# ---------------------------------------------------------------------------
# Generators
# ---------------------------------------------------------------------------

# JSON-serializable scalar values usable for equality assertions.
json_scalars = st.one_of(
    st.none(),
    st.booleans(),
    st.integers(min_value=-(10**6), max_value=10**6),
    st.floats(allow_nan=False, allow_infinity=False, width=32),
    st.text(max_size=50),
)

# Simple JSON values (scalars plus small lists) for equality comparisons.
json_values = st.one_of(
    json_scalars,
    st.lists(json_scalars, max_size=5),
)

step_names = st.text(min_size=0, max_size=20)
field_names = st.sampled_from(["actual", "status", "output", "status_code", "result"])


# ---------------------------------------------------------------------------
# Property 9 — Equality assertions
# ---------------------------------------------------------------------------


@settings(max_examples=200)
@given(
    name=step_names,
    field=field_names,
    actual=json_values,
    expected=json_values,
)
def test_property9_equality_matches_python_equality(name, field, actual, expected):
    """passed is True iff actual == expected for equality assertions.

    Feature: ai-store-labs, Property 9: Exercise Step Assertion Evaluation
    Validates: Requirements 3.7
    """
    validator = make_validator()
    step = {"name": name, field: actual}
    assertion = {"type": "equality", "expected": expected, "field": field}

    result = validator.validate_step(step, assertion)

    assert result.passed == (actual == expected)


@settings(max_examples=100)
@given(name=step_names, field=field_names, value=json_values)
def test_property9_equality_identical_values_pass(name, field, value):
    """Identical actual/expected values always satisfy an equality assertion.

    Feature: ai-store-labs, Property 9: Exercise Step Assertion Evaluation
    Validates: Requirements 3.7
    """
    validator = make_validator()
    step = {"name": name, field: value}
    assertion = {"type": "equality", "expected": value, "field": field}

    result = validator.validate_step(step, assertion)

    assert result.passed is True


# ---------------------------------------------------------------------------
# Property 9 — Containment assertions
# ---------------------------------------------------------------------------


@settings(max_examples=200)
@given(
    name=step_names,
    actual=st.text(max_size=80),
    expected=st.text(max_size=80),
)
def test_property9_containment_matches_substring(name, actual, expected):
    """passed is True iff expected substring is contained in the actual string.

    Feature: ai-store-labs, Property 9: Exercise Step Assertion Evaluation
    Validates: Requirements 3.7
    """
    validator = make_validator()
    step = {"name": name, "actual": actual}
    assertion = {"type": "containment", "expected": expected}

    result = validator.validate_step(step, assertion)

    # The validator compares string representations; for text values this is
    # the identity, so the ground truth is plain substring membership.
    assert result.passed == (str(expected) in str(actual))


@settings(max_examples=150)
@given(
    name=step_names,
    prefix=st.text(max_size=30),
    needle=st.text(min_size=1, max_size=30),
    suffix=st.text(max_size=30),
)
def test_property9_containment_substring_always_found(name, prefix, needle, suffix):
    """A substring deliberately embedded in the actual value is always found.

    Feature: ai-store-labs, Property 9: Exercise Step Assertion Evaluation
    Validates: Requirements 3.7
    """
    validator = make_validator()
    actual = prefix + needle + suffix
    step = {"name": name, "actual": actual}
    assertion = {"type": "containment", "expected": needle}

    result = validator.validate_step(step, assertion)

    assert result.passed is True


@settings(max_examples=100)
@given(name=step_names, expected=st.text(min_size=1, max_size=30))
def test_property9_containment_none_actual_fails(name, expected):
    """Containment against a None actual value never passes.

    Feature: ai-store-labs, Property 9: Exercise Step Assertion Evaluation
    Validates: Requirements 3.7
    """
    validator = make_validator()
    step = {"name": name, "actual": None}
    assertion = {"type": "containment", "expected": expected}

    result = validator.validate_step(step, assertion)

    assert result.passed is False

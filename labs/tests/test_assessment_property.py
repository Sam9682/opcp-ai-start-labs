"""Property-based tests for the AssessmentEngine.

Feature: ai-store-labs, Property 6: Assessment Result Consistency
Validates: Requirement 3.3 (Assessment engine evaluates submissions)

These tests exercise AssessmentEngine.evaluate() across many generated
submission/expected pairs. The engine is a pure function (no Docker, no
network, no I/O), so no mocks are required.
"""

from hypothesis import given, settings
from hypothesis import strategies as st

from labs.core.assessment import AssessmentEngine
from labs.core.models import AssessmentResult, CheckResult


# Simple, hashable, comparable values usable as dict values. Kept intentionally
# small so generated submissions can both match and mismatch expected values.
_values = st.one_of(
    st.integers(min_value=-5, max_value=5),
    st.booleans(),
    st.none(),
    st.text(alphabet="abcxyz", max_size=3),
)

# Check names (dict keys).
_keys = st.text(alphabet="abcdefghij", min_size=1, max_size=4)

# "expected" dictionaries: the outcomes an exercise is checked against.
_expected_dicts = st.dictionaries(keys=_keys, values=_values, max_size=6)


def _submission_strategy(expected: dict):
    """Build a submission that overlaps with the given expected keys.

    For each expected key, the generated submission may: keep the matching
    value, replace it with a (likely) different value, or omit the key. This
    produces a healthy mix of passing and failing checks while still exploring
    the input space broadly. Extra, unrelated keys are also added.
    """
    key_choices = {}
    for key, exp_value in expected.items():
        key_choices[key] = st.one_of(
            st.just(exp_value),              # matching value -> check passes
            _values,                          # possibly-different value
            st.just(_OMIT),                   # omit key -> actual is None
        )
    base = st.fixed_dictionaries(key_choices) if key_choices else st.just({})
    extras = st.dictionaries(keys=_keys, values=_values, max_size=3)

    return st.builds(_merge_submission, base, extras)


_OMIT = object()


def _merge_submission(base: dict, extras: dict) -> dict:
    submission = {k: v for k, v in base.items() if v is not _OMIT}
    # Extras must not clobber keys we deliberately shaped above.
    for k, v in extras.items():
        if k not in base:
            submission[k] = v
    return submission


_engine = AssessmentEngine()


@settings(max_examples=200)
@given(exercise_id=st.text(alphabet="ex-123", min_size=1, max_size=6),
       expected=_expected_dicts, data=st.data())
def test_assessment_result_consistency(exercise_id, expected, data):
    """Feature: ai-store-labs, Property 6: Assessment Result Consistency.

    For any submission evaluated by the AssessmentEngine:
      - status is "pass" iff every check reports passed=True;
      - status is "fail" iff any check reports passed=False;
      - the checks list is always non-empty;
      - feedback is always a non-empty string.
    """
    submission = data.draw(_submission_strategy(expected))

    result = _engine.evaluate(exercise_id, submission, expected)

    # Structural guarantees.
    assert isinstance(result, AssessmentResult)
    assert isinstance(result.checks, list)
    assert len(result.checks) >= 1, "checks list must never be empty"
    assert all(isinstance(c, CheckResult) for c in result.checks)
    assert isinstance(result.feedback, str)
    assert len(result.feedback) > 0, "feedback must be non-empty"

    # Status is restricted to the documented values.
    assert result.status in ("pass", "fail")

    # The core consistency invariant: pass iff all checks passed.
    all_passed = all(c.passed for c in result.checks)
    any_failed = any(not c.passed for c in result.checks)

    if all_passed:
        assert result.status == "pass"
    if any_failed:
        assert result.status == "fail"

    # Biconditional stated explicitly.
    assert (result.status == "pass") == all_passed
    assert (result.status == "fail") == any_failed


@settings(max_examples=100)
@given(exercise_id=st.text(alphabet="ex-123", min_size=1, max_size=6),
       expected=_expected_dicts)
def test_matching_submission_always_passes(exercise_id, expected):
    """A submission equal to expected yields status 'pass' with all checks passed.

    Feature: ai-store-labs, Property 6: Assessment Result Consistency.
    """
    submission = dict(expected)

    result = _engine.evaluate(exercise_id, submission, expected)

    assert result.status == "pass"
    assert all(c.passed for c in result.checks)
    assert len(result.checks) >= 1
    assert len(result.feedback) > 0

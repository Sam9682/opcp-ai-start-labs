"""Property-based tests for validation result display completeness.

Feature: ai-store-labs, Property 14: Validation Result Display Completeness
Validates: Requirements 7.5

For any set of check results produced by the ExerciseValidator, the displayed
output contains every check name along with its individual pass/fail status.
No check is omitted from the display.

The display function under test is
``labs.scripts.validate_exercise.display_results``, which renders an
``ExerciseValidationResult`` (produced by ``ExerciseValidator``) to stdout.
These tests run without Docker, network, or live platform access: the
``ExerciseValidator`` only touches the (unused) platform client for display,
and ``display_results`` is pure stdout formatting.
"""

import io
from contextlib import redirect_stdout

from hypothesis import given, settings
from hypothesis import strategies as st

from labs.core.validators import ExerciseValidator
from labs.scripts.validate_exercise import display_results


class FakePlatformClient:
    """Lightweight fake platform client (no network / Docker)."""

    def query(self, endpoint: str, params=None) -> dict:
        return {"status": "ok"}


def _make_validator() -> ExerciseValidator:
    return ExerciseValidator(platform_client=FakePlatformClient())


# ---------------------------------------------------------------------------
# Generators
# ---------------------------------------------------------------------------

# JSON-serializable scalar values used as actual/expected for equality checks.
_scalars = st.one_of(
    st.none(),
    st.booleans(),
    st.integers(min_value=-1000, max_value=1000),
    st.text(alphabet="abcABC123_- ", max_size=12),
)

# Distinct, searchable step names. We constrain to a readable alphabet and
# require non-empty names so each name can be located unambiguously in the
# rendered output. Uniqueness is enforced at the list level below.
_step_names = st.text(
    alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_",
    min_size=1,
    max_size=16,
)


@st.composite
def _steps_with_assertions(draw):
    """Build a list of step dicts each carrying an embedded assertion.

    Each step gets a unique name so individual lines in the rendered output
    map back to exactly one check. Assertions are a mix of equality and
    containment so that the generated checks include both passing and failing
    results across examples.
    """
    names = draw(
        st.lists(_step_names, min_size=1, max_size=8, unique=True)
    )

    steps = []
    for name in names:
        assertion_type = draw(st.sampled_from(["equality", "containment"]))
        if assertion_type == "equality":
            actual = draw(_scalars)
            # Half the time use a matching expected value (passing check),
            # otherwise an independently drawn one (likely failing).
            if draw(st.booleans()):
                expected = actual
            else:
                expected = draw(_scalars)
            step = {
                "name": name,
                "actual": actual,
                "assertion": {"type": "equality", "expected": expected},
            }
        else:
            actual_text = draw(st.text(alphabet="abcABC123 ", max_size=20))
            if draw(st.booleans()) and actual_text:
                # Embed a real substring -> passing containment check.
                start = draw(st.integers(min_value=0, max_value=len(actual_text)))
                end = draw(
                    st.integers(min_value=start, max_value=len(actual_text))
                )
                expected = actual_text[start:end]
            else:
                expected = draw(st.text(alphabet="xyzXYZ789", min_size=1, max_size=6))
            step = {
                "name": name,
                "actual": actual_text,
                "assertion": {"type": "containment", "expected": expected},
            }
        steps.append(step)

    return steps


def _render(result) -> str:
    """Capture the stdout produced by display_results for a result."""
    buffer = io.StringIO()
    with redirect_stdout(buffer):
        display_results(result)
    return buffer.getvalue()


# Icons used by display_results for per-step pass/fail status.
_PASS_ICON = "\u2713"  # ✓
_FAIL_ICON = "\u2717"  # ✗


# ---------------------------------------------------------------------------
# Property 14 — Validation Result Display Completeness
# ---------------------------------------------------------------------------


@settings(max_examples=200)
@given(exercise_id=st.text(alphabet="exercise-0123456789", min_size=1, max_size=10),
       steps=_steps_with_assertions())
def test_property14_display_contains_every_check_name_and_status(exercise_id, steps):
    """Feature: ai-store-labs, Property 14: Validation Result Display Completeness.

    For any set of check results produced by the ExerciseValidator, the
    displayed output contains every check name together with its individual
    pass/fail status. No check is omitted.

    Validates: Requirements 7.5
    """
    validator = _make_validator()
    result = validator.validate_exercise(exercise_id, steps)

    # Sanity: one check result per input step.
    assert len(result.step_results) == len(steps)

    output = _render(result)
    lines = output.splitlines()

    for step_result in result.step_results:
        name = step_result.step_name
        expected_icon = _PASS_ICON if step_result.passed else _FAIL_ICON

        # The check name must appear in the display at all.
        assert name in output, (
            f"Check name {name!r} missing from displayed output."
        )

        # There must be a line that carries BOTH this check's name and its
        # correct pass/fail status icon — i.e. the per-check status is shown,
        # not just an aggregate.
        matching = [
            line for line in lines if name in line and expected_icon in line
        ]
        assert matching, (
            f"No display line shows check {name!r} with its "
            f"{'pass' if step_result.passed else 'fail'} status."
        )


@settings(max_examples=100)
@given(exercise_id=st.text(alphabet="exercise-0123456789", min_size=1, max_size=10),
       steps=_steps_with_assertions())
def test_property14_display_shows_one_status_line_per_check(exercise_id, steps):
    """Every check contributes a per-step status icon to the display.

    The number of per-step status icons rendered equals the number of checks,
    guaranteeing no check is dropped from or duplicated in the display.

    Feature: ai-store-labs, Property 14: Validation Result Display Completeness.
    Validates: Requirements 7.5
    """
    validator = _make_validator()
    result = validator.validate_exercise(exercise_id, steps)

    output = _render(result)
    lines = output.splitlines()

    # Per-step lines follow the pattern "  <icon> [<n>] <name>". Count lines
    # that begin a numbered step entry so the aggregate header icon is excluded.
    step_lines = [
        line
        for line in lines
        if (_PASS_ICON in line or _FAIL_ICON in line) and "[" in line and "]" in line
    ]

    assert len(step_lines) == len(result.step_results), (
        f"Expected {len(result.step_results)} per-check status lines, "
        f"found {len(step_lines)}."
    )

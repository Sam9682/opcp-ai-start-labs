"""Property-based tests for MIG profile alternative suggestion.

Feature: ai-store-labs, Property 15: MIG Profile Alternative Suggestion
Validates: Requirement 11.4

For any set of available MIG profiles and a requested profile that is
unavailable, the system suggests at least one alternative profile. The
suggested profile is the one closest in compute capability to the requested
profile among all available profiles.

These tests exercise the pure ``suggest_alternative_profiles`` helper and run
without Docker, network access, or a physical GPU.
"""

import importlib

from hypothesis import given, settings
from hypothesis import strategies as st

# The module directory name contains a hyphen (mig-gpu), which is invalid in a
# dotted `from ... import` path, so load it via importlib following the
# convention used by the other module-specific tests in this package.
_deploy = importlib.import_module(
    "labs.modules.mig-gpu.exercises.02_deploy_with_mig"
)
suggest_alternative_profiles = _deploy.suggest_alternative_profiles
_parse_compute_capability = _deploy._parse_compute_capability


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

# MIG compute capability is expressed as a fraction of a 7-way sliced GPU.
_SLICE_COUNTS = st.integers(min_value=1, max_value=7)


def _profile(slices: int, memory_mb: int, suffix: str) -> dict:
    """Build a MIG profile dict with an "n/7" compute capability."""
    return {
        "id": f"{slices}g.{memory_mb // 1024}gb-{suffix}",
        "compute_capability": f"{slices}/7",
        "memory_mb": memory_mb,
    }


# A list of available profiles, each with a distinct id, keyed by slice count.
available_profiles_strategy = st.lists(
    st.tuples(_SLICE_COUNTS, st.integers(min_value=5, max_value=80)),
    min_size=1,
    max_size=7,
).map(
    lambda specs: [
        _profile(slices, mem * 1024, str(i))
        for i, (slices, mem) in enumerate(specs)
    ]
)

requested_slices_strategy = _SLICE_COUNTS


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _min_distance(requested_cap: float, profiles: list[dict]) -> float:
    """Smallest capability distance between the request and any profile."""
    return min(
        abs(_parse_compute_capability(p["compute_capability"]) - requested_cap)
        for p in profiles
    )


# ---------------------------------------------------------------------------
# Property tests
# ---------------------------------------------------------------------------


@settings(max_examples=200)
@given(
    available=available_profiles_strategy,
    requested_slices=requested_slices_strategy,
)
def test_suggests_at_least_one_alternative_when_profiles_available(
    available, requested_slices
):
    """Feature: ai-store-labs, Property 15: MIG Profile Alternative Suggestion

    At least one alternative is always suggested whenever any profile is
    available, regardless of the requested (unavailable) profile.
    """
    requested = {
        "id": f"{requested_slices}g.unavailable",
        "compute_capability": f"{requested_slices}/7",
        "memory_mb": requested_slices * 5120,
    }

    suggestions = suggest_alternative_profiles(requested, available)

    assert len(suggestions) >= 1
    # Every suggestion is drawn from the available set, nothing invented.
    available_ids = {p["id"] for p in available}
    assert all(s["id"] in available_ids for s in suggestions)


@settings(max_examples=200)
@given(
    available=available_profiles_strategy,
    requested_slices=requested_slices_strategy,
)
def test_first_suggestion_is_closest_in_compute_capability(
    available, requested_slices
):
    """Feature: ai-store-labs, Property 15: MIG Profile Alternative Suggestion

    The first suggested profile is the one closest in compute capability to the
    requested profile among all available profiles.
    """
    requested = {
        "id": f"{requested_slices}g.unavailable",
        "compute_capability": f"{requested_slices}/7",
        "memory_mb": requested_slices * 5120,
    }
    requested_cap = _parse_compute_capability(requested["compute_capability"])

    suggestions = suggest_alternative_profiles(requested, available)

    best = suggestions[0]
    best_distance = abs(
        _parse_compute_capability(best["compute_capability"]) - requested_cap
    )
    assert best_distance == _min_distance(requested_cap, available)


@settings(max_examples=200)
@given(
    available=available_profiles_strategy,
    requested_slices=requested_slices_strategy,
)
def test_suggestions_sorted_by_ascending_distance(available, requested_slices):
    """Feature: ai-store-labs, Property 15: MIG Profile Alternative Suggestion

    Suggestions are ordered from closest to farthest in compute capability, so
    the capability distance is non-decreasing across the returned list.
    """
    requested = {
        "id": f"{requested_slices}g.unavailable",
        "compute_capability": f"{requested_slices}/7",
        "memory_mb": requested_slices * 5120,
    }
    requested_cap = _parse_compute_capability(requested["compute_capability"])

    suggestions = suggest_alternative_profiles(requested, available)

    distances = [
        abs(_parse_compute_capability(s["compute_capability"]) - requested_cap)
        for s in suggestions
    ]
    assert distances == sorted(distances)
    # Returned list preserves the full available set (nothing dropped).
    assert len(suggestions) == len(available)


def test_no_profiles_available_yields_no_suggestions():
    """Feature: ai-store-labs, Property 15: MIG Profile Alternative Suggestion

    With no available profiles there is nothing to suggest (edge case).
    """
    requested = {
        "id": "1g.5gb",
        "compute_capability": "1/7",
        "memory_mb": 5120,
    }
    assert suggest_alternative_profiles(requested, []) == []

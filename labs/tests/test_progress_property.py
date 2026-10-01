"""Property-based tests for the server-side ProgressTracker.

Feature: ai-store-labs, Property 7: Server-Side Progress Persistence Round-Trip
Validates: Requirement 3.4 (Server-side progress persistence)

These tests exercise ProgressTracker.record_completion() followed by
get_progress() across many generated progress entries. Persistence is backed
by a JSON file located under a per-example temporary directory, so the tests
run without Docker, network access, or live platform connectivity.
"""

from datetime import datetime, timezone

from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from labs.core.models import ExerciseStatus, ProgressEntry
from labs.core.progress import ProgressTracker


# Identifiers kept to a small, filesystem/JSON-safe alphabet. Non-empty so the
# tracker always has a concrete student/module/exercise to key on.
_identifiers = st.text(
    alphabet="abcdefghijklmnopqrstuvwxyz0123456789-_",
    min_size=1,
    max_size=12,
)

# Results must be valid ExerciseStatus values so the stored string round-trips
# back to the same enum member on read.
_results = st.sampled_from([status.value for status in ExerciseStatus])


@settings(max_examples=200, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    student_id=_identifiers,
    module_name=_identifiers,
    exercise_id=_identifiers,
    result=_results,
)
def test_progress_persistence_round_trip(
    tmp_path_factory, student_id, module_name, exercise_id, result
):
    """Feature: ai-store-labs, Property 7: Server-Side Progress Persistence Round-Trip.

    For any progress entry recorded through the ProgressTracker, querying for
    that student and module returns an entry whose student_id, module_name,
    exercise_id, and result match what was recorded, with a valid timestamp.
    """
    storage_path = str(tmp_path_factory.mktemp("progress") / "progress.json")
    tracker = ProgressTracker(storage_path)

    before = datetime.now(timezone.utc)
    tracker.record_completion(student_id, module_name, exercise_id, result)
    after = datetime.now(timezone.utc)

    entries = tracker.get_progress(student_id, module_name)

    # Exactly one entry was recorded for this (student, module, exercise).
    matching = [e for e in entries if e.exercise_id == exercise_id]
    assert len(matching) == 1, "recorded exercise must be retrievable exactly once"

    entry = matching[0]
    assert isinstance(entry, ProgressEntry)

    # Field-for-field round-trip of the recorded data.
    assert entry.student_id == student_id
    assert entry.module_name == module_name
    assert entry.exercise_id == exercise_id
    assert entry.result == ExerciseStatus(result)

    # Timestamp is a valid, timezone-aware datetime bracketed by the write.
    assert isinstance(entry.timestamp, datetime)
    assert entry.timestamp.tzinfo is not None
    assert before <= entry.timestamp <= after


@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    student_id=_identifiers,
    module_name=_identifiers,
    exercise_id=_identifiers,
    result=_results,
)
def test_progress_round_trip_survives_reload(
    tmp_path_factory, student_id, module_name, exercise_id, result
):
    """Recorded progress persists across a fresh ProgressTracker instance.

    Feature: ai-store-labs, Property 7: Server-Side Progress Persistence Round-Trip.

    A new tracker loading the same JSON store returns the same entry, proving
    the round-trip survives the persistence layer rather than in-memory state.
    """
    storage_path = str(tmp_path_factory.mktemp("progress") / "progress.json")

    writer = ProgressTracker(storage_path)
    writer.record_completion(student_id, module_name, exercise_id, result)

    reader = ProgressTracker(storage_path)
    entries = reader.get_progress(student_id, module_name)

    matching = [e for e in entries if e.exercise_id == exercise_id]
    assert len(matching) == 1

    entry = matching[0]
    assert entry.student_id == student_id
    assert entry.module_name == module_name
    assert entry.exercise_id == exercise_id
    assert entry.result == ExerciseStatus(result)
    assert isinstance(entry.timestamp, datetime)
    assert entry.timestamp.tzinfo is not None

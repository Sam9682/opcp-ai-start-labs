"""Unit tests for the ProgressTracker module."""

import json
import os
import tempfile
from datetime import datetime, timezone

import pytest

from labs.core.models import ExerciseStatus, ProgressEntry
from labs.core.progress import ProgressTracker


@pytest.fixture
def storage_path(tmp_path):
    """Provide a temporary file path for progress storage."""
    return str(tmp_path / "progress.json")


@pytest.fixture
def tracker(storage_path):
    """Create a fresh ProgressTracker instance."""
    return ProgressTracker(storage_path)


class TestRecordCompletion:
    """Tests for record_completion method."""

    def test_records_pass_result(self, tracker, storage_path):
        tracker.record_completion("student-001", "install-bare-metal", "01_prereqs", "pass")

        with open(storage_path, "r") as f:
            data = json.load(f)

        exercise = data["students"]["student-001"]["modules"]["install-bare-metal"]["exercises"]["01_prereqs"]
        assert exercise["result"] == "pass"
        assert "timestamp" in exercise

    def test_records_fail_result(self, tracker, storage_path):
        tracker.record_completion("student-001", "install-bare-metal", "01_prereqs", "fail")

        with open(storage_path, "r") as f:
            data = json.load(f)

        exercise = data["students"]["student-001"]["modules"]["install-bare-metal"]["exercises"]["01_prereqs"]
        assert exercise["result"] == "fail"

    def test_records_valid_iso_timestamp(self, tracker, storage_path):
        before = datetime.now(timezone.utc)
        tracker.record_completion("student-001", "install-bare-metal", "01_prereqs", "pass")
        after = datetime.now(timezone.utc)

        with open(storage_path, "r") as f:
            data = json.load(f)

        ts_str = data["students"]["student-001"]["modules"]["install-bare-metal"]["exercises"]["01_prereqs"]["timestamp"]
        ts = datetime.fromisoformat(ts_str)
        assert before <= ts <= after

    def test_multiple_exercises_in_module(self, tracker, storage_path):
        tracker.record_completion("student-001", "install-bare-metal", "01_prereqs", "pass")
        tracker.record_completion("student-001", "install-bare-metal", "02_docker", "pass")

        with open(storage_path, "r") as f:
            data = json.load(f)

        exercises = data["students"]["student-001"]["modules"]["install-bare-metal"]["exercises"]
        assert "01_prereqs" in exercises
        assert "02_docker" in exercises

    def test_multiple_students(self, tracker, storage_path):
        tracker.record_completion("student-001", "install-bare-metal", "01_prereqs", "pass")
        tracker.record_completion("student-002", "install-bare-metal", "01_prereqs", "fail")

        with open(storage_path, "r") as f:
            data = json.load(f)

        assert "student-001" in data["students"]
        assert "student-002" in data["students"]

    def test_overwrites_previous_result(self, tracker, storage_path):
        tracker.record_completion("student-001", "install-bare-metal", "01_prereqs", "fail")
        tracker.record_completion("student-001", "install-bare-metal", "01_prereqs", "pass")

        with open(storage_path, "r") as f:
            data = json.load(f)

        exercise = data["students"]["student-001"]["modules"]["install-bare-metal"]["exercises"]["01_prereqs"]
        assert exercise["result"] == "pass"

    def test_updates_completed_flag_all_pass(self, tracker, storage_path):
        tracker.record_completion("student-001", "install-bare-metal", "01_prereqs", "pass")
        tracker.record_completion("student-001", "install-bare-metal", "02_docker", "pass")

        with open(storage_path, "r") as f:
            data = json.load(f)

        assert data["students"]["student-001"]["modules"]["install-bare-metal"]["completed"] is True

    def test_completed_flag_false_when_any_fail(self, tracker, storage_path):
        tracker.record_completion("student-001", "install-bare-metal", "01_prereqs", "pass")
        tracker.record_completion("student-001", "install-bare-metal", "02_docker", "fail")

        with open(storage_path, "r") as f:
            data = json.load(f)

        assert data["students"]["student-001"]["modules"]["install-bare-metal"]["completed"] is False


class TestGetProgress:
    """Tests for get_progress method."""

    def test_empty_for_unknown_student(self, tracker):
        result = tracker.get_progress("unknown-student")
        assert result == []

    def test_returns_all_modules_when_no_filter(self, tracker):
        tracker.record_completion("student-001", "install-bare-metal", "01_prereqs", "pass")
        tracker.record_completion("student-001", "adding-applications", "01_cli", "fail")

        result = tracker.get_progress("student-001")
        assert len(result) == 2
        module_names = {entry.module_name for entry in result}
        assert module_names == {"install-bare-metal", "adding-applications"}

    def test_filters_by_module_name(self, tracker):
        tracker.record_completion("student-001", "install-bare-metal", "01_prereqs", "pass")
        tracker.record_completion("student-001", "adding-applications", "01_cli", "fail")

        result = tracker.get_progress("student-001", module_name="install-bare-metal")
        assert len(result) == 1
        assert result[0].module_name == "install-bare-metal"
        assert result[0].exercise_id == "01_prereqs"

    def test_returns_empty_for_unknown_module(self, tracker):
        tracker.record_completion("student-001", "install-bare-metal", "01_prereqs", "pass")

        result = tracker.get_progress("student-001", module_name="nonexistent")
        assert result == []

    def test_returns_progress_entry_with_correct_fields(self, tracker):
        tracker.record_completion("student-001", "install-bare-metal", "01_prereqs", "pass")

        result = tracker.get_progress("student-001", module_name="install-bare-metal")
        assert len(result) == 1

        entry = result[0]
        assert isinstance(entry, ProgressEntry)
        assert entry.student_id == "student-001"
        assert entry.module_name == "install-bare-metal"
        assert entry.exercise_id == "01_prereqs"
        assert entry.result == ExerciseStatus.PASS
        assert isinstance(entry.timestamp, datetime)

    def test_returns_fail_status(self, tracker):
        tracker.record_completion("student-001", "install-bare-metal", "01_prereqs", "fail")

        result = tracker.get_progress("student-001", module_name="install-bare-metal")
        assert result[0].result == ExerciseStatus.FAIL


class TestIsModuleComplete:
    """Tests for is_module_complete method."""

    def test_false_for_unknown_student(self, tracker):
        assert tracker.is_module_complete("unknown", "install-bare-metal") is False

    def test_false_for_unknown_module(self, tracker):
        tracker.record_completion("student-001", "install-bare-metal", "01_prereqs", "pass")
        assert tracker.is_module_complete("student-001", "nonexistent") is False

    def test_true_when_all_pass(self, tracker):
        tracker.record_completion("student-001", "install-bare-metal", "01_prereqs", "pass")
        tracker.record_completion("student-001", "install-bare-metal", "02_docker", "pass")
        assert tracker.is_module_complete("student-001", "install-bare-metal") is True

    def test_false_when_any_fail(self, tracker):
        tracker.record_completion("student-001", "install-bare-metal", "01_prereqs", "pass")
        tracker.record_completion("student-001", "install-bare-metal", "02_docker", "fail")
        assert tracker.is_module_complete("student-001", "install-bare-metal") is False

    def test_becomes_true_after_retry_passes(self, tracker):
        tracker.record_completion("student-001", "install-bare-metal", "01_prereqs", "pass")
        tracker.record_completion("student-001", "install-bare-metal", "02_docker", "fail")
        assert tracker.is_module_complete("student-001", "install-bare-metal") is False

        # Student retries and passes
        tracker.record_completion("student-001", "install-bare-metal", "02_docker", "pass")
        assert tracker.is_module_complete("student-001", "install-bare-metal") is True


class TestPersistence:
    """Tests for JSON persistence across instances."""

    def test_data_survives_reload(self, storage_path):
        tracker1 = ProgressTracker(storage_path)
        tracker1.record_completion("student-001", "install-bare-metal", "01_prereqs", "pass")

        # Create a new instance pointing to the same file
        tracker2 = ProgressTracker(storage_path)
        result = tracker2.get_progress("student-001")
        assert len(result) == 1
        assert result[0].exercise_id == "01_prereqs"

    def test_handles_missing_file_gracefully(self, tmp_path):
        path = str(tmp_path / "nonexistent" / "progress.json")
        tracker = ProgressTracker(path)
        assert tracker.get_progress("student-001") == []

        # Can still write
        tracker.record_completion("student-001", "install-bare-metal", "01_prereqs", "pass")
        assert os.path.exists(path)

    def test_handles_corrupted_json(self, tmp_path):
        path = str(tmp_path / "progress.json")
        with open(path, "w") as f:
            f.write("not valid json{{{")

        tracker = ProgressTracker(path)
        assert tracker.get_progress("student-001") == []

    def test_handles_json_missing_students_key(self, tmp_path):
        path = str(tmp_path / "progress.json")
        with open(path, "w") as f:
            json.dump({"other": "data"}, f)

        tracker = ProgressTracker(path)
        assert tracker.get_progress("student-001") == []

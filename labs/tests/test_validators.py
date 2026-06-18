"""Unit tests for ExerciseValidator."""

import pytest

from labs.core.validators import ExerciseValidator, ExerciseValidationResult
from labs.core.models import ExerciseStatus


class FakePlatformClient:
    """Fake platform client for testing."""

    def query(self, endpoint: str, params=None) -> dict:
        return {"status": "ok"}


@pytest.fixture
def validator():
    return ExerciseValidator(platform_client=FakePlatformClient())


class TestValidateStep:
    """Tests for validate_step method."""

    def test_equality_assertion_passes(self, validator):
        step = {"name": "check_status", "actual": "running"}
        assertion = {"type": "equality", "expected": "running"}
        result = validator.validate_step(step, assertion)
        assert result.passed is True
        assert result.step_name == "check_status"

    def test_equality_assertion_fails(self, validator):
        step = {"name": "check_status", "actual": "stopped"}
        assertion = {"type": "equality", "expected": "running"}
        result = validator.validate_step(step, assertion)
        assert result.passed is False
        assert "stopped" in result.message
        assert "running" in result.message

    def test_containment_assertion_passes(self, validator):
        step = {"name": "check_output", "actual": "Service started successfully on port 8080"}
        assertion = {"type": "containment", "expected": "successfully"}
        result = validator.validate_step(step, assertion)
        assert result.passed is True

    def test_containment_assertion_fails(self, validator):
        step = {"name": "check_output", "actual": "Service failed to start"}
        assertion = {"type": "containment", "expected": "successfully"}
        result = validator.validate_step(step, assertion)
        assert result.passed is False

    def test_containment_with_none_actual(self, validator):
        step = {"name": "check_output", "actual": None}
        assertion = {"type": "containment", "expected": "hello"}
        result = validator.validate_step(step, assertion)
        assert result.passed is False

    def test_containment_with_none_expected(self, validator):
        step = {"name": "check_output", "actual": "hello world"}
        assertion = {"type": "containment", "expected": None}
        result = validator.validate_step(step, assertion)
        assert result.passed is False

    def test_unknown_assertion_type(self, validator):
        step = {"name": "check_foo", "actual": "bar"}
        assertion = {"type": "regex", "expected": "b.*r"}
        result = validator.validate_step(step, assertion)
        assert result.passed is False
        assert "unknown assertion type" in result.message

    def test_default_assertion_type_is_equality(self, validator):
        step = {"name": "check_val", "actual": 42}
        assertion = {"expected": 42}
        result = validator.validate_step(step, assertion)
        assert result.passed is True

    def test_custom_field(self, validator):
        step = {"name": "check_code", "status_code": 200}
        assertion = {"type": "equality", "expected": 200, "field": "status_code"}
        result = validator.validate_step(step, assertion)
        assert result.passed is True

    def test_missing_field_returns_none(self, validator):
        step = {"name": "check_missing"}
        assertion = {"type": "equality", "expected": "something"}
        result = validator.validate_step(step, assertion)
        assert result.passed is False

    def test_unnamed_step(self, validator):
        step = {"actual": "value"}
        assertion = {"type": "equality", "expected": "value"}
        result = validator.validate_step(step, assertion)
        assert result.passed is True
        assert result.step_name == "unnamed_step"

    def test_equality_with_numeric_values(self, validator):
        step = {"name": "count", "actual": 5}
        assertion = {"type": "equality", "expected": 5}
        result = validator.validate_step(step, assertion)
        assert result.passed is True

    def test_equality_type_mismatch(self, validator):
        step = {"name": "count", "actual": "5"}
        assertion = {"type": "equality", "expected": 5}
        result = validator.validate_step(step, assertion)
        assert result.passed is False

    def test_details_populated(self, validator):
        step = {"name": "step1", "actual": "foo"}
        assertion = {"type": "equality", "expected": "bar"}
        result = validator.validate_step(step, assertion)
        assert result.details is not None
        assert result.details["assertion_type"] == "equality"
        assert result.details["expected"] == "bar"
        assert result.details["actual"] == "foo"


class TestValidateExercise:
    """Tests for validate_exercise method."""

    def test_all_steps_pass(self, validator):
        steps = [
            {"name": "step1", "actual": "a", "assertion": {"type": "equality", "expected": "a"}},
            {"name": "step2", "actual": "hello world", "assertion": {"type": "containment", "expected": "world"}},
        ]
        result = validator.validate_exercise("ex-001", steps)
        assert result.passed is True
        assert result.exercise_id == "ex-001"
        assert len(result.step_results) == 2
        assert result.status == ExerciseStatus.PASS

    def test_one_step_fails(self, validator):
        steps = [
            {"name": "step1", "actual": "a", "assertion": {"type": "equality", "expected": "a"}},
            {"name": "step2", "actual": "bad", "assertion": {"type": "equality", "expected": "good"}},
        ]
        result = validator.validate_exercise("ex-002", steps)
        assert result.passed is False
        assert result.status == ExerciseStatus.FAIL
        assert result.step_results[0].passed is True
        assert result.step_results[1].passed is False

    def test_empty_steps(self, validator):
        result = validator.validate_exercise("ex-empty", [])
        assert result.passed is True
        assert len(result.step_results) == 0

    def test_missing_assertion_key(self, validator):
        steps = [
            {"name": "step_no_assertion", "actual": "foo"},
        ]
        result = validator.validate_exercise("ex-003", steps)
        # With empty assertion dict, type defaults to equality, expected is None
        # actual is "foo", expected is None → fails
        assert result.passed is False

    def test_summary_property(self, validator):
        steps = [
            {"name": "s1", "actual": 1, "assertion": {"type": "equality", "expected": 1}},
            {"name": "s2", "actual": 2, "assertion": {"type": "equality", "expected": 3}},
            {"name": "s3", "actual": "x", "assertion": {"type": "containment", "expected": "x"}},
        ]
        result = validator.validate_exercise("ex-sum", steps)
        assert "2/3" in result.summary

"""Unit tests for the AssessmentEngine.

Requirements: 17.1, 17.2, 17.3
Validates: Requirement 3.3 (Assessment engine evaluates submissions)
"""

import pytest

from labs.core.assessment import AssessmentEngine
from labs.core.models import AssessmentResult, CheckResult


@pytest.fixture
def engine():
    """Create an AssessmentEngine instance."""
    return AssessmentEngine()


class TestEvaluateBasic:
    """Tests for basic AssessmentEngine.evaluate behavior."""

    def test_all_checks_pass(self, engine):
        """Overall status is 'pass' when all checks match."""
        submission = {"output": "hello", "code": 0}
        expected = {"output": "hello", "code": 0}

        result = engine.evaluate("ex-1", submission, expected)

        assert result.status == "pass"
        assert all(c.passed for c in result.checks)
        assert len(result.checks) == 2

    def test_one_check_fails(self, engine):
        """Overall status is 'fail' when any check does not match."""
        submission = {"output": "hello", "code": 1}
        expected = {"output": "hello", "code": 0}

        result = engine.evaluate("ex-2", submission, expected)

        assert result.status == "fail"
        passed_names = [c.name for c in result.checks if c.passed]
        failed_names = [c.name for c in result.checks if not c.passed]
        assert "output" in passed_names
        assert "code" in failed_names

    def test_all_checks_fail(self, engine):
        """Overall status is 'fail' when all checks fail."""
        submission = {"a": 1, "b": 2}
        expected = {"a": 99, "b": 88}

        result = engine.evaluate("ex-3", submission, expected)

        assert result.status == "fail"
        assert not any(c.passed for c in result.checks)

    def test_empty_expected_produces_structural_check(self, engine):
        """When expected is empty, a structural 'submission_received' check is added."""
        submission = {"data": "anything"}
        expected = {}

        result = engine.evaluate("ex-4", submission, expected)

        assert result.status == "pass"
        assert len(result.checks) == 1
        assert result.checks[0].name == "submission_received"
        assert result.checks[0].passed is True


class TestEvaluateResultStructure:
    """Tests for AssessmentResult structure completeness."""

    def test_result_is_assessment_result(self, engine):
        """evaluate() returns an AssessmentResult instance."""
        result = engine.evaluate("ex-1", {"a": 1}, {"a": 1})
        assert isinstance(result, AssessmentResult)

    def test_checks_list_is_never_empty(self, engine):
        """Result always contains a non-empty checks list."""
        result = engine.evaluate("ex-1", {}, {})
        assert len(result.checks) >= 1

    def test_feedback_is_non_empty_string(self, engine):
        """Result always contains a non-empty feedback string."""
        result = engine.evaluate("ex-1", {"x": 1}, {"x": 1})
        assert isinstance(result.feedback, str)
        assert len(result.feedback) > 0

    def test_feedback_on_failure_mentions_failed_checks(self, engine):
        """Failure feedback lists the names of failed checks."""
        result = engine.evaluate("ex-1", {"foo": "bar"}, {"foo": "baz"})
        assert "foo" in result.feedback

    def test_feedback_on_success_mentions_pass_count(self, engine):
        """Success feedback reports number of checks passed."""
        result = engine.evaluate("ex-1", {"a": 1, "b": 2}, {"a": 1, "b": 2})
        assert "2" in result.feedback


class TestCheckResultDetails:
    """Tests for individual CheckResult content."""

    def test_check_result_has_name(self, engine):
        """Each check result has the correct name from expected keys."""
        result = engine.evaluate("ex-1", {"status": "ok"}, {"status": "ok"})
        assert result.checks[0].name == "status"

    def test_check_result_passed_true(self, engine):
        """Check result reports passed=True when values match."""
        result = engine.evaluate("ex-1", {"val": 42}, {"val": 42})
        assert result.checks[0].passed is True

    def test_check_result_passed_false(self, engine):
        """Check result reports passed=False when values differ."""
        result = engine.evaluate("ex-1", {"val": 0}, {"val": 42})
        assert result.checks[0].passed is False

    def test_check_result_feedback_on_pass(self, engine):
        """Passing check feedback contains the check name."""
        result = engine.evaluate("ex-1", {"key": "v"}, {"key": "v"})
        assert "key" in result.checks[0].feedback

    def test_check_result_feedback_on_fail(self, engine):
        """Failing check feedback shows expected and actual values."""
        result = engine.evaluate("ex-1", {"key": "wrong"}, {"key": "right"})
        feedback = result.checks[0].feedback
        assert "right" in feedback
        assert "wrong" in feedback

    def test_check_result_expected_and_actual_fields(self, engine):
        """Check result includes expected and actual repr strings."""
        result = engine.evaluate("ex-1", {"n": 5}, {"n": 10})
        check = result.checks[0]
        assert check.expected == repr(10)
        assert check.actual == repr(5)


class TestEdgeCases:
    """Tests for edge case submissions."""

    def test_missing_key_in_submission(self, engine):
        """Missing key in submission results in None actual value and failure."""
        submission = {}
        expected = {"status": "running"}

        result = engine.evaluate("ex-1", submission, expected)

        assert result.status == "fail"
        assert result.checks[0].passed is False
        assert result.checks[0].actual == repr(None)

    def test_extra_key_in_submission_ignored(self, engine):
        """Extra keys in submission do not affect assessment."""
        submission = {"status": "ok", "extra": "data"}
        expected = {"status": "ok"}

        result = engine.evaluate("ex-1", submission, expected)

        assert result.status == "pass"
        assert len(result.checks) == 1

    def test_none_vs_none_passes(self, engine):
        """None == None should pass as a check."""
        result = engine.evaluate("ex-1", {"x": None}, {"x": None})
        assert result.status == "pass"

    def test_type_mismatch_string_vs_int(self, engine):
        """Different types with same representation fail (strict equality)."""
        result = engine.evaluate("ex-1", {"val": "1"}, {"val": 1})
        assert result.status == "fail"

    def test_list_equality(self, engine):
        """Lists are compared by equality."""
        result = engine.evaluate(
            "ex-1",
            {"items": [1, 2, 3]},
            {"items": [1, 2, 3]},
        )
        assert result.status == "pass"

    def test_dict_equality(self, engine):
        """Nested dicts are compared by equality."""
        result = engine.evaluate(
            "ex-1",
            {"config": {"a": 1}},
            {"config": {"a": 1}},
        )
        assert result.status == "pass"

    def test_multiple_failed_checks_all_listed(self, engine):
        """All failed check names appear in feedback when multiple fail."""
        submission = {"a": "wrong_a", "b": "wrong_b", "c": "correct"}
        expected = {"a": "right_a", "b": "right_b", "c": "correct"}

        result = engine.evaluate("ex-1", submission, expected)

        assert result.status == "fail"
        assert "a" in result.feedback
        assert "b" in result.feedback

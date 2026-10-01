"""Tests for the Agent Execution Trace Reading lab module.

Covers the four annotation exercises with correct, partial, and incorrect
submissions, hint availability, and config registration.
"""

import importlib
from pathlib import Path

import pytest

from labs.core.config_loader import ConfigLoader

_MODULE = "labs.modules.trace-reading"
trace = importlib.import_module(f"{_MODULE}.setup.sample_trace")
ex01 = importlib.import_module(f"{_MODULE}.exercises.ex01_label_phases")
ex02 = importlib.import_module(f"{_MODULE}.exercises.ex02_identify_tools")
ex03 = importlib.import_module(f"{_MODULE}.exercises.ex03_stopping_criterion")
ex04 = importlib.import_module(f"{_MODULE}.exercises.ex04_guardrail_trigger")
sol01 = importlib.import_module(f"{_MODULE}.solutions.01_solution")
sol02 = importlib.import_module(f"{_MODULE}.solutions.02_solution")
sol03 = importlib.import_module(f"{_MODULE}.solutions.03_solution")
sol04 = importlib.import_module(f"{_MODULE}.solutions.04_solution")


def run(exercise, submission):
    exercise.setup()
    result = exercise.execute(submission)
    checks = exercise.validate(result)
    exercise.teardown()
    return result, checks


def passed(checks, name):
    for c in checks:
        if c["name"] == name:
            return c["passed"]
    raise AssertionError(f"check '{name}' not found")


def all_passed(checks):
    return all(c["passed"] for c in checks)


# ---------------------------------------------------------------------------
# Trace fixture integrity
# ---------------------------------------------------------------------------


class TestTraceFixture:
    def test_every_step_has_a_phase(self):
        for step in trace.TRACE:
            assert step["phase"] in {"think", "act", "observe"}

    def test_learner_view_hides_phase(self):
        for step in trace.learner_view():
            assert "phase" not in step
            assert "id" in step and "content" in step

    def test_tools_in_order_includes_retries(self):
        # deploy_app was retried: it appears multiple times.
        tools = trace.tools_in_order()
        assert tools.count("deploy_app") == 3
        assert tools[0] == "list_apps"


# ---------------------------------------------------------------------------
# Exercise 1 — Label the loop phases
# ---------------------------------------------------------------------------


class TestLabelPhases:
    def test_reference_solution_passes(self):
        ex = ex01.LabelPhasesExercise()
        _, checks = run(ex, sol01.submission())
        assert all_passed(checks)

    def test_partial_labels_fail_coverage(self):
        ex = ex01.LabelPhasesExercise()
        # Only label the first two steps.
        _, checks = run(ex, {"labels": {"s1": "think", "s2": "act"}})
        assert passed(checks, "all_steps_labeled") is False
        assert passed(checks, "all_phases_correct") is False

    def test_invalid_label_value_flagged(self):
        ex = ex01.LabelPhasesExercise()
        labels = dict(sol01.submission()["labels"])
        labels["s1"] = "reason"  # not a valid phase
        _, checks = run(ex, {"labels": labels})
        assert passed(checks, "labels_are_valid") is False

    def test_one_wrong_phase_fails_correctness_only(self):
        ex = ex01.LabelPhasesExercise()
        labels = dict(sol01.submission()["labels"])
        labels["s2"] = "observe"  # s2 is actually 'act'
        _, checks = run(ex, {"labels": labels})
        assert passed(checks, "labels_are_valid") is True
        assert passed(checks, "all_steps_labeled") is True
        assert passed(checks, "all_phases_correct") is False

    def test_hints_available(self):
        assert len(ex01.LabelPhasesExercise().get_hints()) >= 3


# ---------------------------------------------------------------------------
# Exercise 2 — Identify the tools
# ---------------------------------------------------------------------------


class TestIdentifyTools:
    def test_reference_solution_passes(self):
        ex = ex02.IdentifyToolsExercise()
        _, checks = run(ex, sol02.submission())
        assert all_passed(checks)

    def test_right_set_wrong_order_fails_order_only(self):
        ex = ex02.IdentifyToolsExercise()
        # Correct distinct set, but collapse the retries → order mismatch.
        _, checks = run(ex, {"tools_in_order": ["deploy_app", "list_apps"]})
        assert passed(checks, "all_tools_identified") is True
        assert passed(checks, "tools_in_correct_order") is False

    def test_missing_tool_fails_set(self):
        ex = ex02.IdentifyToolsExercise()
        _, checks = run(ex, {"tools_in_order": ["list_apps"]})
        assert passed(checks, "all_tools_identified") is False

    def test_hints_available(self):
        assert len(ex02.IdentifyToolsExercise().get_hints()) >= 3


# ---------------------------------------------------------------------------
# Exercise 3 — Name the stopping criterion
# ---------------------------------------------------------------------------


class TestStoppingCriterion:
    def test_reference_solution_passes(self):
        ex = ex03.StoppingCriterionExercise()
        _, checks = run(ex, sol03.submission())
        assert all_passed(checks)

    def test_alias_accepted(self):
        ex = ex03.StoppingCriterionExercise()
        _, checks = run(ex, {
            "stopping_criterion": "repeated error",
            "fired_at_step": "s14",
        })
        assert passed(checks, "stopping_criterion_identified") is True

    def test_wrong_criterion_fails(self):
        ex = ex03.StoppingCriterionExercise()
        _, checks = run(ex, {
            "stopping_criterion": "goal_achieved",
            "fired_at_step": "s14",
        })
        assert passed(checks, "stopping_criterion_identified") is False
        assert passed(checks, "firing_step_identified") is True

    def test_wrong_step_fails(self):
        ex = ex03.StoppingCriterionExercise()
        _, checks = run(ex, {
            "stopping_criterion": "error_threshold",
            "fired_at_step": "s6",
        })
        assert passed(checks, "firing_step_identified") is False


# ---------------------------------------------------------------------------
# Exercise 4 — Spot the guardrail trigger
# ---------------------------------------------------------------------------


class TestGuardrailTrigger:
    def test_reference_solution_passes(self):
        ex = ex04.GuardrailTriggerExercise()
        _, checks = run(ex, sol04.submission())
        assert all_passed(checks)

    def test_wrong_layer_fails(self):
        ex = ex04.GuardrailTriggerExercise()
        _, checks = run(ex, {
            "guardrail_layer": "kill_switch",
            "prevented_action": "another deploy retry",
        })
        assert passed(checks, "guardrail_layer_identified") is False

    def test_vague_prevented_action_fails(self):
        ex = ex04.GuardrailTriggerExercise()
        _, checks = run(ex, {
            "guardrail_layer": "operational_limits",
            "prevented_action": "stuff",
        })
        assert passed(checks, "prevented_action_identified") is False

    def test_hints_available(self):
        assert len(ex04.GuardrailTriggerExercise().get_hints()) >= 3


# ---------------------------------------------------------------------------
# Config registration
# ---------------------------------------------------------------------------


class TestConfigRegistration:
    @pytest.fixture
    def config(self, mock_urlopen):
        config_path = (
            Path(__file__).resolve().parents[1] / "config" / "lab_config.yaml"
        )
        return ConfigLoader(str(config_path)).load()

    def test_module_registered_with_prereq(self, config):
        module = next(
            (m for m in config.modules if m.id == "trace-reading"), None
        )
        assert module is not None
        assert "opcp-explorer-connect" in module.prerequisites

    def test_dag_remains_acyclic(self, config):
        # load() raised already if cyclic; also assert no self-prereq.
        for m in config.modules:
            assert m.id not in m.prerequisites

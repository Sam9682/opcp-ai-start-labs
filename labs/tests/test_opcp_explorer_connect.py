"""Tests for the opcp-explorer Connectivity lab module.

Covers the three exercises' validate() logic in simulated mode (and live-mode
parameter handling), plus a config test asserting the module registers in
lab_config.yaml and the prerequisite DAG stays acyclic.
"""

import importlib
from pathlib import Path

import pytest

from labs.core.config_loader import ConfigLoader

# Exercises are loaded via importlib because the module directory name contains
# hyphens, which are not valid in a `from ... import` dotted path.
_MODULE = "labs.modules.opcp-explorer-connect"
ex01 = importlib.import_module(f"{_MODULE}.exercises.ex01_discover_surface")
ex02 = importlib.import_module(f"{_MODULE}.exercises.ex02_authenticate")
ex03 = importlib.import_module(f"{_MODULE}.exercises.ex03_tool_call")
sol01 = importlib.import_module(f"{_MODULE}.solutions.01_solution")
sol02 = importlib.import_module(f"{_MODULE}.solutions.02_solution")
sol03 = importlib.import_module(f"{_MODULE}.solutions.03_solution")


def run(exercise, submission):
    """Helper: run execute()->validate() and return (result, checks)."""
    exercise.setup()
    result = exercise.execute(submission)
    checks = exercise.validate(result)
    exercise.teardown()
    return result, checks


def passed(checks, name):
    for c in checks:
        if c["name"] == name:
            return c["passed"]
    raise AssertionError(f"check '{name}' not found in {[c['name'] for c in checks]}")


def all_passed(checks):
    return all(c["passed"] for c in checks)


# ---------------------------------------------------------------------------
# Exercise 1 — Discover the tool surface
# ---------------------------------------------------------------------------


class TestDiscoverSurface:
    def test_reference_solution_passes(self):
        ex = ex01.DiscoverSurfaceExercise()
        _, checks = run(ex, sol01.submission())
        assert all_passed(checks)

    def test_unknown_tool_fails(self):
        ex = ex01.DiscoverSurfaceExercise()
        _, checks = run(ex, {
            "interface": "api",
            "selected_tools": ["list_apps", "not_a_tool"],
        })
        assert passed(checks, "no_unknown_tools") is False

    def test_invalid_interface_fails(self):
        ex = ex01.DiscoverSurfaceExercise()
        _, checks = run(ex, {
            "interface": "grpc",
            "selected_tools": ["list_apps"],
        })
        assert passed(checks, "valid_interface") is False

    def test_empty_selection_fails(self):
        ex = ex01.DiscoverSurfaceExercise()
        _, checks = run(ex, {"interface": "cli", "selected_tools": []})
        assert passed(checks, "selected_at_least_one_tool") is False

    def test_cli_interface_resolves_invocations(self):
        ex = ex01.DiscoverSurfaceExercise()
        _, checks = run(ex, {
            "interface": "cli",
            "selected_tools": ["list_apps", "deploy_app"],
        })
        assert passed(checks, "invocations_resolved") is True


# ---------------------------------------------------------------------------
# Exercise 2 — Authenticate with a scoped token
# ---------------------------------------------------------------------------


class TestAuthenticate:
    def test_reference_solution_passes(self):
        ex = ex02.AuthenticateExercise()
        _, checks = run(ex, sol02.submission())
        assert all_passed(checks)

    def test_raw_secret_detected(self):
        ex = ex02.AuthenticateExercise()
        _, checks = run(ex, {
            "token_ref": "sk-livesecrettokenvalue1234567890",
            "requested_scopes": ["apps:read"],
            "tools": ["list_apps"],
        })
        assert passed(checks, "no_raw_secret") is False

    def test_unknown_scope_fails(self):
        ex = ex02.AuthenticateExercise()
        _, checks = run(ex, {
            "token_ref": "env:OPCP_TOKEN",
            "requested_scopes": ["apps:read", "root:all"],
            "tools": ["list_apps"],
        })
        assert passed(checks, "scopes_known") is False

    def test_missing_scope_for_tool_fails(self):
        ex = ex02.AuthenticateExercise()
        # deploy_app needs apps:write + deploy:execute, but we only grant read.
        _, checks = run(ex, {
            "token_ref": "env:OPCP_TOKEN",
            "requested_scopes": ["apps:read"],
            "tools": ["deploy_app"],
        })
        assert passed(checks, "scopes_cover_tools") is False

    def test_excess_scope_breaks_least_privilege(self):
        ex = ex02.AuthenticateExercise()
        _, checks = run(ex, {
            "token_ref": "env:OPCP_TOKEN",
            "requested_scopes": ["apps:read", "billing:read"],
            "tools": ["list_apps"],  # only needs apps:read
        })
        assert passed(checks, "least_privilege") is False

    def test_live_mode_requires_base_url(self):
        ex = ex02.AuthenticateExercise()
        _, checks = run(ex, {
            "token_ref": "env:OPCP_TOKEN",
            "requested_scopes": ["apps:read"],
            "tools": ["list_apps"],
            "live_mode": True,
            "base_url": "not-a-url",
        })
        assert passed(checks, "live_connection_params") is False

    def test_live_mode_accepts_https_base_url(self):
        ex = ex02.AuthenticateExercise()
        _, checks = run(ex, {
            "token_ref": "env:OPCP_TOKEN",
            "requested_scopes": ["apps:read"],
            "tools": ["list_apps"],
            "live_mode": True,
            "base_url": "https://opcp.example.com",
        })
        assert all_passed(checks)


# ---------------------------------------------------------------------------
# Exercise 3 — Perform a basic tool call
# ---------------------------------------------------------------------------


class TestToolCall:
    def test_reference_solution_passes(self):
        ex = ex03.ToolCallExercise()
        result, checks = run(ex, sol03.submission())
        assert result["status"] == "executed"
        assert all_passed(checks)

    def test_list_apps_simulated_returns_apps(self):
        ex = ex03.ToolCallExercise()
        result, checks = run(ex, {
            "tool": "list_apps",
            "interface": "api",
            "params": {},
        })
        assert result["status"] == "executed"
        assert "apps" in result["response"]
        assert all_passed(checks)

    def test_unknown_tool_fails(self):
        ex = ex03.ToolCallExercise()
        _, checks = run(ex, {
            "tool": "nuke_everything",
            "interface": "api",
            "params": {},
        })
        assert passed(checks, "tool_call_constructed") is False

    def test_missing_required_params_fails(self):
        ex = ex03.ToolCallExercise()
        # deploy_app requires repo_url and app_name.
        _, checks = run(ex, {
            "tool": "deploy_app",
            "interface": "api",
            "params": {"app_name": "x"},
        })
        assert passed(checks, "tool_call_constructed") is False

    def test_live_mode_defers_to_adapter(self):
        ex = ex03.ToolCallExercise()
        result, checks = run(ex, {
            "tool": "list_apps",
            "interface": "api",
            "params": {},
            "live_mode": True,
            "base_url": "https://opcp.example.com",
        })
        assert result["status"] == "deferred_to_live_adapter"
        assert result["response"] is None
        assert passed(checks, "live_call_well_formed") is True


# ---------------------------------------------------------------------------
# Config registration
# ---------------------------------------------------------------------------


class TestConfigRegistration:
    @pytest.fixture
    def config(self, mock_urlopen):
        # mock_urlopen keeps the loader's endpoint reachability check offline.
        config_path = (
            Path(__file__).resolve().parents[1] / "config" / "lab_config.yaml"
        )
        return ConfigLoader(str(config_path)).load()

    def test_module_registered(self, config):
        ids = [m.id for m in config.modules]
        assert "opcp-explorer-connect" in ids

    def test_module_resource_limits_in_range(self, config):
        module = next(
            m for m in config.modules if m.id == "opcp-explorer-connect"
        )
        rl = module.resource_limits
        assert 0.5 <= rl.cpu_cores <= 4.0
        assert 128 <= rl.memory_mb <= 4096
        assert 1 <= rl.time_minutes <= 120

    def test_opcp_explorer_endpoints_present(self, config):
        assert "opcp_explorer_api" in config.endpoints
        assert config.endpoints["opcp_explorer_api"].startswith("https://")

    def test_dag_remains_acyclic(self, config):
        # ConfigLoader.load() raises on a cyclic DAG; reaching here proves it.
        loader = ConfigLoader(
            str(Path(__file__).resolve().parents[1] / "config" / "lab_config.yaml")
        )
        raw = {
            "version": config.version,
            "modules": [
                {
                    "id": m.id,
                    "name": m.name,
                    "order": m.order,
                    "prerequisites": m.prerequisites,
                    "session_time_limit_minutes": m.session_time_limit_minutes,
                    "resource_limits": {
                        "cpu_cores": m.resource_limits.cpu_cores,
                        "memory_mb": m.resource_limits.memory_mb,
                        "time_minutes": m.resource_limits.time_minutes,
                    },
                }
                for m in config.modules
            ],
            "endpoints": config.endpoints,
            "global": {
                "max_concurrent_containers": config.max_concurrent_containers,
                "memory_ceiling_mb": config.memory_ceiling_mb,
                "cpu_ceiling_cores": config.cpu_ceiling_cores,
            },
        }
        valid, errors = loader.validate(raw)
        assert valid, errors

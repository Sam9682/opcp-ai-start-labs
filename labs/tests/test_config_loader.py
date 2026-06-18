"""Unit tests for the ConfigLoader."""

import os
import tempfile
import time
import threading
from pathlib import Path

import pytest
import yaml

from labs.core.config_loader import ConfigLoader
from labs.core.models import LabConfig, LabModule, ResourceLimits


@pytest.fixture
def valid_config_dict():
    """Return a minimal valid configuration dictionary."""
    return {
        "version": "1.0",
        "modules": [
            {
                "id": "mod-a",
                "name": "Module A",
                "order": 1,
                "prerequisites": [],
                "session_time_limit_minutes": 60,
                "resource_limits": {
                    "cpu_cores": 1.0,
                    "memory_mb": 512,
                    "time_minutes": 30,
                },
            }
        ],
        "endpoints": {
            "platform_api": "https://example.com/api",
            "platform_cli": "/usr/local/bin/cli.py",
        },
        "global": {
            "max_concurrent_containers": 10,
            "memory_ceiling_mb": 16384,
            "cpu_ceiling_cores": 8.0,
        },
    }


@pytest.fixture
def config_file(valid_config_dict, tmp_path):
    """Write valid config to a temp file and return its path."""
    config_path = tmp_path / "lab_config.yaml"
    config_path.write_text(yaml.dump(valid_config_dict), encoding="utf-8")
    return str(config_path)


class TestConfigLoaderLoad:
    """Tests for ConfigLoader.load()."""

    def test_load_valid_config(self, config_file):
        loader = ConfigLoader(config_file)
        config = loader.load()

        assert isinstance(config, LabConfig)
        assert config.version == "1.0"
        assert len(config.modules) == 1
        assert config.modules[0].id == "mod-a"
        assert config.modules[0].name == "Module A"
        assert config.modules[0].order == 1
        assert config.modules[0].prerequisites == []
        assert config.modules[0].session_time_limit_minutes == 60
        assert config.modules[0].resource_limits.cpu_cores == 1.0
        assert config.modules[0].resource_limits.memory_mb == 512
        assert config.modules[0].resource_limits.time_minutes == 30
        assert config.endpoints["platform_api"] == "https://example.com/api"
        assert config.max_concurrent_containers == 10
        assert config.memory_ceiling_mb == 16384
        assert config.cpu_ceiling_cores == 8.0

    def test_load_file_not_found(self, tmp_path):
        loader = ConfigLoader(str(tmp_path / "nonexistent.yaml"))
        with pytest.raises(FileNotFoundError):
            loader.load()

    def test_load_invalid_yaml(self, tmp_path):
        config_path = tmp_path / "bad.yaml"
        config_path.write_text("{ invalid yaml: [", encoding="utf-8")

        loader = ConfigLoader(str(config_path))
        with pytest.raises(ValueError, match="Invalid YAML syntax"):
            loader.load()

    def test_load_sets_current_config(self, config_file):
        loader = ConfigLoader(config_file)
        assert loader.current_config is None
        config = loader.load()
        assert loader.current_config is config

    def test_load_with_prerequisites(self, tmp_path):
        config_dict = {
            "version": "1.0",
            "modules": [
                {
                    "id": "mod-a",
                    "name": "Module A",
                    "order": 1,
                    "prerequisites": [],
                    "session_time_limit_minutes": 60,
                    "resource_limits": {
                        "cpu_cores": 1.0,
                        "memory_mb": 512,
                        "time_minutes": 30,
                    },
                },
                {
                    "id": "mod-b",
                    "name": "Module B",
                    "order": 2,
                    "prerequisites": ["mod-a"],
                    "session_time_limit_minutes": 90,
                    "resource_limits": {
                        "cpu_cores": 2.0,
                        "memory_mb": 1024,
                        "time_minutes": 60,
                    },
                },
            ],
            "endpoints": {
                "api": "https://example.com/api",
            },
            "global": {
                "max_concurrent_containers": 5,
                "memory_ceiling_mb": 8192,
                "cpu_ceiling_cores": 4.0,
            },
        }
        config_path = tmp_path / "config.yaml"
        config_path.write_text(yaml.dump(config_dict), encoding="utf-8")

        loader = ConfigLoader(str(config_path))
        config = loader.load()

        assert len(config.modules) == 2
        assert config.modules[1].prerequisites == ["mod-a"]


class TestConfigLoaderValidate:
    """Tests for ConfigLoader.validate()."""

    def test_valid_config(self, valid_config_dict):
        loader = ConfigLoader("dummy_path")
        valid, errors = loader.validate(valid_config_dict)
        assert valid is True
        assert errors == []

    def test_missing_top_level_key(self, valid_config_dict):
        del valid_config_dict["modules"]
        loader = ConfigLoader("dummy_path")
        valid, errors = loader.validate(valid_config_dict)
        assert valid is False
        assert any("modules" in e for e in errors)

    def test_circular_dependency(self):
        config = {
            "version": "1.0",
            "modules": [
                {
                    "id": "a",
                    "name": "A",
                    "order": 1,
                    "prerequisites": ["b"],
                    "session_time_limit_minutes": 60,
                    "resource_limits": {
                        "cpu_cores": 1.0,
                        "memory_mb": 512,
                        "time_minutes": 30,
                    },
                },
                {
                    "id": "b",
                    "name": "B",
                    "order": 2,
                    "prerequisites": ["a"],
                    "session_time_limit_minutes": 60,
                    "resource_limits": {
                        "cpu_cores": 1.0,
                        "memory_mb": 512,
                        "time_minutes": 30,
                    },
                },
            ],
            "endpoints": {"api": "https://example.com/api"},
            "global": {
                "max_concurrent_containers": 10,
                "memory_ceiling_mb": 16384,
                "cpu_ceiling_cores": 8.0,
            },
        }
        loader = ConfigLoader("dummy_path")
        valid, errors = loader.validate(config)
        assert valid is False
        assert any("Circular" in e for e in errors)

    def test_undefined_prerequisite(self, valid_config_dict):
        valid_config_dict["modules"][0]["prerequisites"] = ["nonexistent"]
        loader = ConfigLoader("dummy_path")
        valid, errors = loader.validate(valid_config_dict)
        assert valid is False
        assert any("undefined module" in e for e in errors)

    def test_invalid_url_format(self, valid_config_dict):
        valid_config_dict["endpoints"]["bad_url"] = "ftp://not-http.com"
        loader = ConfigLoader("dummy_path")
        valid, errors = loader.validate(valid_config_dict)
        assert valid is False
        assert any("HTTP/HTTPS" in e for e in errors)

    def test_session_time_below_minimum(self, valid_config_dict):
        valid_config_dict["modules"][0]["session_time_limit_minutes"] = 4
        loader = ConfigLoader("dummy_path")
        valid, errors = loader.validate(valid_config_dict)
        assert valid is False
        assert any("session_time_limit_minutes" in e for e in errors)

    def test_session_time_above_maximum(self, valid_config_dict):
        valid_config_dict["modules"][0]["session_time_limit_minutes"] = 481
        loader = ConfigLoader("dummy_path")
        valid, errors = loader.validate(valid_config_dict)
        assert valid is False
        assert any("session_time_limit_minutes" in e for e in errors)

    def test_cpu_cores_below_minimum(self, valid_config_dict):
        valid_config_dict["modules"][0]["resource_limits"]["cpu_cores"] = 0.1
        loader = ConfigLoader("dummy_path")
        valid, errors = loader.validate(valid_config_dict)
        assert valid is False
        assert any("cpu_cores" in e for e in errors)

    def test_cpu_cores_above_maximum(self, valid_config_dict):
        valid_config_dict["modules"][0]["resource_limits"]["cpu_cores"] = 5.0
        loader = ConfigLoader("dummy_path")
        valid, errors = loader.validate(valid_config_dict)
        assert valid is False
        assert any("cpu_cores" in e for e in errors)

    def test_memory_below_minimum(self, valid_config_dict):
        valid_config_dict["modules"][0]["resource_limits"]["memory_mb"] = 64
        loader = ConfigLoader("dummy_path")
        valid, errors = loader.validate(valid_config_dict)
        assert valid is False
        assert any("memory_mb" in e for e in errors)

    def test_memory_above_maximum(self, valid_config_dict):
        valid_config_dict["modules"][0]["resource_limits"]["memory_mb"] = 5000
        loader = ConfigLoader("dummy_path")
        valid, errors = loader.validate(valid_config_dict)
        assert valid is False
        assert any("memory_mb" in e for e in errors)

    def test_time_minutes_below_minimum(self, valid_config_dict):
        valid_config_dict["modules"][0]["resource_limits"]["time_minutes"] = 0
        loader = ConfigLoader("dummy_path")
        valid, errors = loader.validate(valid_config_dict)
        assert valid is False
        assert any("time_minutes" in e for e in errors)

    def test_time_minutes_above_maximum(self, valid_config_dict):
        valid_config_dict["modules"][0]["resource_limits"]["time_minutes"] = 121
        loader = ConfigLoader("dummy_path")
        valid, errors = loader.validate(valid_config_dict)
        assert valid is False
        assert any("time_minutes" in e for e in errors)

    def test_max_containers_below_minimum(self, valid_config_dict):
        valid_config_dict["global"]["max_concurrent_containers"] = 0
        loader = ConfigLoader("dummy_path")
        valid, errors = loader.validate(valid_config_dict)
        assert valid is False
        assert any("max_concurrent_containers" in e for e in errors)

    def test_max_containers_above_maximum(self, valid_config_dict):
        valid_config_dict["global"]["max_concurrent_containers"] = 101
        loader = ConfigLoader("dummy_path")
        valid, errors = loader.validate(valid_config_dict)
        assert valid is False
        assert any("max_concurrent_containers" in e for e in errors)

    def test_memory_ceiling_below_minimum(self, valid_config_dict):
        valid_config_dict["global"]["memory_ceiling_mb"] = 64
        loader = ConfigLoader("dummy_path")
        valid, errors = loader.validate(valid_config_dict)
        assert valid is False
        assert any("memory_ceiling_mb" in e for e in errors)

    def test_memory_ceiling_above_maximum(self, valid_config_dict):
        valid_config_dict["global"]["memory_ceiling_mb"] = 65537
        loader = ConfigLoader("dummy_path")
        valid, errors = loader.validate(valid_config_dict)
        assert valid is False
        assert any("memory_ceiling_mb" in e for e in errors)

    def test_cpu_ceiling_below_minimum(self, valid_config_dict):
        valid_config_dict["global"]["cpu_ceiling_cores"] = 0.1
        loader = ConfigLoader("dummy_path")
        valid, errors = loader.validate(valid_config_dict)
        assert valid is False
        assert any("cpu_ceiling_cores" in e for e in errors)

    def test_cpu_ceiling_above_maximum(self, valid_config_dict):
        valid_config_dict["global"]["cpu_ceiling_cores"] = 65.0
        loader = ConfigLoader("dummy_path")
        valid, errors = loader.validate(valid_config_dict)
        assert valid is False
        assert any("cpu_ceiling_cores" in e for e in errors)

    def test_too_many_modules(self, valid_config_dict):
        # Create 51 modules
        valid_config_dict["modules"] = [
            {
                "id": f"mod-{i}",
                "name": f"Module {i}",
                "order": i,
                "prerequisites": [],
                "session_time_limit_minutes": 60,
                "resource_limits": {
                    "cpu_cores": 1.0,
                    "memory_mb": 512,
                    "time_minutes": 30,
                },
            }
            for i in range(51)
        ]
        loader = ConfigLoader("dummy_path")
        valid, errors = loader.validate(valid_config_dict)
        assert valid is False
        assert any("Maximum 50" in e for e in errors)

    def test_duplicate_module_ids(self, valid_config_dict):
        valid_config_dict["modules"].append(
            valid_config_dict["modules"][0].copy()
        )
        loader = ConfigLoader("dummy_path")
        valid, errors = loader.validate(valid_config_dict)
        assert valid is False
        assert any("duplicate" in e for e in errors)

    def test_boundary_values_valid(self):
        """Test that boundary values are accepted."""
        config = {
            "version": "1.0",
            "modules": [
                {
                    "id": "boundary-test",
                    "name": "Boundary Test",
                    "order": 1,
                    "prerequisites": [],
                    "session_time_limit_minutes": 5,  # min
                    "resource_limits": {
                        "cpu_cores": 0.5,     # min
                        "memory_mb": 128,     # min
                        "time_minutes": 1,    # min
                    },
                }
            ],
            "endpoints": {
                "api": "https://example.com",
            },
            "global": {
                "max_concurrent_containers": 1,    # min
                "memory_ceiling_mb": 128,          # min
                "cpu_ceiling_cores": 0.5,          # min
            },
        }
        loader = ConfigLoader("dummy_path")
        valid, errors = loader.validate(config)
        assert valid is True
        assert errors == []

    def test_boundary_values_max_valid(self):
        """Test that max boundary values are accepted."""
        config = {
            "version": "1.0",
            "modules": [
                {
                    "id": "boundary-max",
                    "name": "Max Boundary",
                    "order": 1,
                    "prerequisites": [],
                    "session_time_limit_minutes": 480,  # max
                    "resource_limits": {
                        "cpu_cores": 4.0,      # max
                        "memory_mb": 4096,     # max
                        "time_minutes": 120,   # max
                    },
                }
            ],
            "endpoints": {
                "api": "http://example.com",
            },
            "global": {
                "max_concurrent_containers": 100,   # max
                "memory_ceiling_mb": 65536,         # max
                "cpu_ceiling_cores": 64.0,          # max
            },
        }
        loader = ConfigLoader("dummy_path")
        valid, errors = loader.validate(config)
        assert valid is True
        assert errors == []


class TestConfigLoaderWatch:
    """Tests for ConfigLoader.watch() hot-reload functionality."""

    def test_watch_reloads_on_valid_change(self, tmp_path):
        """Test that valid config changes are applied."""
        config_dict = {
            "version": "1.0",
            "modules": [
                {
                    "id": "mod-a",
                    "name": "Module A",
                    "order": 1,
                    "prerequisites": [],
                    "session_time_limit_minutes": 60,
                    "resource_limits": {
                        "cpu_cores": 1.0,
                        "memory_mb": 512,
                        "time_minutes": 30,
                    },
                }
            ],
            "endpoints": {"api": "https://example.com/api"},
            "global": {
                "max_concurrent_containers": 10,
                "memory_ceiling_mb": 16384,
                "cpu_ceiling_cores": 8.0,
            },
        }

        config_path = tmp_path / "lab_config.yaml"
        config_path.write_text(yaml.dump(config_dict), encoding="utf-8")

        loader = ConfigLoader(str(config_path))
        loader.load()

        callback_called = threading.Event()
        received_config = []

        def on_reload(config):
            received_config.append(config)
            callback_called.set()

        loader.watch(on_reload)

        try:
            # Modify the config
            config_dict["global"]["max_concurrent_containers"] = 20
            time.sleep(0.5)  # Give watcher time to start
            config_path.write_text(yaml.dump(config_dict), encoding="utf-8")

            # Wait up to 10 seconds (requirement: within 10 seconds)
            assert callback_called.wait(timeout=10), (
                "Config reload callback not called within 10 seconds"
            )
            assert len(received_config) == 1
            assert received_config[0].max_concurrent_containers == 20
        finally:
            loader.stop_watching()

    def test_watch_rejects_invalid_change(self, tmp_path):
        """Test that invalid config changes are rejected."""
        config_dict = {
            "version": "1.0",
            "modules": [
                {
                    "id": "mod-a",
                    "name": "Module A",
                    "order": 1,
                    "prerequisites": [],
                    "session_time_limit_minutes": 60,
                    "resource_limits": {
                        "cpu_cores": 1.0,
                        "memory_mb": 512,
                        "time_minutes": 30,
                    },
                }
            ],
            "endpoints": {"api": "https://example.com/api"},
            "global": {
                "max_concurrent_containers": 10,
                "memory_ceiling_mb": 16384,
                "cpu_ceiling_cores": 8.0,
            },
        }

        config_path = tmp_path / "lab_config.yaml"
        config_path.write_text(yaml.dump(config_dict), encoding="utf-8")

        loader = ConfigLoader(str(config_path))
        original_config = loader.load()

        callback_called = threading.Event()

        def on_reload(config):
            callback_called.set()

        loader.watch(on_reload)

        try:
            # Write invalid config
            time.sleep(0.5)
            config_path.write_text("{ invalid yaml: [", encoding="utf-8")

            # Callback should NOT be called for invalid config
            assert not callback_called.wait(timeout=5), (
                "Callback should not be called for invalid config"
            )

            # Previous config should be retained
            assert loader.current_config == original_config
        finally:
            loader.stop_watching()

    def test_stop_watching(self, config_file):
        """Test that stop_watching stops the observer."""
        loader = ConfigLoader(config_file)
        loader.load()
        loader.watch(lambda c: None)
        loader.stop_watching()
        # Should not raise even when called twice
        loader.stop_watching()


class TestConfigLoaderDAG:
    """Tests for DAG integrity validation."""

    def test_simple_dag_valid(self):
        config = {
            "version": "1.0",
            "modules": [
                {
                    "id": "a",
                    "name": "A",
                    "order": 1,
                    "prerequisites": [],
                    "session_time_limit_minutes": 60,
                    "resource_limits": {
                        "cpu_cores": 1.0,
                        "memory_mb": 512,
                        "time_minutes": 30,
                    },
                },
                {
                    "id": "b",
                    "name": "B",
                    "order": 2,
                    "prerequisites": ["a"],
                    "session_time_limit_minutes": 60,
                    "resource_limits": {
                        "cpu_cores": 1.0,
                        "memory_mb": 512,
                        "time_minutes": 30,
                    },
                },
                {
                    "id": "c",
                    "name": "C",
                    "order": 3,
                    "prerequisites": ["a", "b"],
                    "session_time_limit_minutes": 60,
                    "resource_limits": {
                        "cpu_cores": 1.0,
                        "memory_mb": 512,
                        "time_minutes": 30,
                    },
                },
            ],
            "endpoints": {"api": "https://example.com"},
            "global": {
                "max_concurrent_containers": 10,
                "memory_ceiling_mb": 16384,
                "cpu_ceiling_cores": 8.0,
            },
        }
        loader = ConfigLoader("dummy_path")
        valid, errors = loader.validate(config)
        assert valid is True

    def test_self_referencing_module(self):
        config = {
            "version": "1.0",
            "modules": [
                {
                    "id": "a",
                    "name": "A",
                    "order": 1,
                    "prerequisites": ["a"],
                    "session_time_limit_minutes": 60,
                    "resource_limits": {
                        "cpu_cores": 1.0,
                        "memory_mb": 512,
                        "time_minutes": 30,
                    },
                },
            ],
            "endpoints": {"api": "https://example.com"},
            "global": {
                "max_concurrent_containers": 10,
                "memory_ceiling_mb": 16384,
                "cpu_ceiling_cores": 8.0,
            },
        }
        loader = ConfigLoader("dummy_path")
        valid, errors = loader.validate(config)
        assert valid is False
        assert any("Circular" in e for e in errors)

    def test_three_node_cycle(self):
        config = {
            "version": "1.0",
            "modules": [
                {
                    "id": "a",
                    "name": "A",
                    "order": 1,
                    "prerequisites": ["c"],
                    "session_time_limit_minutes": 60,
                    "resource_limits": {
                        "cpu_cores": 1.0,
                        "memory_mb": 512,
                        "time_minutes": 30,
                    },
                },
                {
                    "id": "b",
                    "name": "B",
                    "order": 2,
                    "prerequisites": ["a"],
                    "session_time_limit_minutes": 60,
                    "resource_limits": {
                        "cpu_cores": 1.0,
                        "memory_mb": 512,
                        "time_minutes": 30,
                    },
                },
                {
                    "id": "c",
                    "name": "C",
                    "order": 3,
                    "prerequisites": ["b"],
                    "session_time_limit_minutes": 60,
                    "resource_limits": {
                        "cpu_cores": 1.0,
                        "memory_mb": 512,
                        "time_minutes": 30,
                    },
                },
            ],
            "endpoints": {"api": "https://example.com"},
            "global": {
                "max_concurrent_containers": 10,
                "memory_ceiling_mb": 16384,
                "cpu_ceiling_cores": 8.0,
            },
        }
        loader = ConfigLoader("dummy_path")
        valid, errors = loader.validate(config)
        assert valid is False
        assert any("Circular" in e for e in errors)


class TestConfigLoaderRealFile:
    """Tests that load the actual lab_config.yaml from the project."""

    def test_load_project_config(self):
        """Verify the actual lab_config.yaml file is valid."""
        config_path = (
            Path(__file__).parent.parent / "config" / "lab_config.yaml"
        )
        if not config_path.exists():
            pytest.skip("lab_config.yaml not found")

        loader = ConfigLoader(str(config_path))
        config = loader.load()

        assert config.version == "1.0"
        assert len(config.modules) == 9
        assert config.max_concurrent_containers == 10
        assert config.memory_ceiling_mb == 16384
        assert config.cpu_ceiling_cores == 8.0

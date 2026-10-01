"""Property-based tests for the ConfigLoader.

Feature: ai-store-labs

Covers:
    Property 4: Configuration Validation Round-Trip
        Validates: Requirements 3.2, 16.1, 16.2, 16.3
    Property 5: Invalid Configuration Rejection
        Validates: Requirements 16.5

These tests run without Docker, network access, or a live platform. The
autouse ``block_network_access`` fixture (see conftest.py) blocks outbound
HTTP; ConfigLoader.load() tolerates unreachable endpoints by design, so no
network is required. All configs are generated in-memory and written to
pytest ``tmp_path`` temp files.
"""

import copy

import pytest
import yaml
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from labs.core.config_loader import ConfigLoader
from labs.core.models import LabConfig


# ---------------------------------------------------------------------------
# Strategies for generating VALID LabConfig dictionaries.
#
# Validity constraints enforced by ConfigLoader (see config_loader.py):
#   - 1..50 modules, unique non-empty string ids
#   - module.order: positive int
#   - module.session_time_limit_minutes: 5..480
#   - resource_limits.cpu_cores: 0.5..4.0
#   - resource_limits.memory_mb: 128..4096
#   - resource_limits.time_minutes: 1..120
#   - prerequisites: list of existing module ids forming a DAG
#   - endpoints: HTTP/HTTPS URLs (or absolute file paths)
#   - global.max_concurrent_containers: 1..100
#   - global.memory_ceiling_mb: 128..65536
#   - global.cpu_ceiling_cores: 0.5..64
# ---------------------------------------------------------------------------

# Safe URL path/host fragments (letters/digits only) to keep urlparse happy.
_url_token = st.text(
    alphabet="abcdefghijklmnopqrstuvwxyz0123456789", min_size=1, max_size=8
)


@st.composite
def http_url(draw):
    """A well-formed HTTP/HTTPS URL with scheme and netloc."""
    scheme = draw(st.sampled_from(["http", "https"]))
    host = draw(_url_token)
    tld = draw(st.sampled_from(["com", "io", "net", "example"]))
    path = draw(st.lists(_url_token, min_size=0, max_size=3))
    url = f"{scheme}://{host}.{tld}"
    if path:
        url += "/" + "/".join(path)
    return url


def _resource_limits(draw):
    """Draw a valid resource_limits mapping."""
    return {
        "cpu_cores": draw(
            st.floats(min_value=0.5, max_value=4.0).map(lambda x: round(x, 2))
        ),
        "memory_mb": draw(st.integers(min_value=128, max_value=4096)),
        "time_minutes": draw(st.integers(min_value=1, max_value=120)),
    }


@st.composite
def valid_config(draw):
    """Generate a valid LabConfig dict whose modules form a DAG.

    Prerequisites of module i only reference earlier modules (index < i),
    which guarantees the dependency graph is acyclic regardless of ordering.
    """
    num_modules = draw(st.integers(min_value=1, max_value=6))
    module_ids = [f"mod-{i}" for i in range(num_modules)]

    modules = []
    for i, mid in enumerate(module_ids):
        earlier = module_ids[:i]
        if earlier:
            prereqs = draw(
                st.lists(
                    st.sampled_from(earlier),
                    max_size=len(earlier),
                    unique=True,
                )
            )
        else:
            prereqs = []
        modules.append(
            {
                "id": mid,
                "name": f"Module {i}",
                "order": i + 1,
                "prerequisites": prereqs,
                "session_time_limit_minutes": draw(
                    st.integers(min_value=5, max_value=480)
                ),
                "resource_limits": _resource_limits(draw),
            }
        )

    # 1..4 endpoints, all well-formed HTTP/HTTPS URLs.
    num_endpoints = draw(st.integers(min_value=1, max_value=4))
    endpoints = {
        f"endpoint_{j}": draw(http_url()) for j in range(num_endpoints)
    }

    return {
        "version": draw(st.sampled_from(["1.0", "1.1", "2.0"])),
        "modules": modules,
        "endpoints": endpoints,
        "global": {
            "max_concurrent_containers": draw(
                st.integers(min_value=1, max_value=100)
            ),
            "memory_ceiling_mb": draw(
                st.integers(min_value=128, max_value=65536)
            ),
            "cpu_ceiling_cores": draw(
                st.floats(min_value=0.5, max_value=64.0).map(
                    lambda x: round(x, 2)
                )
            ),
        },
    }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _write_config(tmp_path, config_dict, name="lab_config.yaml"):
    path = tmp_path / name
    path.write_text(yaml.dump(config_dict), encoding="utf-8")
    return str(path)


def _config_to_comparable(config: LabConfig) -> dict:
    """Reduce a LabConfig to a plain dict for structural equivalence checks."""
    return {
        "version": config.version,
        "modules": [
            {
                "id": m.id,
                "name": m.name,
                "order": m.order,
                "prerequisites": list(m.prerequisites),
                "session_time_limit_minutes": m.session_time_limit_minutes,
                "resource_limits": {
                    "cpu_cores": float(m.resource_limits.cpu_cores),
                    "memory_mb": int(m.resource_limits.memory_mb),
                    "time_minutes": int(m.resource_limits.time_minutes),
                },
            }
            for m in config.modules
        ],
        "endpoints": dict(config.endpoints),
        "max_concurrent_containers": config.max_concurrent_containers,
        "memory_ceiling_mb": config.memory_ceiling_mb,
        "cpu_ceiling_cores": float(config.cpu_ceiling_cores),
    }


def _expected_comparable(raw: dict) -> dict:
    """Expected comparable form derived directly from the raw config dict."""
    return {
        "version": raw["version"],
        "modules": [
            {
                "id": m["id"],
                "name": m["name"],
                "order": int(m["order"]),
                "prerequisites": list(m["prerequisites"]),
                "session_time_limit_minutes": int(
                    m["session_time_limit_minutes"]
                ),
                "resource_limits": {
                    "cpu_cores": float(m["resource_limits"]["cpu_cores"]),
                    "memory_mb": int(m["resource_limits"]["memory_mb"]),
                    "time_minutes": int(m["resource_limits"]["time_minutes"]),
                },
            }
            for m in raw["modules"]
        ],
        "endpoints": dict(raw["endpoints"]),
        "max_concurrent_containers": int(
            raw["global"]["max_concurrent_containers"]
        ),
        "memory_ceiling_mb": int(raw["global"]["memory_ceiling_mb"]),
        "cpu_ceiling_cores": float(raw["global"]["cpu_ceiling_cores"]),
    }


# ---------------------------------------------------------------------------
# Property 4: Configuration Validation Round-Trip
# ---------------------------------------------------------------------------


class TestProperty4ConfigRoundTrip:
    """Feature: ai-store-labs, Property 4: Configuration Validation Round-Trip.

    Validates: Requirements 3.2, 16.1, 16.2, 16.3
    """

    @settings(
        max_examples=150,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    @given(raw=valid_config())
    def test_valid_config_round_trips(self, raw, tmp_path):
        """A valid config serialized to YAML loads to an equivalent object.

        All DAG-valid module orderings are accepted and all HTTP/HTTPS URLs
        pass validation.
        """
        config_path = _write_config(tmp_path, raw)
        loader = ConfigLoader(config_path)

        config = loader.load()

        assert isinstance(config, LabConfig)
        assert _config_to_comparable(config) == _expected_comparable(raw)
        # Loaded config is retained as the current config.
        assert loader.current_config is config

    @settings(
        max_examples=150,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    @given(raw=valid_config())
    def test_valid_config_passes_validate(self, raw):
        """validate() reports a valid config with no errors."""
        loader = ConfigLoader("dummy_path")
        valid, errors = loader.validate(raw)
        assert valid is True
        assert errors == []


# ---------------------------------------------------------------------------
# Property 5: Invalid Configuration Rejection
# ---------------------------------------------------------------------------


# Each corrupter mutates a VALID config in-place to introduce exactly one
# class of invalidity, and returns a substring expected in the error message.
def _corrupt_circular(raw):
    # Introduce a guaranteed cycle. With one module, self-reference it.
    # With 2+, force a mutual dependency between the first and last modules.
    ids = [m["id"] for m in raw["modules"]]
    if len(ids) == 1:
        raw["modules"][0]["prerequisites"] = [ids[0]]
    else:
        raw["modules"][0]["prerequisites"] = [ids[-1]]
        raw["modules"][-1]["prerequisites"] = [ids[0]]
    return "Circular"


def _corrupt_undefined_prereq(raw):
    raw["modules"][0]["prerequisites"] = ["does-not-exist"]
    return "undefined module"


def _corrupt_bad_url(raw):
    key = next(iter(raw["endpoints"]))
    raw["endpoints"][key] = "ftp://not-http.example"
    return "HTTP/HTTPS"


def _corrupt_cpu_out_of_range(raw):
    raw["modules"][0]["resource_limits"]["cpu_cores"] = 99.0
    return "cpu_cores"


def _corrupt_memory_out_of_range(raw):
    raw["modules"][0]["resource_limits"]["memory_mb"] = 1
    return "memory_mb"


def _corrupt_time_out_of_range(raw):
    raw["modules"][0]["resource_limits"]["time_minutes"] = 9999
    return "time_minutes"


def _corrupt_session_time_out_of_range(raw):
    raw["modules"][0]["session_time_limit_minutes"] = 1
    return "session_time_limit_minutes"


def _corrupt_max_containers(raw):
    raw["global"]["max_concurrent_containers"] = 0
    return "max_concurrent_containers"


_CORRUPTERS = [
    _corrupt_circular,
    _corrupt_undefined_prereq,
    _corrupt_bad_url,
    _corrupt_cpu_out_of_range,
    _corrupt_memory_out_of_range,
    _corrupt_time_out_of_range,
    _corrupt_session_time_out_of_range,
    _corrupt_max_containers,
]


class TestProperty5InvalidConfigRejection:
    """Feature: ai-store-labs, Property 5: Invalid Configuration Rejection.

    Validates: Requirements 16.5
    """

    @settings(
        max_examples=150,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    @given(
        raw=valid_config(),
        corrupter=st.sampled_from(_CORRUPTERS),
    )
    def test_invalid_config_rejected_and_previous_retained(
        self, raw, corrupter, tmp_path
    ):
        """An invalid change is rejected, retains the prior valid config, and
        the error identifies the specific validation failure."""
        # Load a valid config first and remember it.
        good_path = _write_config(tmp_path, raw, name="lab_config.yaml")
        loader = ConfigLoader(good_path)
        good_config = loader.load()
        assert loader.current_config is good_config

        # Build an invalid variant and attempt to load it.
        bad_raw = copy.deepcopy(raw)
        expected_fragment = corrupter(bad_raw)
        bad_path = _write_config(tmp_path, bad_raw, name="bad_config.yaml")
        bad_loader = ConfigLoader(bad_path)
        # Preserve the previously loaded valid config on the same loader to
        # verify retention semantics explicitly.
        loader._config_path = bad_loader._config_path

        with pytest.raises(ValueError) as exc_info:
            loader.load()

        message = str(exc_info.value)
        assert "validation failed" in message or "Invalid YAML" in message
        assert expected_fragment in message
        # The previously loaded valid config is retained unchanged.
        assert loader.current_config is good_config

    @settings(
        max_examples=150,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    @given(raw=valid_config())
    def test_invalid_yaml_syntax_rejected(self, raw, tmp_path):
        """Malformed YAML syntax is rejected with an identifying error, and
        the prior valid config is retained."""
        good_path = _write_config(tmp_path, raw)
        loader = ConfigLoader(good_path)
        good_config = loader.load()

        # Overwrite with syntactically invalid YAML.
        (tmp_path / "lab_config.yaml").write_text(
            "{ invalid: yaml: [[[", encoding="utf-8"
        )

        with pytest.raises(ValueError) as exc_info:
            loader.load()

        assert "Invalid YAML syntax" in str(exc_info.value)
        assert loader.current_config is good_config

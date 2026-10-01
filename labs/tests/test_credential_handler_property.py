"""Property-based tests for CredentialHandler.

Feature: ai-store-labs, Property 10: Credential Retrieval and Non-Leakage

**Validates: Requirements 3.8**

Property 10: For any credential key/value pair loaded from environment
variables or a secrets file, the CredentialHandler returns the exact value
when queried by key. Additionally, for any operation that produces log
output, the log output never contains any credential value stored in the
handler.

These tests run without Docker, network, or a live platform: environment
variables are set via monkeypatch and secrets are written to temp files.
"""

import contextlib
import json
import logging
import os

from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

import pytest

from labs.core.credential_handler import CredentialHandler, _RedactingFilter


def _strip_redacting_filters():
    """Remove every CredentialHandler redacting filter from shared loggers.

    CredentialHandler installs a redacting filter on the module and root
    loggers on construction and never removes it. Other test modules build
    handlers too, so stale filters can linger on the shared root logger and
    interfere with (and slow down) these property tests. Clearing all of them
    gives each example a clean, isolated logging state.
    """
    for logger_obj in (
        logging.getLogger("labs.core.credential_handler"),
        logging.getLogger(),
    ):
        logger_obj.filters = [
            f for f in logger_obj.filters
            if not isinstance(f, _RedactingFilter)
        ]


@pytest.fixture(autouse=True)
def _clean_logger_filters():
    """Ensure no stray redacting filters bleed into or out of each test."""
    _strip_redacting_filters()
    try:
        yield
    finally:
        _strip_redacting_filters()


@contextlib.contextmanager
def _temporary_env(env_vars):
    """Set the given env vars for the duration of the block, then restore.

    Hypothesis runs many examples within a single test function call, so a
    function-scoped ``monkeypatch`` fixture would leak state between examples.
    This helper sets and fully restores os.environ per example instead.
    """
    saved = {key: os.environ.get(key) for key in env_vars}
    try:
        for key, value in env_vars.items():
            os.environ[key] = value
        yield
    finally:
        for key, previous in saved.items():
            if previous is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = previous


@contextlib.contextmanager
def _handler(secrets_file=None):
    """Build a CredentialHandler and remove its redacting filters on exit.

    CredentialHandler installs a redacting filter on the module and root
    loggers and never removes it. Hypothesis runs many examples per function,
    so without per-example cleanup the filters accumulate and logging slows
    quadratically. This context manager removes exactly the filter the handler
    added once the example completes.
    """
    # Start from a clean slate so only this handler's filter is active, then
    # remove it again afterwards to keep per-example logging state isolated.
    _strip_redacting_filters()
    handler = CredentialHandler(secrets_file=secrets_file)
    try:
        yield handler
    finally:
        _strip_redacting_filters()

# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

# Credential key names: valid environment-variable-style identifiers.
# Env var names on most platforms are uppercase letters, digits, underscores,
# and must not start with a digit. We also avoid "=" and NUL which os.environ
# rejects.
_key_strategy = st.from_regex(r"[A-Z_][A-Z0-9_]{0,30}", fullmatch=True)

# Credential values: non-empty printable strings. We exclude characters that
# cannot appear in environment variable values (NUL) and keep them non-empty
# so that redaction/containment checks are meaningful.
_value_strategy = st.text(
    alphabet=st.characters(
        min_codepoint=33,
        max_codepoint=126,
    ),
    min_size=1,
    max_size=40,
)

# A mapping of distinct credential keys to values.
_credentials_strategy = st.dictionaries(
    keys=_key_strategy,
    values=_value_strategy,
    min_size=1,
    max_size=8,
)

# The placeholder the handler substitutes for redacted values.
_REDACTION_PLACEHOLDER = "***REDACTED***"


def _log_secret(target_logger, value):
    """Log a credential value as a pre-formatted literal message.

    The message is passed with no logging ``%``-style args so that the logging
    machinery performs no interpolation. This matters because a secret value
    may itself contain ``%`` or ``*`` characters, which would raise a
    formatting error if used as (or alongside) a format template. The goal is
    to force the raw secret into the log stream and confirm the handler redacts
    it rather than to exercise logging's formatting.
    """
    # Pass the value as the sole message with no logging args. With no args,
    # logging performs no %-interpolation, so a secret containing "%" or "*"
    # is safe. Using no surrounding filler text guarantees that any letters
    # remaining after placeholder stripping belong to a leaked secret and not
    # to scaffolding.
    target_logger.info(value)


def _assert_no_value_leaked(records, values):
    """Assert that no credential value survives into the emitted log output.

    Each credential value is logged as the entire message with no surrounding
    text, so a correctly redacting handler produces records consisting only of
    redaction placeholders. We strip those placeholders before checking so the
    placeholder's own letters (R, E, D, A, ...) cannot be mistaken for a leaked
    single-character secret. Anything remaining is a real leak.
    """
    emitted = "\n".join(record.getMessage() for record in records)
    emitted = emitted.replace(_REDACTION_PLACEHOLDER, "")
    for value in values:
        assert value not in emitted, (
            f"credential value {value!r} leaked into log output"
        )


# ---------------------------------------------------------------------------
# Part 1: Retrieval returns the exact stored value
# ---------------------------------------------------------------------------


@settings(max_examples=150, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(credentials=_credentials_strategy)
def test_get_credential_returns_exact_value_from_secrets_file(
    credentials, tmp_path_factory
):
    """get_credential returns the exact value loaded from a secrets file.

    Feature: ai-store-labs, Property 10: Credential Retrieval and Non-Leakage
    Validates: Requirements 3.8
    """
    secrets_file = tmp_path_factory.mktemp("secrets") / "secrets.json"
    secrets_file.write_text(json.dumps(credentials), encoding="utf-8")

    with _handler(secrets_file=str(secrets_file)) as handler:
        for key, expected_value in credentials.items():
            assert handler.get_credential(key) == expected_value


@settings(max_examples=150)
@given(credentials=_credentials_strategy)
def test_get_credential_returns_exact_value_from_env(credentials):
    """get_credential returns the exact value loaded from env vars.

    Feature: ai-store-labs, Property 10: Credential Retrieval and Non-Leakage
    Validates: Requirements 3.8
    """
    with _temporary_env(credentials), _handler() as handler:
        for key, expected_value in credentials.items():
            assert handler.get_credential(key) == expected_value


@settings(max_examples=150, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    env_credentials=_credentials_strategy,
    file_credentials=_credentials_strategy,
)
def test_env_takes_priority_and_values_are_exact(
    env_credentials, file_credentials, tmp_path_factory
):
    """When a key is in both sources, env wins; values are always exact.

    Feature: ai-store-labs, Property 10: Credential Retrieval and Non-Leakage
    Validates: Requirements 3.8
    """
    secrets_file = tmp_path_factory.mktemp("secrets") / "secrets.json"
    secrets_file.write_text(json.dumps(file_credentials), encoding="utf-8")

    with _temporary_env(env_credentials), _handler(
        secrets_file=str(secrets_file)
    ) as handler:
        for key in set(env_credentials) | set(file_credentials):
            expected = env_credentials.get(key, file_credentials.get(key))
            assert handler.get_credential(key) == expected


# ---------------------------------------------------------------------------
# Part 2: Credential values never leak into log output
# ---------------------------------------------------------------------------


@settings(max_examples=150, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(credentials=_credentials_strategy)
def test_secrets_file_values_never_leak_into_logs(
    credentials, tmp_path_factory, caplog
):
    """Log output never contains credential values loaded from a file.

    Feature: ai-store-labs, Property 10: Credential Retrieval and Non-Leakage
    Validates: Requirements 3.8
    """
    secrets_file = tmp_path_factory.mktemp("secrets") / "secrets.json"
    secrets_file.write_text(json.dumps(credentials), encoding="utf-8")

    test_logger = logging.getLogger("labs.core.credential_handler")

    with _handler(secrets_file=str(secrets_file)) as handler:
        caplog.clear()
        with caplog.at_level(
            logging.DEBUG, logger="labs.core.credential_handler"
        ):
            # Attempt to leak every credential value through a log operation.
            # Each value is logged as the entire message with no surrounding
            # text, so the post-redaction record contains nothing but
            # redaction placeholders unless the real secret leaked.
            for key, value in credentials.items():
                handler.get_credential(key)
                _log_secret(test_logger, value)

        _assert_no_value_leaked(caplog.records, credentials.values())


@settings(max_examples=150, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(credentials=_credentials_strategy)
def test_env_values_never_leak_into_logs_after_retrieval(credentials, caplog):
    """Log output never contains credential values from env after retrieval.

    Feature: ai-store-labs, Property 10: Credential Retrieval and Non-Leakage
    Validates: Requirements 3.8
    """
    test_logger = logging.getLogger("labs.core.credential_handler")

    with _temporary_env(credentials), _handler() as handler:
        caplog.clear()
        with caplog.at_level(
            logging.DEBUG, logger="labs.core.credential_handler"
        ):
            for key, value in credentials.items():
                # Retrieval registers the env value for redaction.
                handler.get_credential(key)
                _log_secret(test_logger, value)

        _assert_no_value_leaked(caplog.records, credentials.values())

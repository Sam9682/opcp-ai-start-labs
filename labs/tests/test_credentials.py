"""Unit tests for CredentialHandler."""

import json
import logging
import os
import tempfile

import pytest

from labs.core.credential_handler import CredentialHandler


class TestCredentialHandlerInit:
    """Tests for CredentialHandler initialization."""

    def test_init_without_secrets_file(self):
        """Handler initializes successfully without a secrets file."""
        handler = CredentialHandler()
        assert handler._secrets == {}

    def test_init_with_nonexistent_secrets_file(self):
        """Handler initializes with warning when secrets file doesn't exist."""
        handler = CredentialHandler(secrets_file="/nonexistent/path.json")
        assert handler._secrets == {}

    def test_init_with_valid_secrets_file(self, tmp_path):
        """Handler loads credentials from a valid JSON secrets file."""
        secrets = {"API_KEY": "secret123", "TOKEN": "tok456"}
        secrets_file = tmp_path / "secrets.json"
        secrets_file.write_text(json.dumps(secrets))

        handler = CredentialHandler(secrets_file=str(secrets_file))
        assert handler._secrets == secrets

    def test_init_with_invalid_json_secrets_file(self, tmp_path):
        """Handler handles invalid JSON in secrets file gracefully."""
        secrets_file = tmp_path / "secrets.json"
        secrets_file.write_text("not valid json {{{")

        handler = CredentialHandler(secrets_file=str(secrets_file))
        assert handler._secrets == {}

    def test_init_with_non_object_secrets_file(self, tmp_path):
        """Handler handles non-object JSON in secrets file."""
        secrets_file = tmp_path / "secrets.json"
        secrets_file.write_text(json.dumps(["a", "b", "c"]))

        handler = CredentialHandler(secrets_file=str(secrets_file))
        assert handler._secrets == {}

    def test_init_skips_non_string_values(self, tmp_path):
        """Handler only loads string values from secrets file."""
        secrets = {"API_KEY": "secret123", "NUM_VALUE": 42, "BOOL": True}
        secrets_file = tmp_path / "secrets.json"
        secrets_file.write_text(json.dumps(secrets))

        handler = CredentialHandler(secrets_file=str(secrets_file))
        assert handler._secrets == {"API_KEY": "secret123"}


class TestGetCredential:
    """Tests for get_credential method."""

    def test_get_credential_from_env_var(self, monkeypatch):
        """Retrieves credential from environment variable."""
        monkeypatch.setenv("MY_API_KEY", "env_value_123")
        handler = CredentialHandler()

        result = handler.get_credential("MY_API_KEY")
        assert result == "env_value_123"

    def test_get_credential_from_secrets_file(self, tmp_path):
        """Retrieves credential from secrets file when not in env."""
        secrets = {"DB_PASSWORD": "dbpass789"}
        secrets_file = tmp_path / "secrets.json"
        secrets_file.write_text(json.dumps(secrets))

        handler = CredentialHandler(secrets_file=str(secrets_file))
        result = handler.get_credential("DB_PASSWORD")
        assert result == "dbpass789"

    def test_env_var_takes_priority_over_secrets_file(
        self, tmp_path, monkeypatch
    ):
        """Environment variable takes priority over secrets file."""
        secrets = {"API_KEY": "file_value"}
        secrets_file = tmp_path / "secrets.json"
        secrets_file.write_text(json.dumps(secrets))
        monkeypatch.setenv("API_KEY", "env_value")

        handler = CredentialHandler(secrets_file=str(secrets_file))
        result = handler.get_credential("API_KEY")
        assert result == "env_value"

    def test_get_credential_raises_key_error_when_not_found(self):
        """Raises KeyError when credential is not found anywhere."""
        handler = CredentialHandler()

        with pytest.raises(KeyError, match="not found"):
            handler.get_credential("NONEXISTENT_KEY")

    def test_get_credential_error_includes_key_name(self):
        """KeyError message includes the missing key name."""
        handler = CredentialHandler()

        with pytest.raises(KeyError, match="MY_MISSING_KEY"):
            handler.get_credential("MY_MISSING_KEY")


class TestInjectIntoEnv:
    """Tests for inject_into_env method."""

    def test_inject_adds_secrets_to_container_env(self, tmp_path):
        """Credentials from secrets file are added to container env."""
        secrets = {"API_KEY": "key123", "TOKEN": "tok456"}
        secrets_file = tmp_path / "secrets.json"
        secrets_file.write_text(json.dumps(secrets))

        handler = CredentialHandler(secrets_file=str(secrets_file))
        container_env = {"PATH": "/usr/bin", "HOME": "/root"}

        result = handler.inject_into_env(container_env)

        assert result["PATH"] == "/usr/bin"
        assert result["HOME"] == "/root"
        assert result["API_KEY"] == "key123"
        assert result["TOKEN"] == "tok456"

    def test_inject_does_not_modify_original_dict(self, tmp_path):
        """inject_into_env returns a new dict, not modifying the original."""
        secrets = {"API_KEY": "key123"}
        secrets_file = tmp_path / "secrets.json"
        secrets_file.write_text(json.dumps(secrets))

        handler = CredentialHandler(secrets_file=str(secrets_file))
        container_env = {"PATH": "/usr/bin"}

        result = handler.inject_into_env(container_env)

        assert "API_KEY" not in container_env
        assert "API_KEY" in result

    def test_inject_with_empty_secrets(self):
        """inject_into_env works with no secrets loaded."""
        handler = CredentialHandler()
        container_env = {"PATH": "/usr/bin"}

        result = handler.inject_into_env(container_env)

        assert result == {"PATH": "/usr/bin"}

    def test_inject_with_empty_container_env(self, tmp_path):
        """inject_into_env works with empty container env."""
        secrets = {"API_KEY": "key123"}
        secrets_file = tmp_path / "secrets.json"
        secrets_file.write_text(json.dumps(secrets))

        handler = CredentialHandler(secrets_file=str(secrets_file))
        result = handler.inject_into_env({})

        assert result == {"API_KEY": "key123"}


class TestCredentialRedaction:
    """Tests for credential non-leakage in logs."""

    def test_credentials_redacted_from_log_output(self, tmp_path, caplog):
        """Credential values are redacted from log messages."""
        secrets = {"API_KEY": "supersecretvalue"}
        secrets_file = tmp_path / "secrets.json"
        secrets_file.write_text(json.dumps(secrets))

        handler = CredentialHandler(secrets_file=str(secrets_file))

        # Get the module logger with the redacting filter
        test_logger = logging.getLogger("labs.core.credential_handler")

        with caplog.at_level(logging.INFO, logger="labs.core.credential_handler"):
            test_logger.info("The value is: supersecretvalue")

        # The credential value should be redacted
        for record in caplog.records:
            assert "supersecretvalue" not in record.getMessage()

    def test_env_credential_redacted_after_retrieval(self, monkeypatch, caplog):
        """Credentials from env vars are redacted after first retrieval."""
        monkeypatch.setenv("SECRET_TOKEN", "myenvtoken123")
        handler = CredentialHandler()

        # Retrieve the credential (this registers it for redaction)
        handler.get_credential("SECRET_TOKEN")

        test_logger = logging.getLogger("labs.core.credential_handler")

        with caplog.at_level(logging.INFO, logger="labs.core.credential_handler"):
            test_logger.info("Token is: myenvtoken123")

        for record in caplog.records:
            assert "myenvtoken123" not in record.getMessage()

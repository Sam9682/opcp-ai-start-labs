"""Credential handler for managing API keys and tokens.

Reads credentials from environment variables or a secrets file.
Ensures credentials never appear in log output.
"""

import json
import logging
import os
from pathlib import Path
from typing import Optional


class _RedactingFilter(logging.Filter):
    """Logging filter that redacts credential values from log output."""

    def __init__(self, credential_values: set[str]):
        super().__init__()
        self._credential_values = credential_values

    def filter(self, record: logging.LogRecord) -> bool:
        """Redact any credential values found in log messages."""
        if self._credential_values:
            msg = record.getMessage()
            for value in self._credential_values:
                if value and value in msg:
                    record.msg = str(record.msg).replace(value, "***REDACTED***")
                    if record.args:
                        # Re-format args to redact values
                        if isinstance(record.args, dict):
                            record.args = {
                                k: (
                                    str(v).replace(value, "***REDACTED***")
                                    if isinstance(v, str) else v
                                )
                                for k, v in record.args.items()
                            }
                        elif isinstance(record.args, tuple):
                            record.args = tuple(
                                str(a).replace(value, "***REDACTED***")
                                if isinstance(a, str) else a
                                for a in record.args
                            )
        return True


logger = logging.getLogger(__name__)


class CredentialHandler:
    """Manages API keys and tokens from environment or secrets file.

    Credentials are loaded from:
    1. Environment variables (highest priority)
    2. A JSON secrets file (fallback)

    Credentials are never embedded in source code or logs.
    """

    def __init__(self, secrets_file: Optional[str] = None):
        """Initialize the credential handler.

        Args:
            secrets_file: Optional path to a JSON secrets file.
                         Keys in the file map to credential names,
                         values are the credential strings.
        """
        self._secrets: dict[str, str] = {}
        self._redacting_filter = _RedactingFilter(set())

        # Install redacting filter on the module logger and root logger
        logger.addFilter(self._redacting_filter)
        logging.getLogger().addFilter(self._redacting_filter)

        if secrets_file is not None:
            self._load_secrets_file(secrets_file)

    def _load_secrets_file(self, secrets_file: str) -> None:
        """Load credentials from a JSON secrets file."""
        path = Path(secrets_file)
        if not path.exists():
            logger.warning(
                "Secrets file not found: %s", secrets_file
            )
            return

        try:
            content = path.read_text(encoding="utf-8")
            data = json.loads(content)
            if not isinstance(data, dict):
                logger.warning(
                    "Secrets file must contain a JSON object at top level"
                )
                return

            for key, value in data.items():
                if isinstance(value, str):
                    self._secrets[key] = value
                    self._redacting_filter._credential_values.add(value)

            logger.info(
                "Loaded %d credentials from secrets file", len(self._secrets)
            )
        except (json.JSONDecodeError, OSError) as e:
            logger.warning("Failed to load secrets file: %s", e)

    def get_credential(self, key: str) -> str:
        """Retrieve a credential by key.

        Looks up the credential in this order:
        1. Environment variable with the given key name
        2. Secrets file entry with the given key name

        Args:
            key: The credential key name to look up.

        Returns:
            The credential value as a string.

        Raises:
            KeyError: If the credential is not found in any source.
        """
        # Check environment variable first (highest priority)
        env_value = os.environ.get(key)
        if env_value is not None:
            # Register the value for redaction
            self._redacting_filter._credential_values.add(env_value)
            return env_value

        # Check secrets file
        if key in self._secrets:
            return self._secrets[key]

        raise KeyError(
            f"Credential '{key}' not found in environment variables "
            f"or secrets file"
        )

    def inject_into_env(self, container_env: dict) -> dict:
        """Add required credentials to container environment dict.

        Merges all known credentials (from both env vars and secrets file)
        into the provided container environment dictionary.

        Args:
            container_env: Existing environment dict for the container.

        Returns:
            Updated environment dict with credentials added.
        """
        result = dict(container_env)

        # Inject credentials from secrets file
        for key, value in self._secrets.items():
            result[key] = value

        return result

"""Application metadata validation for the Adding Applications module.

Validates application metadata fields according to platform requirements:
- name: required, string, 1-64 characters
- description: required, non-empty string
- git_url: required, valid URL (http:// or https://)
- docker_image: optional, string
"""

import re
from dataclasses import dataclass
from typing import Optional


# URL pattern matching well-formed HTTP/HTTPS URLs
_URL_PATTERN = re.compile(
    r"^https?://"                # scheme
    r"[^\s/$.?#][^\s]*$",       # host and path (at least one char after scheme)
    re.IGNORECASE,
)


@dataclass
class ValidationError:
    """Represents a single validation error for a metadata field."""

    field: str
    constraint: str
    message: str


@dataclass
class MetadataValidationResult:
    """Result of metadata validation."""

    valid: bool
    errors: list[ValidationError]


def validate_metadata(metadata: dict) -> MetadataValidationResult:
    """Validate application metadata against platform constraints.

    Args:
        metadata: Dictionary containing application metadata fields.
            Expected keys: name, description, git_url, docker_image (optional)

    Returns:
        MetadataValidationResult with valid=True if all constraints pass,
        or valid=False with a list of specific validation errors.
    """
    errors: list[ValidationError] = []

    # Validate name: required, string, 1-64 characters
    name = metadata.get("name")
    if name is None:
        errors.append(ValidationError(
            field="name",
            constraint="required",
            message="Field 'name' is required.",
        ))
    elif not isinstance(name, str):
        errors.append(ValidationError(
            field="name",
            constraint="type",
            message="Field 'name' must be a string.",
        ))
    elif len(name) < 1 or len(name) > 64:
        errors.append(ValidationError(
            field="name",
            constraint="length",
            message="Field 'name' must be between 1 and 64 characters.",
        ))

    # Validate description: required, non-empty string
    description = metadata.get("description")
    if description is None:
        errors.append(ValidationError(
            field="description",
            constraint="required",
            message="Field 'description' is required.",
        ))
    elif not isinstance(description, str):
        errors.append(ValidationError(
            field="description",
            constraint="type",
            message="Field 'description' must be a string.",
        ))
    elif len(description) == 0:
        errors.append(ValidationError(
            field="description",
            constraint="non_empty",
            message="Field 'description' must be non-empty.",
        ))

    # Validate git_url: required, valid URL
    git_url = metadata.get("git_url")
    if git_url is None:
        errors.append(ValidationError(
            field="git_url",
            constraint="required",
            message="Field 'git_url' is required.",
        ))
    elif not isinstance(git_url, str):
        errors.append(ValidationError(
            field="git_url",
            constraint="type",
            message="Field 'git_url' must be a string.",
        ))
    elif not _URL_PATTERN.match(git_url):
        errors.append(ValidationError(
            field="git_url",
            constraint="format",
            message="Field 'git_url' must be a valid HTTP or HTTPS URL.",
        ))

    # Validate docker_image: optional, string if provided
    docker_image = metadata.get("docker_image")
    if docker_image is not None and not isinstance(docker_image, str):
        errors.append(ValidationError(
            field="docker_image",
            constraint="type",
            message="Field 'docker_image' must be a string if provided.",
        ))

    return MetadataValidationResult(
        valid=len(errors) == 0,
        errors=errors,
    )

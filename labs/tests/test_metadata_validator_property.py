"""Property-based tests for the Adding Applications metadata validator.

Feature: ai-store-labs

Covers:
    Property 13: Application Metadata Validation
        Validates: Requirements 6.3

For any application metadata submission, the validator accepts it if and only
if: name is a non-empty string of 1-64 characters, description is a non-empty
string, and git_url is a well-formed URL. The validator rejects any submission
violating these constraints and reports the specific field and constraint
violated.

These tests run without Docker, network access, or a live platform. The
validator is a pure function over an in-memory dict; the autouse network-block
fixture in conftest.py is harmless here because no network is touched.
"""

import importlib

from hypothesis import given, settings
from hypothesis import strategies as st

# The module directory name contains hyphens, which are invalid in a dotted
# `from ... import` path, so load it via importlib (same pattern as the
# opcp-explorer-connect tests).
_metadata_validator = importlib.import_module(
    "labs.modules.adding-applications.metadata_validator"
)
validate_metadata = _metadata_validator.validate_metadata


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

# Valid name: non-empty string, 1..64 characters.
valid_name = st.text(min_size=1, max_size=64)

# Valid description: non-empty string.
valid_description = st.text(min_size=1, max_size=200)


@st.composite
def valid_git_url(draw):
    """A well-formed HTTP/HTTPS URL accepted by the validator.

    The validator's pattern is: ^https?://[^\\s/$.?#][^\\s]*$ (case-insensitive),
    i.e. a scheme followed by at least one non-whitespace host/path char whose
    first character is not one of /$.?#.
    """
    scheme = draw(st.sampled_from(["http", "https"]))
    host = draw(
        st.text(
            alphabet="abcdefghijklmnopqrstuvwxyz0123456789",
            min_size=1,
            max_size=12,
        )
    )
    tld = draw(st.sampled_from(["com", "io", "net", "org", "example"]))
    path = draw(
        st.text(
            alphabet="abcdefghijklmnopqrstuvwxyz0123456789/-_",
            min_size=0,
            max_size=20,
        )
    )
    url = f"{scheme}://{host}.{tld}"
    if path:
        url += "/" + path
    return url


# Optional docker_image: either absent (None) or a string.
optional_docker_image = st.one_of(st.none(), st.text(max_size=64))


def _constraint_for(result, field):
    """Return the constraint reported for a given field, or None."""
    for err in result.errors:
        if err.field == field:
            return err.constraint
    return None


# ---------------------------------------------------------------------------
# Positive direction: fully valid submissions are accepted.
# ---------------------------------------------------------------------------


@settings(max_examples=200)
@given(valid_name, valid_description, valid_git_url(), optional_docker_image)
def test_property_13_accepts_valid_metadata(name, description, git_url, docker_image):
    """Feature: ai-store-labs, Property 13: Application Metadata Validation"""
    metadata = {"name": name, "description": description, "git_url": git_url}
    if docker_image is not None:
        metadata["docker_image"] = docker_image

    result = validate_metadata(metadata)

    assert result.valid is True, (
        f"Expected valid metadata to be accepted, got errors: {result.errors}"
    )
    assert result.errors == []


# ---------------------------------------------------------------------------
# Negative direction: an invalid name is rejected and the name field reported.
# ---------------------------------------------------------------------------


@settings(max_examples=150)
@given(
    name=st.one_of(st.none(), st.text(min_size=65, max_size=120)),
    description=valid_description,
    git_url=valid_git_url(),
)
def test_property_13_rejects_invalid_name(name, description, git_url):
    """Feature: ai-store-labs, Property 13: Application Metadata Validation"""
    metadata = {"name": name, "description": description, "git_url": git_url}

    result = validate_metadata(metadata)

    assert result.valid is False
    constraint = _constraint_for(result, "name")
    assert constraint is not None, "Expected an error reported for the 'name' field"
    expected = "required" if name is None else "length"
    assert constraint == expected


# ---------------------------------------------------------------------------
# Negative direction: an invalid description is rejected and reported.
# ---------------------------------------------------------------------------


@settings(max_examples=150)
@given(
    name=valid_name,
    description=st.one_of(st.none(), st.just("")),
    git_url=valid_git_url(),
)
def test_property_13_rejects_invalid_description(name, description, git_url):
    """Feature: ai-store-labs, Property 13: Application Metadata Validation"""
    metadata = {"name": name, "git_url": git_url}
    if description is not None:
        metadata["description"] = description

    result = validate_metadata(metadata)

    assert result.valid is False
    constraint = _constraint_for(result, "description")
    assert constraint is not None, (
        "Expected an error reported for the 'description' field"
    )
    expected = "required" if description is None else "non_empty"
    assert constraint == expected


# ---------------------------------------------------------------------------
# Negative direction: a malformed git_url is rejected and reported.
# ---------------------------------------------------------------------------


@st.composite
def malformed_git_url(draw):
    """A string that is not a well-formed HTTP/HTTPS URL (and not empty)."""
    return draw(
        st.one_of(
            # No scheme at all.
            st.text(
                alphabet="abcdefghijklmnopqrstuvwxyz0123456789.",
                min_size=1,
                max_size=20,
            ),
            # Wrong scheme.
            st.builds(lambda s: "ftp://" + s, st.text(min_size=1, max_size=10)),
            # Scheme only, nothing after.
            st.sampled_from(["http://", "https://"]),
        )
    )


@settings(max_examples=150)
@given(
    name=valid_name,
    description=valid_description,
    git_url=st.one_of(st.none(), malformed_git_url()),
)
def test_property_13_rejects_invalid_git_url(name, description, git_url):
    """Feature: ai-store-labs, Property 13: Application Metadata Validation"""
    metadata = {"name": name, "description": description}
    if git_url is not None:
        metadata["git_url"] = git_url

    result = validate_metadata(metadata)

    assert result.valid is False
    constraint = _constraint_for(result, "git_url")
    assert constraint is not None, (
        "Expected an error reported for the 'git_url' field"
    )
    expected = "required" if git_url is None else "format"
    assert constraint == expected

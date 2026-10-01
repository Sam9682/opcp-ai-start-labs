"""Property-based tests for the module structure validator.

Feature: ai-store-labs, Property 12: Module Structure Validation
Validates: Requirements 4.5, 4.6

These tests construct Lab_Module directories under Hypothesis-provided
``tmp_path`` roots and assert that ``validate_module`` reports exactly the
required components / README sections that are absent. The validator performs
only filesystem reads of locally constructed directories, so the tests run
without Docker or network access.
"""

import shutil

from hypothesis import given, settings
from hypothesis import strategies as st

from labs.core.module_validator import validate_module


# Required structural components checked by the validator.
REQUIRED_SUBDIRS = ("exercises", "solutions", "setup")
REQUIRED_FILE = "README.md"

# Required README sections and the substrings the validator emits for each.
README_SECTIONS = ("title", "objective", "prerequisite list", "exercise table")

# README fragments that satisfy each section individually. Each fragment, when
# present, makes the corresponding ``_has_*`` check succeed.
SECTION_FRAGMENTS = {
    "title": "# Module Title\n",
    "objective": "## Objective\n\nLearn the thing.\n",
    "prerequisite list": "## Prerequisites\n\n- Item one\n- Item two\n",
    "exercise table": (
        "## Exercises\n\n"
        "| # | Name | Objective |\n"
        "|---|------|-----------|\n"
        "| 1 | Ex1 | Do stuff |\n"
    ),
}


def _build_readme(present_sections: frozenset[str]) -> str:
    """Assemble README content containing exactly ``present_sections``.

    Sections are concatenated in a fixed order with blank-line separators so
    that each enabled section remains independently detectable.
    """
    parts = [
        SECTION_FRAGMENTS[name]
        for name in README_SECTIONS
        if name in present_sections
    ]
    # Join with an extra blank line so a prerequisite list cannot bleed into a
    # following section and vice versa.
    return "\n".join(parts) + ("\n" if parts else "")


def _structural_warnings(warnings: list[str]) -> list[str]:
    """Return warnings that concern missing directories or the README file."""
    out = []
    for w in warnings:
        if "missing required subdirectory" in w or "missing required file" in w:
            out.append(w)
    return out


def _section_warnings(warnings: list[str]) -> list[str]:
    """Return warnings that concern missing README sections."""
    return [w for w in warnings if "missing required section" in w]


# ---------------------------------------------------------------------------
# Property 12 (part A): structural component validation.
# ---------------------------------------------------------------------------
@settings(max_examples=200)
@given(
    present_subdirs=st.sets(st.sampled_from(REQUIRED_SUBDIRS)),
    readme_present=st.booleans(),
)
def test_structure_warnings_name_exactly_missing_components(
    present_subdirs, readme_present, tmp_path_factory
):
    """Feature: ai-store-labs, Property 12: Module Structure Validation.

    For any Lab_Module directory, the validator produces warnings naming
    exactly the required structural components (exercises/, solutions/,
    setup/, README.md) that are missing. When all are present, no structural
    warnings are produced.
    """
    root = tmp_path_factory.mktemp("mod")
    module_dir = root / "a-module"
    module_dir.mkdir()

    for subdir in present_subdirs:
        (module_dir / subdir).mkdir()

    if readme_present:
        # Use a fully valid README so README-content warnings don't appear and
        # we can isolate the structural check.
        (module_dir / "README.md").write_text(
            _build_readme(frozenset(README_SECTIONS)), encoding="utf-8"
        )

    warnings = validate_module(module_dir)
    structural = _structural_warnings(warnings)

    missing_subdirs = set(REQUIRED_SUBDIRS) - set(present_subdirs)
    expected_structural_count = len(missing_subdirs) + (0 if readme_present else 1)

    # Exactly one structural warning per missing component.
    assert len(structural) == expected_structural_count

    for subdir in REQUIRED_SUBDIRS:
        mentioned = any(f"{subdir}/" in w for w in structural)
        assert mentioned == (subdir in missing_subdirs)

    readme_warned = any(REQUIRED_FILE in w for w in structural)
    assert readme_warned == (not readme_present)

    if present_subdirs == set(REQUIRED_SUBDIRS) and readme_present:
        assert structural == []
        # A fully valid module produces no warnings at all.
        assert warnings == []

    # Clean up the generated tree to keep the tmp area small across examples.
    shutil.rmtree(root, ignore_errors=True)


# ---------------------------------------------------------------------------
# Property 12 (part B): README section validation.
# ---------------------------------------------------------------------------
@settings(max_examples=200)
@given(
    present_sections=st.sets(st.sampled_from(README_SECTIONS)),
)
def test_readme_warnings_name_exactly_missing_sections(
    present_sections, tmp_path_factory
):
    """Feature: ai-store-labs, Property 12: Module Structure Validation.

    For README.md content, the validator identifies exactly which required
    sections (title, objective, prerequisite list, exercise table) are absent.
    When all sections are present, no section warnings are produced.
    """
    root = tmp_path_factory.mktemp("mod")
    module_dir = root / "a-module"
    module_dir.mkdir()
    # Provide all structural subdirs so only README-section warnings vary.
    for subdir in REQUIRED_SUBDIRS:
        (module_dir / subdir).mkdir()

    present = frozenset(present_sections)
    (module_dir / "README.md").write_text(_build_readme(present), encoding="utf-8")

    warnings = validate_module(module_dir)
    sections = _section_warnings(warnings)

    missing_sections = set(README_SECTIONS) - set(present_sections)

    # Exactly one section warning per missing section.
    assert len(sections) == len(missing_sections)

    for name in README_SECTIONS:
        mentioned = any(f"missing required section: {name}" in w for w in sections)
        assert mentioned == (name in missing_sections)

    if present == frozenset(README_SECTIONS):
        assert sections == []
        # Fully valid module (structure + README) => no warnings at all.
        assert warnings == []

    shutil.rmtree(root, ignore_errors=True)

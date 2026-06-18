"""Unit tests for the module structure validator."""

import pytest
from pathlib import Path

from labs.core.module_validator import (
    validate_module,
    validate_all_modules,
    _has_title,
    _has_objective,
    _has_prerequisite_list,
    _has_exercise_table,
)


VALID_README = """\
# Install Bare-Metal Ubuntu

## Objective

Learn how to install the AI-Powered-Store on bare-metal Ubuntu.

## Prerequisites

- Ubuntu 22.04 or 24.04 LTS
- Docker Engine installed
- Basic Linux command-line knowledge

## Exercises

| # | Exercise Name | Objective |
|---|---------------|-----------|
| 1 | System Prerequisites | Verify system requirements |
| 2 | Docker Installation | Install Docker Engine |
"""


@pytest.fixture
def valid_module(tmp_path):
    """Create a valid module directory with all required components."""
    module_dir = tmp_path / "test-module"
    module_dir.mkdir()
    (module_dir / "exercises").mkdir()
    (module_dir / "solutions").mkdir()
    (module_dir / "setup").mkdir()
    (module_dir / "README.md").write_text(VALID_README, encoding="utf-8")
    return module_dir


@pytest.fixture
def modules_dir(tmp_path):
    """Create a modules directory with multiple modules."""
    modules = tmp_path / "modules"
    modules.mkdir()
    return modules


class TestValidateModule:
    """Tests for validate_module function."""

    def test_valid_module_no_warnings(self, valid_module):
        """A complete module should produce no warnings."""
        warnings = validate_module(valid_module)
        assert warnings == []

    def test_nonexistent_path(self, tmp_path):
        """Non-existent path should produce a warning."""
        warnings = validate_module(tmp_path / "nonexistent")
        assert len(warnings) == 1
        assert "does not exist" in warnings[0]

    def test_missing_exercises_dir(self, valid_module):
        """Missing exercises/ should produce a warning."""
        (valid_module / "exercises").rmdir()
        warnings = validate_module(valid_module)
        assert any("exercises/" in w for w in warnings)

    def test_missing_solutions_dir(self, valid_module):
        """Missing solutions/ should produce a warning."""
        (valid_module / "solutions").rmdir()
        warnings = validate_module(valid_module)
        assert any("solutions/" in w for w in warnings)

    def test_missing_setup_dir(self, valid_module):
        """Missing setup/ should produce a warning."""
        (valid_module / "setup").rmdir()
        warnings = validate_module(valid_module)
        assert any("setup/" in w for w in warnings)

    def test_missing_readme(self, valid_module):
        """Missing README.md should produce a warning."""
        (valid_module / "README.md").unlink()
        warnings = validate_module(valid_module)
        assert any("README.md" in w for w in warnings)

    def test_missing_multiple_components(self, tmp_path):
        """Missing multiple components should produce multiple warnings."""
        module_dir = tmp_path / "empty-module"
        module_dir.mkdir()
        warnings = validate_module(module_dir)
        # Should have warnings for exercises/, solutions/, setup/, README.md
        assert len(warnings) == 4

    def test_readme_missing_title(self, valid_module):
        """README without title should produce a warning."""
        readme = valid_module / "README.md"
        content = readme.read_text(encoding="utf-8")
        # Remove the title line
        content = content.replace("# Install Bare-Metal Ubuntu\n", "")
        readme.write_text(content, encoding="utf-8")
        warnings = validate_module(valid_module)
        assert any("title" in w for w in warnings)

    def test_readme_missing_objective(self, valid_module):
        """README without objective should produce a warning."""
        readme = valid_module / "README.md"
        content = readme.read_text(encoding="utf-8")
        # Remove objective section
        content = content.replace("## Objective\n\nLearn how to install the AI-Powered-Store on bare-metal Ubuntu.\n", "")
        readme.write_text(content, encoding="utf-8")
        warnings = validate_module(valid_module)
        assert any("objective" in w for w in warnings)

    def test_readme_missing_prerequisites(self, valid_module):
        """README without prerequisite list should produce a warning."""
        readme = valid_module / "README.md"
        content = "# Title\n\n## Objective\n\nSome objective.\n\n## Exercises\n\n| # | Name | Obj |\n|---|------|-----|\n| 1 | Ex1 | Do something |\n"
        readme.write_text(content, encoding="utf-8")
        warnings = validate_module(valid_module)
        assert any("prerequisite list" in w for w in warnings)

    def test_readme_missing_exercise_table(self, valid_module):
        """README without exercise table should produce a warning."""
        readme = valid_module / "README.md"
        content = "# Title\n\n## Objective\n\nSome objective.\n\n## Prerequisites\n\n- Item 1\n- Item 2\n"
        readme.write_text(content, encoding="utf-8")
        warnings = validate_module(valid_module)
        assert any("exercise table" in w for w in warnings)


class TestValidateAllModules:
    """Tests for validate_all_modules function."""

    def test_empty_modules_dir(self, modules_dir):
        """Empty modules directory should return empty dict."""
        results = validate_all_modules(modules_dir)
        assert results == {}

    def test_nonexistent_modules_dir(self, tmp_path):
        """Non-existent modules dir should return empty dict."""
        results = validate_all_modules(tmp_path / "nonexistent")
        assert results == {}

    def test_valid_module_in_dir(self, modules_dir):
        """Valid module in directory should have empty warnings list."""
        module = modules_dir / "good-module"
        module.mkdir()
        (module / "exercises").mkdir()
        (module / "solutions").mkdir()
        (module / "setup").mkdir()
        (module / "README.md").write_text(VALID_README, encoding="utf-8")

        results = validate_all_modules(modules_dir)
        assert "good-module" in results
        assert results["good-module"] == []

    def test_multiple_modules(self, modules_dir):
        """Multiple modules should all be validated."""
        # Create a valid module
        good = modules_dir / "good-module"
        good.mkdir()
        (good / "exercises").mkdir()
        (good / "solutions").mkdir()
        (good / "setup").mkdir()
        (good / "README.md").write_text(VALID_README, encoding="utf-8")

        # Create an incomplete module
        bad = modules_dir / "bad-module"
        bad.mkdir()

        results = validate_all_modules(modules_dir)
        assert "good-module" in results
        assert "bad-module" in results
        assert results["good-module"] == []
        assert len(results["bad-module"]) > 0

    def test_skips_hidden_directories(self, modules_dir):
        """Hidden directories (starting with .) should be skipped."""
        hidden = modules_dir / ".hidden"
        hidden.mkdir()

        results = validate_all_modules(modules_dir)
        assert ".hidden" not in results

    def test_skips_dunder_directories(self, modules_dir):
        """__pycache__ and similar dirs should be skipped."""
        pycache = modules_dir / "__pycache__"
        pycache.mkdir()

        results = validate_all_modules(modules_dir)
        assert "__pycache__" not in results

    def test_skips_files(self, modules_dir):
        """Regular files in modules dir should be skipped."""
        (modules_dir / "__init__.py").write_text("", encoding="utf-8")

        results = validate_all_modules(modules_dir)
        assert "__init__.py" not in results


class TestReadmeHelpers:
    """Tests for README content validation helpers."""

    def test_has_title_with_h1(self):
        assert _has_title("# My Title\n")

    def test_has_title_without_heading(self):
        assert not _has_title("Some text without heading\n")

    def test_has_title_with_only_h2(self):
        assert not _has_title("## Subtitle\n")

    def test_has_objective_heading(self):
        assert _has_objective("## Objective\n\nSome text\n")

    def test_has_objective_labeled(self):
        assert _has_objective("**Objective**: Learn stuff\n")

    def test_has_objective_missing(self):
        assert not _has_objective("# Title\n\nSome content\n")

    def test_has_prerequisite_list_with_heading_and_list(self):
        content = "## Prerequisites\n\n- Item 1\n- Item 2\n"
        assert _has_prerequisite_list(content)

    def test_has_prerequisite_list_without_list_items(self):
        content = "## Prerequisites\n\nJust text, no list.\n"
        assert not _has_prerequisite_list(content)

    def test_has_prerequisite_list_missing(self):
        content = "# Title\n\nSome content\n"
        assert not _has_prerequisite_list(content)

    def test_has_exercise_table_valid(self):
        content = "| # | Name | Objective |\n|---|------|----------|\n| 1 | Ex1 | Do stuff |\n"
        assert _has_exercise_table(content)

    def test_has_exercise_table_missing(self):
        content = "# Title\n\nSome content without table\n"
        assert not _has_exercise_table(content)

    def test_has_exercise_table_incomplete(self):
        # Only header row, no separator
        content = "| # | Name | Objective |\n"
        assert not _has_exercise_table(content)

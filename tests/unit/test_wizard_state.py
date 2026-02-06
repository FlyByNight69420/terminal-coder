"""Tests for WizardState and WizardResult."""

from __future__ import annotations

from pathlib import Path

import pytest

from tc.tui.onboarding.state import ValidationError, WizardResult, WizardState


class TestWizardState:
    def test_default_state(self) -> None:
        state = WizardState()
        assert state.project_dir == ""
        assert state.project_name == ""
        assert state.prd_path == ""
        assert state.bootstrap_path == ""
        assert state.current_step == 0
        assert state.TOTAL_STEPS == 7
        assert state.prd_generated is False

    def test_prd_generated_flag(self) -> None:
        state = WizardState()
        state.prd_generated = True
        assert state.prd_generated is True

    def test_validate_empty_state(self) -> None:
        state = WizardState()
        errors = state.validate()
        assert len(errors) >= 2
        assert any("directory" in e.lower() for e in errors)
        assert any("prd" in e.lower() for e in errors)

    def test_validate_relative_path(self) -> None:
        state = WizardState(
            project_dir="relative/path",
            project_name="test",
            prd_path="/tmp/prd.md",
        )
        errors = state.validate()
        assert any("absolute" in e.lower() for e in errors)

    def test_validate_nonexistent_dir(self, tmp_path: Path) -> None:
        nonexistent = tmp_path / "does_not_exist"
        state = WizardState(
            project_dir=str(nonexistent),
            project_name="test",
            prd_path="/tmp/prd.md",
        )
        errors = state.validate()
        assert any("does not exist" in e for e in errors)

    def test_validate_dir_is_file(self, tmp_path: Path) -> None:
        f = tmp_path / "afile.txt"
        f.write_text("x")
        state = WizardState(
            project_dir=str(f),
            project_name="test",
            prd_path="/tmp/prd.md",
        )
        errors = state.validate()
        assert any("not a directory" in e for e in errors)

    def test_validate_missing_name(self, tmp_path: Path) -> None:
        prd = tmp_path / "prd.md"
        prd.write_text("# PRD")
        state = WizardState(
            project_dir=str(tmp_path),
            project_name="",
            prd_path=str(prd),
        )
        errors = state.validate()
        assert any("name" in e.lower() for e in errors)

    def test_validate_nonexistent_prd(self, tmp_path: Path) -> None:
        state = WizardState(
            project_dir=str(tmp_path),
            project_name="test",
            prd_path=str(tmp_path / "nope.md"),
        )
        errors = state.validate()
        assert any("prd" in e.lower() for e in errors)

    def test_validate_prd_is_dir(self, tmp_path: Path) -> None:
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        state = WizardState(
            project_dir=str(tmp_path),
            project_name="test",
            prd_path=str(subdir),
        )
        errors = state.validate()
        assert any("not a file" in e for e in errors)

    def test_validate_nonexistent_bootstrap(self, tmp_path: Path) -> None:
        prd = tmp_path / "prd.md"
        prd.write_text("# PRD")
        state = WizardState(
            project_dir=str(tmp_path),
            project_name="test",
            prd_path=str(prd),
            bootstrap_path=str(tmp_path / "nope.md"),
        )
        errors = state.validate()
        assert any("bootstrap" in e.lower() for e in errors)

    def test_validate_valid_state(self, tmp_path: Path) -> None:
        prd = tmp_path / "prd.md"
        prd.write_text("# PRD")
        state = WizardState(
            project_dir=str(tmp_path),
            project_name="my-project",
            prd_path=str(prd),
        )
        errors = state.validate()
        assert errors == []

    def test_validate_valid_with_bootstrap(self, tmp_path: Path) -> None:
        prd = tmp_path / "prd.md"
        prd.write_text("# PRD")
        bootstrap = tmp_path / "bootstrap.md"
        bootstrap.write_text("# Bootstrap")
        state = WizardState(
            project_dir=str(tmp_path),
            project_name="my-project",
            prd_path=str(prd),
            bootstrap_path=str(bootstrap),
        )
        errors = state.validate()
        assert errors == []

    def test_validate_empty_bootstrap_is_ok(self, tmp_path: Path) -> None:
        prd = tmp_path / "prd.md"
        prd.write_text("# PRD")
        state = WizardState(
            project_dir=str(tmp_path),
            project_name="test",
            prd_path=str(prd),
            bootstrap_path="",
        )
        errors = state.validate()
        assert errors == []


class TestWizardStateToResult:
    def test_to_result_valid(self, tmp_path: Path) -> None:
        prd = tmp_path / "prd.md"
        prd.write_text("# PRD")
        state = WizardState(
            project_dir=str(tmp_path),
            project_name="my-project",
            prd_path=str(prd),
        )
        result = state.to_result()
        assert isinstance(result, WizardResult)
        assert result.project_dir == tmp_path.resolve()
        assert result.project_name == "my-project"
        assert result.prd_path == prd.resolve()
        assert result.bootstrap_path is None

    def test_to_result_with_bootstrap(self, tmp_path: Path) -> None:
        prd = tmp_path / "prd.md"
        prd.write_text("# PRD")
        bootstrap = tmp_path / "bootstrap.md"
        bootstrap.write_text("# Bootstrap")
        state = WizardState(
            project_dir=str(tmp_path),
            project_name="test",
            prd_path=str(prd),
            bootstrap_path=str(bootstrap),
        )
        result = state.to_result()
        assert result.bootstrap_path == bootstrap.resolve()

    def test_to_result_strips_whitespace(self, tmp_path: Path) -> None:
        prd = tmp_path / "prd.md"
        prd.write_text("# PRD")
        state = WizardState(
            project_dir=str(tmp_path),
            project_name="  my-project  ",
            prd_path=str(prd),
        )
        result = state.to_result()
        assert result.project_name == "my-project"

    def test_to_result_invalid_raises(self) -> None:
        state = WizardState()
        with pytest.raises(ValidationError):
            state.to_result()


class TestWizardResult:
    def test_frozen(self, tmp_path: Path) -> None:
        prd = tmp_path / "prd.md"
        prd.write_text("# PRD")
        result = WizardResult(
            project_dir=tmp_path,
            project_name="test",
            prd_path=prd,
            bootstrap_path=None,
        )
        with pytest.raises(AttributeError):
            result.project_name = "changed"  # type: ignore[misc]

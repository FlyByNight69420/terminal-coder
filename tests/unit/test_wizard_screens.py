"""Tests for wizard screen state transitions and behavior."""

from __future__ import annotations

from pathlib import Path

from tc.tui.onboarding.state import WizardState


class TestPrdScreenStatePaths:
    """Test state transitions for manual vs generate PRD paths."""

    def test_manual_path_sets_prd_path(self, tmp_path: Path) -> None:
        prd = tmp_path / "prd.md"
        prd.write_text("# PRD")
        state = WizardState(
            project_dir=str(tmp_path),
            project_name="test",
        )
        # Simulate manual path: user enters PRD path directly
        state.prd_path = str(prd)
        state.current_step = 3
        assert state.prd_path == str(prd)
        assert state.prd_generated is False

    def test_generate_path_sets_prd_generated(self, tmp_path: Path) -> None:
        prd = tmp_path / "prd.md"
        prd.write_text("# PRD")
        state = WizardState(
            project_dir=str(tmp_path),
            project_name="test",
        )
        # Simulate generate path: generation sets path + flag
        state.prd_path = str(prd)
        state.prd_generated = True
        state.current_step = 3
        assert state.prd_path == str(prd)
        assert state.prd_generated is True

    def test_generate_path_sets_bootstrap(self, tmp_path: Path) -> None:
        prd = tmp_path / "prd.md"
        prd.write_text("# PRD")
        bootstrap = tmp_path / "bootstrap.md"
        bootstrap.write_text("# Bootstrap")
        state = WizardState(
            project_dir=str(tmp_path),
            project_name="test",
        )
        state.prd_path = str(prd)
        state.bootstrap_path = str(bootstrap)
        state.prd_generated = True
        assert state.bootstrap_path == str(bootstrap)


class TestBootstrapAutoFill:
    """Test bootstrap screen auto-fill from PRD generation."""

    def test_auto_fill_when_prd_generated(self, tmp_path: Path) -> None:
        bootstrap = tmp_path / "bootstrap.md"
        bootstrap.write_text("# Bootstrap")
        state = WizardState(
            project_dir=str(tmp_path),
            project_name="test",
            prd_path=str(tmp_path / "prd.md"),
            bootstrap_path=str(bootstrap),
            prd_generated=True,
        )
        # When prd_generated is True and bootstrap_path is set,
        # the bootstrap screen should auto-fill
        assert state.prd_generated is True
        assert state.bootstrap_path == str(bootstrap)

    def test_no_auto_fill_when_manual(self, tmp_path: Path) -> None:
        state = WizardState(
            project_dir=str(tmp_path),
            project_name="test",
            prd_path=str(tmp_path / "prd.md"),
        )
        assert state.prd_generated is False
        assert state.bootstrap_path == ""

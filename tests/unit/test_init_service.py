"""Tests for the project initialization service."""

from __future__ import annotations

from pathlib import Path

import pytest

from tc.core.init_service import (
    InitResult,
    ProjectAlreadyExistsError,
    initialize_project,
)


@pytest.fixture()
def project_dir(tmp_path: Path) -> Path:
    """Create a temp directory to use as project root."""
    d = tmp_path / "myproject"
    d.mkdir()
    return d


@pytest.fixture()
def prd_file(tmp_path: Path) -> Path:
    """Create a temp PRD file."""
    f = tmp_path / "prd.md"
    f.write_text("# My PRD\n\nRequirements here.\n")
    return f


@pytest.fixture()
def bootstrap_file(tmp_path: Path) -> Path:
    """Create a temp bootstrap file."""
    f = tmp_path / "bootstrap.md"
    f.write_text("# Bootstrap\n\nChecks here.\n")
    return f


class TestInitializeProject:
    def test_creates_tc_directory(self, project_dir: Path, prd_file: Path) -> None:
        initialize_project(
            project_dir=project_dir,
            project_name="test-project",
            prd_path=prd_file,
        )
        assert (project_dir / ".tc").is_dir()
        assert (project_dir / ".tc" / "briefs").is_dir()
        assert (project_dir / ".tc" / "logs").is_dir()
        assert (project_dir / ".tc" / "plans").is_dir()

    def test_creates_database(self, project_dir: Path, prd_file: Path) -> None:
        result = initialize_project(
            project_dir=project_dir,
            project_name="test-project",
            prd_path=prd_file,
        )
        assert result.db_path.exists()
        assert result.db_path.name == "tc.db"

    def test_copies_prd(self, project_dir: Path, prd_file: Path) -> None:
        result = initialize_project(
            project_dir=project_dir,
            project_name="test-project",
            prd_path=prd_file,
        )
        prd_dest = project_dir / "prd.md"
        assert prd_dest.exists()
        assert prd_dest.read_text() == prd_file.read_text()
        assert result.prd_dest == prd_dest

    def test_copies_bootstrap(
        self, project_dir: Path, prd_file: Path, bootstrap_file: Path,
    ) -> None:
        result = initialize_project(
            project_dir=project_dir,
            project_name="test-project",
            prd_path=prd_file,
            bootstrap_path=bootstrap_file,
        )
        bootstrap_dest = project_dir / "bootstrap.md"
        assert bootstrap_dest.exists()
        assert bootstrap_dest.read_text() == bootstrap_file.read_text()
        assert result.bootstrap_dest == bootstrap_dest

    def test_no_bootstrap(self, project_dir: Path, prd_file: Path) -> None:
        result = initialize_project(
            project_dir=project_dir,
            project_name="test-project",
            prd_path=prd_file,
        )
        assert result.bootstrap_dest is None

    def test_creates_mcp_config(self, project_dir: Path, prd_file: Path) -> None:
        initialize_project(
            project_dir=project_dir,
            project_name="test-project",
            prd_path=prd_file,
        )
        assert (project_dir / ".mcp.json").exists()

    def test_returns_init_result(self, project_dir: Path, prd_file: Path) -> None:
        result = initialize_project(
            project_dir=project_dir,
            project_name="test-project",
            prd_path=prd_file,
        )
        assert isinstance(result, InitResult)
        assert result.project_name == "test-project"
        assert result.project_dir == project_dir
        assert result.project_id  # non-empty UUID string

    def test_raises_if_already_exists(
        self, project_dir: Path, prd_file: Path,
    ) -> None:
        # First init succeeds
        initialize_project(
            project_dir=project_dir,
            project_name="test-project",
            prd_path=prd_file,
        )
        # Second init fails
        with pytest.raises(ProjectAlreadyExistsError):
            initialize_project(
                project_dir=project_dir,
                project_name="test-project",
                prd_path=prd_file,
            )

    def test_prd_already_in_project_dir(self, project_dir: Path) -> None:
        """If PRD is already at project_dir/prd.md, don't copy over itself."""
        prd = project_dir / "prd.md"
        prd.write_text("# Already here\n")
        result = initialize_project(
            project_dir=project_dir,
            project_name="test",
            prd_path=prd,
        )
        assert result.prd_dest == prd
        assert prd.read_text() == "# Already here\n"


class TestStepCallback:
    def test_callback_called_for_steps(
        self, project_dir: Path, prd_file: Path,
    ) -> None:
        calls: list[tuple[str, str]] = []

        def on_step(step: str, status: str) -> None:
            calls.append((step, status))

        initialize_project(
            project_dir=project_dir,
            project_name="test-project",
            prd_path=prd_file,
            on_step=on_step,
        )

        step_names = [c[0] for c in calls]
        assert "directories" in step_names
        assert "database" in step_names
        assert "prd" in step_names
        assert "project_record" in step_names
        assert "mcp_config" in step_names

        # Each step has start and done
        for step_name in ["directories", "database", "prd", "project_record", "mcp_config"]:
            starts = [c for c in calls if c == (step_name, "start")]
            dones = [c for c in calls if c == (step_name, "done")]
            assert len(starts) == 1, f"{step_name} should have exactly one start"
            assert len(dones) == 1, f"{step_name} should have exactly one done"

    def test_callback_includes_bootstrap_step(
        self, project_dir: Path, prd_file: Path, bootstrap_file: Path,
    ) -> None:
        calls: list[tuple[str, str]] = []

        def on_step(step: str, status: str) -> None:
            calls.append((step, status))

        initialize_project(
            project_dir=project_dir,
            project_name="test-project",
            prd_path=prd_file,
            bootstrap_path=bootstrap_file,
            on_step=on_step,
        )

        assert ("bootstrap", "start") in calls
        assert ("bootstrap", "done") in calls

    def test_no_bootstrap_callback_without_bootstrap(
        self, project_dir: Path, prd_file: Path,
    ) -> None:
        calls: list[tuple[str, str]] = []

        def on_step(step: str, status: str) -> None:
            calls.append((step, status))

        initialize_project(
            project_dir=project_dir,
            project_name="test-project",
            prd_path=prd_file,
            on_step=on_step,
        )

        assert ("bootstrap", "start") not in calls

    def test_none_callback_is_safe(
        self, project_dir: Path, prd_file: Path,
    ) -> None:
        # Should not raise
        result = initialize_project(
            project_dir=project_dir,
            project_name="test-project",
            prd_path=prd_file,
            on_step=None,
        )
        assert isinstance(result, InitResult)

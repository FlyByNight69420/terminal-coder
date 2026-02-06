"""Integration tests for the tc verify command."""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from tc.cli.app import app

runner = CliRunner()


def _init_project(tmp_path: Path, bootstrap_content: str | None = None) -> Path:
    """Helper to initialize a project for testing."""
    project_dir = tmp_path / "test-project"
    project_dir.mkdir()
    prd = project_dir / "prd.md"
    prd.write_text("# Test PRD\n")

    args = ["init", str(project_dir), "--prd", str(prd)]

    if bootstrap_content is not None:
        bootstrap = project_dir / "bootstrap.md"
        bootstrap.write_text(bootstrap_content)
        args.extend(["--bootstrap", str(bootstrap)])

    result = runner.invoke(app, args)
    assert result.exit_code == 0
    return project_dir


class TestVerifyCommand:
    def test_verify_without_bootstrap_fails(self, tmp_path: Path) -> None:
        project_dir = _init_project(tmp_path)
        result = runner.invoke(app, ["verify", "--project-dir", str(project_dir)])
        assert result.exit_code == 1

    def test_verify_with_simple_checks(self, tmp_path: Path) -> None:
        bootstrap_content = """\
# Bootstrap

## Prerequisites

| Tool | Install | Verify |
|------|---------|--------|
| Python | apt install python3 | `python3 --version` |
"""
        project_dir = _init_project(tmp_path, bootstrap_content)
        result = runner.invoke(app, ["verify", "--project-dir", str(project_dir)])
        # python3 --version should pass, but claude/tmux/git may or may not be available
        assert "Bootstrap Verification" in result.output

    def test_verify_env_checks_with_env_file(self, tmp_path: Path) -> None:
        bootstrap_content = """\
# Bootstrap

## Environment Configuration

### Populate .env file

- `MY_TEST_VAR` - A test variable
"""
        project_dir = _init_project(tmp_path, bootstrap_content)

        # Create .env file with the variable
        env_file = project_dir / ".env"
        env_file.write_text("MY_TEST_VAR=hello\n")

        result = runner.invoke(app, ["verify", "--project-dir", str(project_dir)])
        assert "Bootstrap Verification" in result.output

    def test_verify_no_project_fails(self, tmp_path: Path) -> None:
        result = runner.invoke(app, ["verify", "--project-dir", str(tmp_path)])
        assert result.exit_code == 1

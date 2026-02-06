"""Integration tests for the tc init command."""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from tc.cli.app import app
from tc.config.settings import project_paths
from tc.db.connection import create_connection
from tc.db.repository import Repository

runner = CliRunner()


class TestInitCommand:
    def test_init_creates_tc_directory(self, tmp_path: Path) -> None:
        project_dir = tmp_path / "my-project"
        project_dir.mkdir()
        prd = tmp_path / "prd.md"
        prd.write_text("# Test PRD\n")

        result = runner.invoke(app, [
            "init", str(project_dir), "--prd", str(prd),
        ])
        assert result.exit_code == 0

        paths = project_paths(project_dir)
        assert paths.tc_dir.exists()
        assert paths.briefs_dir.exists()
        assert paths.logs_dir.exists()
        assert paths.plans_dir.exists()
        assert paths.db_path.exists()

    def test_init_creates_project_record(self, tmp_path: Path) -> None:
        project_dir = tmp_path / "my-project"
        project_dir.mkdir()
        prd = tmp_path / "prd.md"
        prd.write_text("# Test PRD\n")

        result = runner.invoke(app, [
            "init", str(project_dir), "--prd", str(prd), "--name", "TestProj",
        ])
        assert result.exit_code == 0

        paths = project_paths(project_dir)
        conn = create_connection(paths.db_path)
        try:
            repo = Repository(conn)
            row = conn.execute("SELECT id FROM projects LIMIT 1").fetchone()
            assert row is not None
            project = repo.get_project(str(row["id"]))
            assert project.name == "TestProj"
            assert project.prd_path == str(project_dir / "prd.md")
        finally:
            conn.close()

    def test_init_copies_prd_to_project(self, tmp_path: Path) -> None:
        project_dir = tmp_path / "my-project"
        project_dir.mkdir()
        prd = tmp_path / "external_prd.md"
        prd.write_text("# External PRD\n")

        result = runner.invoke(app, [
            "init", str(project_dir), "--prd", str(prd),
        ])
        assert result.exit_code == 0
        assert (project_dir / "prd.md").exists()

    def test_init_with_bootstrap(self, tmp_path: Path) -> None:
        project_dir = tmp_path / "my-project"
        project_dir.mkdir()
        prd = tmp_path / "prd.md"
        prd.write_text("# PRD\n")
        bootstrap = tmp_path / "bootstrap.md"
        bootstrap.write_text("# Bootstrap\n")

        result = runner.invoke(app, [
            "init", str(project_dir),
            "--prd", str(prd),
            "--bootstrap", str(bootstrap),
        ])
        assert result.exit_code == 0
        assert (project_dir / "bootstrap.md").exists()

    def test_init_creates_mcp_json(self, tmp_path: Path) -> None:
        project_dir = tmp_path / "my-project"
        project_dir.mkdir()
        prd = tmp_path / "prd.md"
        prd.write_text("# PRD\n")

        result = runner.invoke(app, [
            "init", str(project_dir), "--prd", str(prd),
        ])
        assert result.exit_code == 0

        mcp_json = project_dir / ".mcp.json"
        assert mcp_json.exists()
        config = json.loads(mcp_json.read_text())
        assert "mcpServers" in config
        assert "tc" in config["mcpServers"]

    def test_init_fails_if_already_initialized(self, tmp_path: Path) -> None:
        project_dir = tmp_path / "my-project"
        project_dir.mkdir()
        prd = tmp_path / "prd.md"
        prd.write_text("# PRD\n")

        # First init
        runner.invoke(app, ["init", str(project_dir), "--prd", str(prd)])

        # Second init should fail
        result = runner.invoke(app, ["init", str(project_dir), "--prd", str(prd)])
        assert result.exit_code == 1

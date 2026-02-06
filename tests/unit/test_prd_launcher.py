"""Tests for PRD launcher helper functions."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from tc.orchestrator.prd_launcher import (
    ClaudeNotFoundError,
    PrdDetectionResult,
    build_claude_command,
    detect_generated_files,
    find_claude_binary,
    load_skill_content,
    prepare_idea_file,
)


class TestFindClaudeBinary:
    def test_found_on_path(self) -> None:
        with patch("shutil.which", return_value="/usr/local/bin/claude"):
            result = find_claude_binary()
            assert result == "/usr/local/bin/claude"

    def test_not_found_raises(self) -> None:
        with patch("shutil.which", return_value=None):
            with pytest.raises(ClaudeNotFoundError, match="claude"):
                find_claude_binary()


class TestPrepareIdeaFile:
    def test_writes_file(self, tmp_path: Path) -> None:
        prepare_idea_file(tmp_path, "Build a CLI tool for X")
        idea_file = tmp_path / "idea.txt"
        assert idea_file.exists()
        assert idea_file.read_text() == "Build a CLI tool for X"

    def test_strips_whitespace(self, tmp_path: Path) -> None:
        prepare_idea_file(tmp_path, "  Build something  \n  ")
        idea_file = tmp_path / "idea.txt"
        assert idea_file.read_text() == "Build something"

    def test_empty_raises(self, tmp_path: Path) -> None:
        with pytest.raises(ValueError, match="empty"):
            prepare_idea_file(tmp_path, "")

    def test_whitespace_only_raises(self, tmp_path: Path) -> None:
        with pytest.raises(ValueError, match="empty"):
            prepare_idea_file(tmp_path, "   \n  ")

    def test_bad_dir_raises(self, tmp_path: Path) -> None:
        bad_dir = tmp_path / "nonexistent"
        with pytest.raises(FileNotFoundError):
            prepare_idea_file(bad_dir, "Some idea")


class TestLoadSkillContent:
    def test_found_returns_content(self, tmp_path: Path) -> None:
        skill_file = tmp_path / "SKILL.md"
        skill_file.write_text("# PRD Generation Skill\nDo the thing.")
        result = load_skill_content(skill_path=skill_file)
        assert result == "# PRD Generation Skill\nDo the thing."

    def test_missing_returns_none(self, tmp_path: Path) -> None:
        missing = tmp_path / "nonexistent" / "SKILL.md"
        result = load_skill_content(skill_path=missing)
        assert result is None

    def test_default_path_uses_home(self, tmp_path: Path) -> None:
        skill_dir = tmp_path / ".claude" / "skills" / "prd-generation"
        skill_dir.mkdir(parents=True)
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text("skill content")
        with patch("tc.orchestrator.prd_launcher.Path.home", return_value=tmp_path):
            result = load_skill_content()
        assert result == "skill content"

    def test_default_path_missing_returns_none(self, tmp_path: Path) -> None:
        with patch("tc.orchestrator.prd_launcher.Path.home", return_value=tmp_path):
            result = load_skill_content()
        assert result is None


class TestBuildClaudeCommand:
    def test_bare_command(self) -> None:
        cmd = build_claude_command("/usr/local/bin/claude")
        assert cmd == ["/usr/local/bin/claude"]

    def test_with_prompt(self) -> None:
        cmd = build_claude_command(
            "/usr/local/bin/claude",
            prompt="Read idea.txt and generate prd.md",
        )
        assert cmd == [
            "/usr/local/bin/claude",
            "Read idea.txt and generate prd.md",
        ]

    def test_with_system_prompt(self) -> None:
        cmd = build_claude_command(
            "/usr/local/bin/claude",
            system_prompt="You are a PRD generator.",
        )
        assert cmd == [
            "/usr/local/bin/claude",
            "--append-system-prompt",
            "You are a PRD generator.",
        ]

    def test_with_prompt_and_system_prompt(self) -> None:
        cmd = build_claude_command(
            "/usr/local/bin/claude",
            prompt="Do the thing",
            system_prompt="Skill instructions here",
        )
        assert cmd == [
            "/usr/local/bin/claude",
            "--append-system-prompt",
            "Skill instructions here",
            "Do the thing",
        ]


class TestDetectGeneratedFiles:
    def test_both_found(self, tmp_path: Path) -> None:
        (tmp_path / "prd.md").write_text("# PRD")
        (tmp_path / "bootstrap.md").write_text("# Bootstrap")
        result = detect_generated_files(tmp_path)
        assert result.prd_path == str(tmp_path / "prd.md")
        assert result.bootstrap_path == str(tmp_path / "bootstrap.md")
        assert result.prd_found is True
        assert result.bootstrap_found is True

    def test_only_prd(self, tmp_path: Path) -> None:
        (tmp_path / "prd.md").write_text("# PRD")
        result = detect_generated_files(tmp_path)
        assert result.prd_path == str(tmp_path / "prd.md")
        assert result.bootstrap_path is None
        assert result.prd_found is True
        assert result.bootstrap_found is False

    def test_neither_found(self, tmp_path: Path) -> None:
        result = detect_generated_files(tmp_path)
        assert result.prd_path is None
        assert result.bootstrap_path is None
        assert result.prd_found is False
        assert result.bootstrap_found is False

    def test_directory_not_detected_as_file(self, tmp_path: Path) -> None:
        (tmp_path / "prd.md").mkdir()
        result = detect_generated_files(tmp_path)
        assert result.prd_found is False

    def test_plans_subdirectory(self, tmp_path: Path) -> None:
        plans_dir = tmp_path / "plans"
        plans_dir.mkdir()
        (plans_dir / "prd.md").write_text("# PRD")
        result = detect_generated_files(tmp_path)
        assert result.prd_found is True
        assert result.prd_path == str(plans_dir / "prd.md")


class TestPrdDetectionResult:
    def test_frozen(self) -> None:
        result = PrdDetectionResult(prd_path="/tmp/prd.md", bootstrap_path=None)
        with pytest.raises(AttributeError):
            result.prd_path = "/other"  # type: ignore[misc]

    def test_prd_found_property(self) -> None:
        found = PrdDetectionResult(prd_path="/tmp/prd.md", bootstrap_path=None)
        assert found.prd_found is True
        not_found = PrdDetectionResult(prd_path=None, bootstrap_path=None)
        assert not_found.prd_found is False

    def test_bootstrap_found_property(self) -> None:
        found = PrdDetectionResult(
            prd_path="/tmp/prd.md", bootstrap_path="/tmp/bootstrap.md"
        )
        assert found.bootstrap_found is True
        not_found = PrdDetectionResult(prd_path="/tmp/prd.md", bootstrap_path=None)
        assert not_found.bootstrap_found is False

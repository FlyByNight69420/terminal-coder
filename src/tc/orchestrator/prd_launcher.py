"""Helper functions for launching Claude CLI to generate PRDs."""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path


class ClaudeNotFoundError(Exception):
    """Raised when the claude CLI binary is not found on PATH."""


@dataclass(frozen=True)
class PrdDetectionResult:
    """Result of scanning a project directory for generated PRD files."""

    prd_path: str | None
    bootstrap_path: str | None

    @property
    def prd_found(self) -> bool:
        return self.prd_path is not None

    @property
    def bootstrap_found(self) -> bool:
        return self.bootstrap_path is not None


def find_claude_binary() -> str:
    """Locate the claude CLI binary on PATH.

    Returns:
        Absolute path to the claude binary.

    Raises:
        ClaudeNotFoundError: If claude is not found on PATH.
    """
    path = shutil.which("claude")
    if path is None:
        raise ClaudeNotFoundError(
            "claude CLI not found on PATH. "
            "Install it from https://docs.anthropic.com/en/docs/claude-code"
        )
    return path


def prepare_idea_file(project_dir: Path, idea_text: str) -> Path:
    """Write idea text to idea.txt in the project directory.

    Args:
        project_dir: Directory to write into (must exist).
        idea_text: The idea text to write.

    Returns:
        Path to the written idea.txt file.

    Raises:
        ValueError: If idea_text is empty after stripping.
        FileNotFoundError: If project_dir does not exist.
    """
    stripped = idea_text.strip()
    if not stripped:
        raise ValueError("Idea text cannot be empty")
    if not project_dir.exists():
        raise FileNotFoundError(f"Directory does not exist: {project_dir}")
    idea_path = project_dir / "idea.txt"
    idea_path.write_text(stripped)
    return idea_path


def load_skill_content(
    skill_path: Path | None = None,
) -> str | None:
    """Read the prd-generation SKILL.md file content.

    Args:
        skill_path: Explicit path to the skill file. When None, checks
            the default location (~/.claude/skills/prd-generation/SKILL.md).

    Returns:
        File content as a string, or None if the file does not exist.
    """
    if skill_path is None:
        skill_path = (
            Path.home() / ".claude" / "skills" / "prd-generation" / "SKILL.md"
        )
    if skill_path.is_file():
        return skill_path.read_text()
    return None


def build_claude_command(
    claude_bin: str,
    prompt: str | None = None,
    system_prompt: str | None = None,
) -> list[str]:
    """Build the subprocess command list for launching claude.

    Args:
        claude_bin: Path to the claude binary.
        prompt: Optional initial prompt passed as a positional argument.
        system_prompt: Optional text appended to the system prompt via
            --append-system-prompt.

    Returns:
        Command list suitable for subprocess.run().
    """
    cmd = [claude_bin]
    if system_prompt is not None:
        cmd.extend(["--append-system-prompt", system_prompt])
    if prompt is not None:
        cmd.append(prompt)
    return cmd


def detect_generated_files(project_dir: Path) -> PrdDetectionResult:
    """Scan project directory for generated PRD and bootstrap files.

    Checks both the root directory and a plans/ subdirectory.

    Args:
        project_dir: Directory to scan.

    Returns:
        PrdDetectionResult with paths to found files.
    """
    prd_path: str | None = None
    bootstrap_path: str | None = None

    # Check plans/ subdirectory first, then root
    search_dirs = []
    plans_dir = project_dir / "plans"
    if plans_dir.is_dir():
        search_dirs.append(plans_dir)
    search_dirs.append(project_dir)

    for search_dir in search_dirs:
        if prd_path is None:
            candidate = search_dir / "prd.md"
            if candidate.is_file():
                prd_path = str(candidate)

        if bootstrap_path is None:
            candidate = search_dir / "bootstrap.md"
            if candidate.is_file():
                bootstrap_path = str(candidate)

    return PrdDetectionResult(prd_path=prd_path, bootstrap_path=bootstrap_path)

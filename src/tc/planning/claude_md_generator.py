"""Generate and write CLAUDE.md for target projects."""

from __future__ import annotations

from pathlib import Path


class ClaudeMdError(Exception):
    """Raised when CLAUDE.md content is invalid."""


def validate_claude_md(content: str) -> bool:
    """Validate that CLAUDE.md has required sections."""
    required_markers = ["build", "test", "style"]
    lower_content = content.lower()
    return all(marker in lower_content for marker in required_markers)


def write_claude_md(project_dir: Path, content: str) -> Path:
    """Write CLAUDE.md to the project root."""
    if not validate_claude_md(content):
        raise ClaudeMdError(
            "CLAUDE.md content missing required sections (Build/Test Commands, Code Style)"
        )

    claude_md_path = project_dir / "CLAUDE.md"
    claude_md_path.write_text(content)
    return claude_md_path

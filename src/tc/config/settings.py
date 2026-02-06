"""Project path configuration."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from tc.config.constants import BRIEFS_DIR, DB_FILENAME, LOGS_DIR, PLANS_DIR, TC_DIR


@dataclass(frozen=True)
class ProjectPaths:
    project_dir: Path
    tc_dir: Path
    db_path: Path
    briefs_dir: Path
    logs_dir: Path
    plans_dir: Path


def project_paths(project_dir: Path) -> ProjectPaths:
    """Create ProjectPaths from a project root directory."""
    tc_dir = project_dir / TC_DIR
    return ProjectPaths(
        project_dir=project_dir,
        tc_dir=tc_dir,
        db_path=tc_dir / DB_FILENAME,
        briefs_dir=tc_dir / BRIEFS_DIR,
        logs_dir=tc_dir / LOGS_DIR,
        plans_dir=tc_dir / PLANS_DIR,
    )

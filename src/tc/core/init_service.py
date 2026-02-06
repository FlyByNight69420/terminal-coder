"""Project initialization service.

Extracted from init_cmd.py so both the CLI and TUI wizard
can call the same logic.
"""

from __future__ import annotations

import shutil
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from tc.config.settings import project_paths
from tc.db.connection import create_connection, initialize_db
from tc.db.repository import Repository
from tc.mcp.config import write_mcp_config

# (step_name, "start" | "done" | "error")
StepCallback = Callable[[str, str], None]


@dataclass(frozen=True)
class InitResult:
    """Result of a successful project initialization."""

    project_id: str
    project_dir: Path
    project_name: str
    db_path: Path
    prd_dest: Path
    bootstrap_dest: Path | None


class ProjectAlreadyExistsError(Exception):
    """Raised when .tc/ directory already exists."""


def _notify(on_step: StepCallback | None, step: str, status: str) -> None:
    if on_step is not None:
        on_step(step, status)


def initialize_project(
    project_dir: Path,
    project_name: str,
    prd_path: Path,
    bootstrap_path: Path | None = None,
    *,
    on_step: StepCallback | None = None,
) -> InitResult:
    """Create .tc/ dir, DB, copy files, generate .mcp.json.

    Args:
        project_dir: Resolved project root directory (must exist).
        project_name: Human-readable project name.
        prd_path: Path to the PRD markdown file (must exist).
        bootstrap_path: Optional path to a bootstrap markdown file.
        on_step: Optional callback invoked with (step_name, status)
                 for each initialization step.

    Returns:
        InitResult with paths and identifiers.

    Raises:
        ProjectAlreadyExistsError: If .tc/ already exists in project_dir.
    """
    paths = project_paths(project_dir)

    if paths.tc_dir.exists():
        raise ProjectAlreadyExistsError(
            f"Project already initialized at {paths.tc_dir}"
        )

    # Create .tc directory structure
    _notify(on_step, "directories", "start")
    paths.tc_dir.mkdir(parents=True)
    paths.briefs_dir.mkdir()
    paths.logs_dir.mkdir()
    paths.plans_dir.mkdir()
    _notify(on_step, "directories", "done")

    # Initialize database
    _notify(on_step, "database", "start")
    initialize_db(paths.db_path)
    _notify(on_step, "database", "done")

    # Copy PRD to project root if not already there
    _notify(on_step, "prd", "start")
    prd_dest = project_dir / "prd.md"
    if prd_path.resolve() != prd_dest.resolve():
        shutil.copy2(prd_path, prd_dest)
    _notify(on_step, "prd", "done")

    # Copy bootstrap to project root if provided
    bootstrap_dest: Path | None = None
    if bootstrap_path is not None:
        _notify(on_step, "bootstrap", "start")
        bootstrap_dest = project_dir / "bootstrap.md"
        if bootstrap_path.resolve() != bootstrap_dest.resolve():
            shutil.copy2(bootstrap_path, bootstrap_dest)
        _notify(on_step, "bootstrap", "done")

    # Create project record
    _notify(on_step, "project_record", "start")
    conn = create_connection(paths.db_path)
    try:
        repo = Repository(conn)
        project_id = str(uuid.uuid4())
        repo.create_project(
            id=project_id,
            name=project_name,
            project_dir=str(project_dir),
            prd_path=str(prd_dest),
            bootstrap_path=str(bootstrap_dest) if bootstrap_dest else None,
        )
    finally:
        conn.close()
    _notify(on_step, "project_record", "done")

    # Generate .mcp.json
    _notify(on_step, "mcp_config", "start")
    write_mcp_config(project_dir)
    _notify(on_step, "mcp_config", "done")

    return InitResult(
        project_id=project_id,
        project_dir=project_dir,
        project_name=project_name,
        db_path=paths.db_path,
        prd_dest=prd_dest,
        bootstrap_dest=bootstrap_dest,
    )

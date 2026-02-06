"""tc pause and tc resume commands."""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console

from tc.config.settings import project_paths
from tc.core.enums import ProjectStatus
from tc.db.connection import create_connection
from tc.db.repository import Repository

console = Console()


def pause_command(
    project_dir: Path = typer.Option(
        None, "--project-dir", help="Project directory", resolve_path=True,
    ),
) -> None:
    """Pause the orchestration engine."""
    resolved_dir = project_dir or Path.cwd()
    paths = project_paths(resolved_dir)

    if not paths.db_path.exists():
        console.print("[red]No project found.[/red]")
        raise typer.Exit(code=1)

    conn = create_connection(paths.db_path)
    try:
        repo = Repository(conn)
        row = conn.execute("SELECT id FROM projects LIMIT 1").fetchone()
        if row is None:
            console.print("[red]No project found.[/red]")
            raise typer.Exit(code=1)

        repo.update_project_status(str(row["id"]), ProjectStatus.PAUSED)
        console.print("[yellow]Project paused. Running tasks will complete but no new tasks will start.[/yellow]")
    finally:
        conn.close()


def resume_command(
    project_dir: Path = typer.Option(
        None, "--project-dir", help="Project directory", resolve_path=True,
    ),
) -> None:
    """Resume the orchestration engine."""
    resolved_dir = project_dir or Path.cwd()
    paths = project_paths(resolved_dir)

    if not paths.db_path.exists():
        console.print("[red]No project found.[/red]")
        raise typer.Exit(code=1)

    conn = create_connection(paths.db_path)
    try:
        repo = Repository(conn)
        row = conn.execute("SELECT id FROM projects LIMIT 1").fetchone()
        if row is None:
            console.print("[red]No project found.[/red]")
            raise typer.Exit(code=1)

        repo.update_project_status(str(row["id"]), ProjectStatus.RUNNING)
        console.print("[green]Project resumed.[/green]")
    finally:
        conn.close()

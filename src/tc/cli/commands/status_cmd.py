"""tc status command - show project status."""

from __future__ import annotations

import json
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from tc.config.settings import project_paths
from tc.core.enums import TaskStatus
from tc.db.connection import create_connection
from tc.db.repository import Repository

console = Console()


def _resolve_project_dir(project_dir: Path | None) -> Path:
    if project_dir is not None:
        return project_dir
    return Path.cwd()


def status_command(
    project_dir: Path = typer.Option(
        None, "--project-dir", help="Project directory", resolve_path=True,
    ),
    as_json: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Show project status with phase and task summary."""
    resolved_dir = _resolve_project_dir(project_dir)
    paths = project_paths(resolved_dir)

    if not paths.db_path.exists():
        console.print("[red]No project found. Run 'tc init' first.[/red]")
        raise typer.Exit(code=1)

    conn = create_connection(paths.db_path)
    try:
        repo = Repository(conn)

        # Get the first (and only) project
        rows = conn.execute("SELECT id FROM projects LIMIT 1").fetchone()
        if rows is None:
            console.print("[red]No project found in database.[/red]")
            raise typer.Exit(code=1)

        project_id = str(rows["id"])
        project = repo.get_project(project_id)
        phases = repo.get_phases_by_project(project_id)

        if as_json:
            _output_json(project, phases, repo)
            return

        # Header
        console.print(f"\n[bold]{project.name}[/bold]  status: {project.status}")
        console.print(f"  dir: {project.project_dir}\n")

        if not phases:
            console.print("[dim]No phases yet. Run 'tc plan' to decompose the PRD.[/dim]")
            return

        # Phase table
        table = Table(title="Phases", show_lines=True)
        table.add_column("Seq", style="dim", width=4)
        table.add_column("Phase", min_width=20)
        table.add_column("Status", width=12)
        table.add_column("Pending", justify="right", width=8)
        table.add_column("Running", justify="right", width=8)
        table.add_column("Done", justify="right", width=8)
        table.add_column("Failed", justify="right", width=8)

        for phase in phases:
            tasks = repo.get_tasks_by_phase(phase.id)
            counts = _count_statuses(tasks)
            status_style = _status_style(phase.status.value)
            table.add_row(
                str(phase.sequence),
                phase.name,
                f"[{status_style}]{phase.status}[/{status_style}]",
                str(counts["pending"]),
                str(counts["running"]),
                str(counts["completed"]),
                str(counts["failed"]),
            )

        console.print(table)
    finally:
        conn.close()


def _count_statuses(tasks: list[object]) -> dict[str, int]:
    counts = {"pending": 0, "running": 0, "completed": 0, "failed": 0}
    for task in tasks:
        status = task.status.value  # type: ignore[attr-defined]
        if status in ("pending", "queued"):
            counts["pending"] += 1
        elif status in ("running", "retrying"):
            counts["running"] += 1
        elif status == "completed":
            counts["completed"] += 1
        elif status in ("failed", "paused"):
            counts["failed"] += 1
    return counts


def _status_style(status: str) -> str:
    styles = {
        "pending": "dim",
        "in_progress": "yellow",
        "completed": "green",
        "failed": "red",
        "skipped": "dim",
        "initialized": "dim",
        "planning": "yellow",
        "planned": "cyan",
        "running": "yellow",
        "paused": "yellow",
    }
    return styles.get(status, "white")


def _output_json(project: object, phases: list[object], repo: Repository) -> None:
    data = {
        "project": {
            "id": project.id,  # type: ignore[attr-defined]
            "name": project.name,  # type: ignore[attr-defined]
            "status": project.status.value,  # type: ignore[attr-defined]
            "project_dir": project.project_dir,  # type: ignore[attr-defined]
        },
        "phases": [],
    }
    for phase in phases:
        tasks = repo.get_tasks_by_phase(phase.id)  # type: ignore[attr-defined]
        phase_data = {
            "sequence": phase.sequence,  # type: ignore[attr-defined]
            "name": phase.name,  # type: ignore[attr-defined]
            "status": phase.status.value,  # type: ignore[attr-defined]
            "tasks": [
                {
                    "id": t.id,
                    "name": t.name,
                    "type": t.task_type.value,
                    "status": t.status.value,
                }
                for t in tasks
            ],
        }
        data["phases"].append(phase_data)
    console.print_json(json.dumps(data))

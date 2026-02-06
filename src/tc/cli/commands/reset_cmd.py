"""tc reset command - reset task or phase status."""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console

from tc.config.settings import project_paths
from tc.core.enums import PhaseStatus, TaskStatus
from tc.db.connection import create_connection
from tc.db.repository import Repository

console = Console()


def reset_command(
    task_id: str = typer.Option(None, "--task", help="Task ID to reset"),
    phase_num: int = typer.Option(None, "--phase", help="Phase number to reset"),
    project_dir: Path = typer.Option(
        None, "--project-dir", help="Project directory", resolve_path=True,
    ),
) -> None:
    """Reset a task or phase back to pending."""
    if task_id is None and phase_num is None:
        console.print("[red]Specify --task or --phase to reset.[/red]")
        raise typer.Exit(code=1)

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

        project_id = str(row["id"])

        if task_id:
            _reset_task(repo, conn, task_id)
        elif phase_num is not None:
            _reset_phase(repo, conn, project_id, phase_num)
    finally:
        conn.close()


def _reset_task(repo: Repository, conn: object, task_id: str) -> None:
    """Reset a single task to pending."""
    try:
        task = repo.get_task(task_id)
    except ValueError:
        console.print(f"[red]Task not found: {task_id}[/red]")
        raise typer.Exit(code=1)

    # Reset task
    conn.execute(  # type: ignore[union-attr]
        "UPDATE tasks SET status = 'pending', retry_count = 0, error_context = NULL, "
        "started_at = NULL, completed_at = NULL WHERE id = ?",
        (task_id,),
    )
    # Delete associated sessions
    conn.execute("DELETE FROM sessions WHERE task_id = ?", (task_id,))  # type: ignore[union-attr]
    conn.commit()  # type: ignore[union-attr]

    console.print(f"[green]Task '{task.name}' reset to pending.[/green]")


def _reset_phase(repo: Repository, conn: object, project_id: str, phase_num: int) -> None:
    """Reset all tasks in a phase to pending."""
    phases = repo.get_phases_by_project(project_id)
    phase = None
    for p in phases:
        if p.sequence == phase_num:
            phase = p
            break

    if phase is None:
        console.print(f"[red]Phase {phase_num} not found.[/red]")
        raise typer.Exit(code=1)

    tasks = repo.get_tasks_by_phase(phase.id)

    # Reset phase
    conn.execute(  # type: ignore[union-attr]
        "UPDATE phases SET status = 'pending', started_at = NULL, completed_at = NULL WHERE id = ?",
        (phase.id,),
    )

    # Reset all tasks in phase
    for task in tasks:
        conn.execute(  # type: ignore[union-attr]
            "UPDATE tasks SET status = 'pending', retry_count = 0, error_context = NULL, "
            "started_at = NULL, completed_at = NULL WHERE id = ?",
            (task.id,),
        )
        conn.execute("DELETE FROM sessions WHERE task_id = ?", (task.id,))  # type: ignore[union-attr]

    conn.commit()  # type: ignore[union-attr]
    console.print(f"[green]Phase '{phase.name}' ({len(tasks)} tasks) reset to pending.[/green]")

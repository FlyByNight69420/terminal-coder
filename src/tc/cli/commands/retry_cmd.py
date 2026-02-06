"""tc retry command - retry a failed task."""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console

from tc.config.settings import project_paths
from tc.core.enums import TaskStatus
from tc.db.connection import create_connection
from tc.db.repository import Repository

console = Console()


def retry_command(
    task_id: str = typer.Option(..., "--task", help="Task ID to retry"),
    project_dir: Path = typer.Option(
        None, "--project-dir", help="Project directory", resolve_path=True,
    ),
) -> None:
    """Retry a failed or paused task."""
    resolved_dir = project_dir or Path.cwd()
    paths = project_paths(resolved_dir)

    if not paths.db_path.exists():
        console.print("[red]No project found.[/red]")
        raise typer.Exit(code=1)

    conn = create_connection(paths.db_path)
    try:
        repo = Repository(conn)
        try:
            task = repo.get_task(task_id)
        except ValueError:
            console.print(f"[red]Task not found: {task_id}[/red]")
            raise typer.Exit(code=1)

        if task.status not in (TaskStatus.FAILED, TaskStatus.PAUSED):
            console.print(f"[yellow]Task status is '{task.status}', can only retry failed/paused tasks.[/yellow]")
            raise typer.Exit(code=1)

        # Reset to pending for re-scheduling
        repo.update_task_status(task_id, TaskStatus.QUEUED)
        console.print(f"[green]Task '{task.name}' queued for retry.[/green]")
    finally:
        conn.close()

"""tc history command - show event history."""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from tc.config.settings import project_paths
from tc.db.connection import create_connection
from tc.db.repository import Repository

console = Console()


def history_command(
    project_dir: Path = typer.Option(
        None, "--project-dir", help="Project directory", resolve_path=True,
    ),
    task: str = typer.Option(None, "--task", help="Filter by task ID"),
    phase: int = typer.Option(None, "--phase", help="Filter by phase number"),
    limit: int = typer.Option(50, "--limit", help="Number of events to show"),
) -> None:
    """Show event history."""
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

        if task:
            events = repo.get_events_by_entity("task", task)
        else:
            events = repo.get_events_by_project(project_id, limit=limit)

        if not events:
            console.print("[dim]No events found.[/dim]")
            return

        table = Table(title="Event History", show_lines=False)
        table.add_column("Time", style="dim", width=10)
        table.add_column("Type", width=20)
        table.add_column("Entity", width=15)
        table.add_column("Details", min_width=30)

        for event in events:
            timestamp = event.created_at.strftime("%H:%M:%S")
            details = ""
            if event.old_value and event.new_value:
                details = f"{event.old_value} -> {event.new_value}"
            elif event.new_value:
                details = event.new_value

            table.add_row(
                timestamp,
                event.event_type.value,
                f"{event.entity_type}/{event.entity_id[:8]}",
                details,
            )

        console.print(table)
    finally:
        conn.close()

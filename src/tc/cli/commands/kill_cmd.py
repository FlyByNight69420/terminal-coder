"""tc kill command - kill a running session."""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console

from tc.config.settings import project_paths
from tc.core.enums import SessionStatus
from tc.db.connection import create_connection
from tc.db.repository import Repository

console = Console()


def kill_command(
    session_id: str = typer.Option(None, "--session", help="Session ID to kill"),
    force: bool = typer.Option(False, "--force", help="Force kill"),
    project_dir: Path = typer.Option(
        None, "--project-dir", help="Project directory", resolve_path=True,
    ),
) -> None:
    """Kill a running session."""
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

        if session_id:
            repo.update_session_status(session_id, SessionStatus.KILLED)
            console.print(f"[yellow]Session {session_id} marked as killed.[/yellow]")
        else:
            # Kill all active sessions
            active = repo.get_active_sessions(project_id)
            if not active:
                console.print("[dim]No active sessions.[/dim]")
                return
            for session in active:
                repo.update_session_status(session.id, SessionStatus.KILLED)
                console.print(f"[yellow]Session {session.id} marked as killed.[/yellow]")
    finally:
        conn.close()

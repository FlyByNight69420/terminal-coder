"""tc run command - start the orchestration engine."""

from __future__ import annotations

import asyncio
from pathlib import Path

import typer
from rich.console import Console

from tc.config.settings import project_paths
from tc.core.enums import ProjectStatus
from tc.core.events import EventBus
from tc.core.scheduler import Scheduler
from tc.db.connection import create_connection
from tc.db.repository import Repository
from tc.orchestrator.engine import OrchestrationEngine
from tc.orchestrator.review_coordinator import ReviewCoordinator
from tc.orchestrator.session_manager import SessionManager
from tc.templates.renderer import BriefRenderer
from tc.tmux.manager import TmuxManager

console = Console()


def run_command(
    project_dir: Path = typer.Option(
        None, "--project-dir", help="Project directory", resolve_path=True,
    ),
    headless: bool = typer.Option(False, "--headless", help="Run without TUI"),
) -> None:
    """Start the orchestration engine."""
    resolved_dir = project_dir or Path.cwd()
    paths = project_paths(resolved_dir)

    if not paths.db_path.exists():
        console.print("[red]No project found. Run 'tc init' first.[/red]")
        raise typer.Exit(code=1)

    conn = create_connection(paths.db_path)
    try:
        repo = Repository(conn)
        row = conn.execute("SELECT id, name, status FROM projects LIMIT 1").fetchone()
        if row is None:
            console.print("[red]No project found in database.[/red]")
            raise typer.Exit(code=1)

        project_id = str(row["id"])
        project_name = str(row["name"])
        status = str(row["status"])

        if status not in ("planned", "paused", "running"):
            console.print(f"[red]Project status is '{status}'. Run 'tc plan' first.[/red]")
            raise typer.Exit(code=1)

        # Set up TMUX
        tmux = TmuxManager(project_name)
        tmux.setup()

        # Build orchestration components
        event_bus = EventBus()
        scheduler = Scheduler(repo)
        renderer = BriefRenderer()
        session_mgr = SessionManager(tmux, repo, resolved_dir)
        review_coord = ReviewCoordinator(repo, renderer)

        engine = OrchestrationEngine(
            repository=repo,
            session_manager=session_mgr,
            scheduler=scheduler,
            review_coordinator=review_coord,
            event_bus=event_bus,
            project_id=project_id,
            project_dir=resolved_dir,
        )

        console.print(f"[green]Starting orchestration for '{project_name}'[/green]")
        console.print(f"  TMUX session: {tmux.session_name}")
        console.print(f"  Attach: tmux attach -t {tmux.session_name}")
        console.print()

        if headless:
            # Log events to console
            def _log_event(event: object) -> None:
                console.print(f"  [{event.event_type}] {event.message}")  # type: ignore[attr-defined]

            event_bus.subscribe(_log_event)  # type: ignore[arg-type]

        try:
            asyncio.run(engine.run())
        except KeyboardInterrupt:
            console.print("\n[yellow]Stopping engine...[/yellow]")
            engine.stop()
        finally:
            if not tmux.session_exists():
                pass  # Already cleaned up
    finally:
        conn.close()

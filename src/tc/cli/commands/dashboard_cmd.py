"""tc dashboard command - launch TUI dashboard."""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console

from tc.config.settings import project_paths

console = Console()


def dashboard_command(
    project_dir: Path = typer.Option(
        None, "--project-dir", help="Project directory", resolve_path=True,
    ),
) -> None:
    """Launch TUI dashboard in read-only mode."""
    resolved_dir = project_dir or Path.cwd()
    paths = project_paths(resolved_dir)

    if not paths.db_path.exists():
        console.print("[red]No project found. Run 'tc init' first.[/red]")
        raise typer.Exit(code=1)

    from tc.tui.app import TerminalCoderApp

    app = TerminalCoderApp(project_dir=resolved_dir)
    app.run()

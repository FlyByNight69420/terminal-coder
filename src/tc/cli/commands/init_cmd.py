"""tc init command - initialize a new project."""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console

from tc.core.init_service import (
    InitResult,
    ProjectAlreadyExistsError,
    initialize_project,
)

console = Console()


def init_command(
    project_dir: Path | None = typer.Argument(
        None, help="Project directory to initialize", exists=True, resolve_path=True,
    ),
    prd: Path | None = typer.Option(
        None, "--prd", help="Path to PRD markdown file", exists=True, resolve_path=True,
    ),
    bootstrap: Path | None = typer.Option(
        None, "--bootstrap", help="Path to bootstrap markdown file",
        exists=True, resolve_path=True,
    ),
    name: str | None = typer.Option(
        None, "--name", help="Project name (defaults to directory name)",
    ),
) -> None:
    """Initialize a new Terminal Coder project."""
    # Launch wizard when called with no args
    if project_dir is None or prd is None:
        from tc.tui.onboarding.app import OnboardingApp

        OnboardingApp().run()
        return

    project_name = name or project_dir.name

    try:
        result: InitResult = initialize_project(
            project_dir=project_dir,
            project_name=project_name,
            prd_path=prd,
            bootstrap_path=bootstrap,
        )
    except ProjectAlreadyExistsError as exc:
        console.print(f"[yellow]{exc}[/yellow]")
        raise typer.Exit(code=1) from None

    msg = f"Initialized project '{result.project_name}' at {result.project_dir}"
    console.print(f"[green]{msg}[/green]")
    console.print(f"  Database: {result.db_path}")
    console.print(f"  PRD: {result.prd_dest}")
    if result.bootstrap_dest:
        console.print(f"  Bootstrap: {result.bootstrap_dest}")
    console.print()
    console.print("[bold]Next steps:[/bold]")
    if result.bootstrap_dest:
        console.print("  1. tc verify --project-dir", str(result.project_dir))
    console.print("  2. tc plan --project-dir", str(result.project_dir))
    console.print("  3. tc run --project-dir", str(result.project_dir))

"""tc init command - initialize a new project."""

from __future__ import annotations

import shutil
import uuid
from pathlib import Path

import typer
from rich.console import Console

from tc.config.settings import project_paths
from tc.db.connection import create_connection, initialize_db
from tc.db.repository import Repository
from tc.mcp.config import write_mcp_config

console = Console()


def init_command(
    project_dir: Path = typer.Argument(
        ..., help="Project directory to initialize", exists=True, resolve_path=True,
    ),
    prd: Path = typer.Option(
        ..., "--prd", help="Path to PRD markdown file", exists=True, resolve_path=True,
    ),
    bootstrap: Path = typer.Option(
        None, "--bootstrap", help="Path to bootstrap markdown file",
        exists=True, resolve_path=True,
    ),
    name: str = typer.Option(
        None, "--name", help="Project name (defaults to directory name)",
    ),
) -> None:
    """Initialize a new Terminal Coder project."""
    project_name = name or project_dir.name
    paths = project_paths(project_dir)

    if paths.tc_dir.exists():
        console.print(f"[yellow]Project already initialized at {paths.tc_dir}[/yellow]")
        raise typer.Exit(code=1)

    # Create .tc directory structure
    paths.tc_dir.mkdir(parents=True)
    paths.briefs_dir.mkdir()
    paths.logs_dir.mkdir()
    paths.plans_dir.mkdir()

    # Initialize database
    initialize_db(paths.db_path)

    # Copy PRD to project root if not already there
    prd_dest = project_dir / "prd.md"
    if prd.resolve() != prd_dest.resolve():
        shutil.copy2(prd, prd_dest)

    # Copy bootstrap to project root if provided and not already there
    bootstrap_dest = None
    if bootstrap is not None:
        bootstrap_dest = project_dir / "bootstrap.md"
        if bootstrap.resolve() != bootstrap_dest.resolve():
            shutil.copy2(bootstrap, bootstrap_dest)

    # Create project record
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

    # Generate .mcp.json
    write_mcp_config(project_dir)

    console.print(f"[green]Initialized project '{project_name}' at {project_dir}[/green]")
    console.print(f"  Database: {paths.db_path}")
    console.print(f"  PRD: {prd_dest}")
    if bootstrap_dest:
        console.print(f"  Bootstrap: {bootstrap_dest}")
    console.print()
    console.print("[bold]Next steps:[/bold]")
    if bootstrap_dest:
        console.print("  1. tc verify --project-dir", str(project_dir))
    console.print("  2. tc plan --project-dir", str(project_dir))
    console.print("  3. tc run --project-dir", str(project_dir))

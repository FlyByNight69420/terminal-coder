"""tc verify command - run bootstrap verification checks."""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from tc.bootstrap.verifier import BootstrapVerifier
from tc.config.settings import project_paths
from tc.db.connection import create_connection
from tc.db.repository import Repository

console = Console()


def verify_command(
    project_dir: Path = typer.Option(
        None, "--project-dir", help="Project directory", resolve_path=True,
    ),
) -> None:
    """Run bootstrap verification checks."""
    resolved_dir = project_dir or Path.cwd()
    paths = project_paths(resolved_dir)

    if not paths.db_path.exists():
        console.print("[red]No project found. Run 'tc init' first.[/red]")
        raise typer.Exit(code=1)

    conn = create_connection(paths.db_path)
    try:
        repo = Repository(conn)
        rows = conn.execute("SELECT id, bootstrap_path FROM projects LIMIT 1").fetchone()
        if rows is None:
            console.print("[red]No project found in database.[/red]")
            raise typer.Exit(code=1)

        project_id = str(rows["id"])
        bootstrap_path = rows["bootstrap_path"]

        if bootstrap_path is None:
            console.print("[yellow]No bootstrap.md configured for this project.[/yellow]")
            raise typer.Exit(code=1)

        verifier = BootstrapVerifier(repo, resolved_dir)
        report = verifier.verify(project_id, Path(bootstrap_path))

        # Display results
        table = Table(title="Bootstrap Verification", show_lines=True)
        table.add_column("Check", min_width=25)
        table.add_column("Type", width=12)
        table.add_column("Result", width=8)
        table.add_column("Output", max_width=50)

        for result in report.results:
            status = "[green]PASS[/green]" if result.passed else "[red]FAIL[/red]"
            output = result.stdout[:100] if result.stdout else result.stderr[:100] if result.stderr else ""
            table.add_row(result.name, result.check_type, status, output.strip())

        console.print(table)
        console.print(
            f"\n[bold]{report.passed}/{report.total} checks passed[/bold]"
        )

        if report.failed > 0:
            console.print("[red]Some checks failed. Fix issues before running.[/red]")
            raise typer.Exit(code=1)

        console.print("[green]All checks passed.[/green]")
    finally:
        conn.close()

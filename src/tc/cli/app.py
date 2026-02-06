"""Terminal Coder CLI application."""

from __future__ import annotations

from typing import Optional

import typer

from tc import __version__
from tc.cli.commands.init_cmd import init_command
from tc.cli.commands.status_cmd import status_command
from tc.cli.commands.verify_cmd import verify_command

app = typer.Typer(
    name="tc",
    help="Terminal Coder - Autonomous software building orchestrator using Claude Code",
    no_args_is_help=True,
)


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"tc {__version__}")
        raise typer.Exit()


@app.callback()
def _main(
    version: Optional[bool] = typer.Option(
        None, "--version", "-V", callback=_version_callback, is_eager=True,
        help="Show version and exit.",
    ),
) -> None:
    """Terminal Coder - Autonomous software building orchestrator using Claude Code."""


# Register commands
app.command("init")(init_command)
app.command("status")(status_command)
app.command("verify")(verify_command)


@app.command("plan")
def plan_command_stub() -> None:
    """Decompose PRD into phases and tasks. (Not yet implemented)"""
    typer.echo("Not yet implemented")
    raise typer.Exit(code=1)


@app.command("run")
def run_command_stub() -> None:
    """Start the orchestration engine. (Not yet implemented)"""
    typer.echo("Not yet implemented")
    raise typer.Exit(code=1)


@app.command("pause")
def pause_command_stub() -> None:
    """Pause orchestration. (Not yet implemented)"""
    typer.echo("Not yet implemented")
    raise typer.Exit(code=1)


@app.command("resume")
def resume_command_stub() -> None:
    """Resume orchestration. (Not yet implemented)"""
    typer.echo("Not yet implemented")
    raise typer.Exit(code=1)


@app.command("dashboard")
def dashboard_command_stub() -> None:
    """Launch TUI dashboard. (Not yet implemented)"""
    typer.echo("Not yet implemented")
    raise typer.Exit(code=1)


def main() -> None:
    app()

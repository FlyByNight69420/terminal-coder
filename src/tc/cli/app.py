"""Terminal Coder CLI application."""

from __future__ import annotations

from typing import Optional

import typer

from tc import __version__
from tc.cli.commands.init_cmd import init_command
from tc.cli.commands.kill_cmd import kill_command
from tc.cli.commands.pause_cmd import pause_command, resume_command
from tc.cli.commands.plan_cmd import plan_command
from tc.cli.commands.retry_cmd import retry_command
from tc.cli.commands.run_cmd import run_command
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
app.command("plan")(plan_command)
app.command("run")(run_command)
app.command("pause")(pause_command)
app.command("resume")(resume_command)
app.command("retry")(retry_command)
app.command("kill")(kill_command)


@app.command("dashboard")
def dashboard_command_stub() -> None:
    """Launch TUI dashboard. (Not yet implemented)"""
    typer.echo("Not yet implemented")
    raise typer.Exit(code=1)


def main() -> None:
    app()

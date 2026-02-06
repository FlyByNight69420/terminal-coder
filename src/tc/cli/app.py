"""Terminal Coder CLI application."""

from __future__ import annotations

from typing import Optional

import typer

from tc import __version__

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


def main() -> None:
    app()

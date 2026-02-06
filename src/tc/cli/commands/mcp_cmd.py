"""tc mcp-server command - internal command for Claude Code MCP integration."""

from __future__ import annotations

import asyncio
from pathlib import Path

import typer

from tc.mcp.server import run_server


def mcp_server_command(
    project_dir: Path = typer.Option(
        ..., "--project-dir", help="Project directory", resolve_path=True,
    ),
) -> None:
    """Start the MCP server (internal - called by Claude Code via .mcp.json)."""
    asyncio.run(run_server(project_dir))

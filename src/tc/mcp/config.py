"""MCP server configuration for Claude Code integration."""

from __future__ import annotations

import json
from pathlib import Path


def generate_mcp_config(project_dir: Path) -> dict[str, object]:
    """Generate the .mcp.json configuration content."""
    return {
        "mcpServers": {
            "tc": {
                "command": "tc",
                "args": ["mcp-server", "--project-dir", str(project_dir.resolve())],
            }
        }
    }


def write_mcp_config(project_dir: Path) -> Path:
    """Write .mcp.json to the project directory."""
    config = generate_mcp_config(project_dir)
    config_path = project_dir / ".mcp.json"
    config_path.write_text(json.dumps(config, indent=2) + "\n")
    return config_path

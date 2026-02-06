"""MCP server for Claude Code session communication."""

from __future__ import annotations

import json
from pathlib import Path

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from tc.mcp.tools import (
    ToolError,
    tc_get_context,
    tc_report_completion,
    tc_report_failure,
    tc_report_progress,
    tc_report_review,
    tc_request_human_input,
)


def create_mcp_server(project_dir: Path) -> Server:
    """Create and configure the MCP server with all tools."""
    from tc.config.settings import project_paths

    paths = project_paths(project_dir)
    db_path = paths.db_path

    server = Server("tc")

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        return [
            Tool(
                name="tc_report_progress",
                description="Report progress on the current task",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "task_id": {"type": "string", "description": "Task ID"},
                        "status": {"type": "string", "description": "Current status message"},
                        "message": {"type": "string", "description": "Progress details"},
                        "percent_complete": {
                            "type": "integer", "description": "Completion percentage (0-100)",
                        },
                    },
                    "required": ["task_id", "status", "message"],
                },
            ),
            Tool(
                name="tc_report_completion",
                description="Report that the current task is complete",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "task_id": {"type": "string", "description": "Task ID"},
                        "summary": {"type": "string", "description": "Completion summary"},
                        "files_changed": {
                            "type": "array", "items": {"type": "string"},
                            "description": "List of files changed",
                        },
                        "test_results": {
                            "type": "string", "description": "Test results summary",
                        },
                    },
                    "required": ["task_id", "summary"],
                },
            ),
            Tool(
                name="tc_report_failure",
                description="Report that the current task has failed",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "task_id": {"type": "string", "description": "Task ID"},
                        "error_type": {"type": "string", "description": "Type of error"},
                        "error_message": {"type": "string", "description": "Error details"},
                        "attempted_fixes": {
                            "type": "array", "items": {"type": "string"},
                            "description": "Fixes that were attempted",
                        },
                    },
                    "required": ["task_id", "error_type", "error_message"],
                },
            ),
            Tool(
                name="tc_report_review",
                description="Submit code review findings",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "task_id": {"type": "string", "description": "Review task ID"},
                        "verdict": {
                            "type": "string",
                            "enum": ["approved", "changes_requested", "critical_issues"],
                            "description": "Review verdict",
                        },
                        "findings": {
                            "type": "array", "items": {"type": "string"},
                            "description": "List of findings",
                        },
                        "summary": {"type": "string", "description": "Review summary"},
                    },
                    "required": ["task_id", "verdict", "findings", "summary"],
                },
            ),
            Tool(
                name="tc_get_context",
                description="Get context about completed work and project state",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "task_id": {"type": "string", "description": "Current task ID"},
                        "include": {
                            "type": "array", "items": {"type": "string"},
                            "description": "Context sections to include",
                        },
                    },
                    "required": ["task_id"],
                },
            ),
            Tool(
                name="tc_request_human_input",
                description="Request human input for a decision",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "task_id": {"type": "string", "description": "Task ID"},
                        "question": {"type": "string", "description": "Question to ask"},
                        "options": {
                            "type": "array", "items": {"type": "string"},
                            "description": "Available options",
                        },
                        "context": {"type": "string", "description": "Additional context"},
                    },
                    "required": ["task_id", "question"],
                },
            ),
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict[str, object]) -> list[TextContent]:
        try:
            result = _dispatch_tool(name, arguments, db_path)
            return [TextContent(type="text", text=json.dumps(result))]
        except ToolError as e:
            return [TextContent(type="text", text=json.dumps({"error": str(e)}))]
        except Exception as e:
            return [TextContent(type="text", text=json.dumps({"error": f"Internal error: {e}"}))]

    return server


def _dispatch_tool(
    name: str, arguments: dict[str, object], db_path: Path
) -> dict[str, object]:
    """Route tool calls to the appropriate handler."""
    if name == "tc_report_progress":
        return tc_report_progress(
            db_path,
            task_id=str(arguments["task_id"]),
            status=str(arguments["status"]),
            message=str(arguments["message"]),
            percent_complete=arguments.get("percent_complete"),  # type: ignore[arg-type]
        )
    elif name == "tc_report_completion":
        return tc_report_completion(
            db_path,
            task_id=str(arguments["task_id"]),
            summary=str(arguments["summary"]),
            files_changed=arguments.get("files_changed"),  # type: ignore[arg-type]
            test_results=arguments.get("test_results"),  # type: ignore[arg-type]
        )
    elif name == "tc_report_failure":
        return tc_report_failure(
            db_path,
            task_id=str(arguments["task_id"]),
            error_type=str(arguments["error_type"]),
            error_message=str(arguments["error_message"]),
            attempted_fixes=arguments.get("attempted_fixes"),  # type: ignore[arg-type]
        )
    elif name == "tc_report_review":
        return tc_report_review(
            db_path,
            task_id=str(arguments["task_id"]),
            verdict=str(arguments["verdict"]),
            findings=list(arguments.get("findings", [])),  # type: ignore[arg-type]
            summary=str(arguments["summary"]),
        )
    elif name == "tc_get_context":
        return tc_get_context(
            db_path,
            task_id=str(arguments["task_id"]),
            include=arguments.get("include"),  # type: ignore[arg-type]
        )
    elif name == "tc_request_human_input":
        return tc_request_human_input(
            db_path,
            task_id=str(arguments["task_id"]),
            question=str(arguments["question"]),
            options=arguments.get("options"),  # type: ignore[arg-type]
            context=arguments.get("context"),  # type: ignore[arg-type]
        )
    else:
        raise ToolError(f"Unknown tool: {name}")


async def run_server(project_dir: Path) -> None:
    """Run the MCP server using stdio transport."""
    server = create_mcp_server(project_dir)
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())

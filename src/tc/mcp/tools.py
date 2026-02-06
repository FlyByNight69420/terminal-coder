"""MCP tool handlers for Claude Code session communication."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from tc.core.enums import EventType, TaskStatus, TaskType
from tc.db.connection import create_connection
from tc.db.repository import Repository


class ToolError(Exception):
    """Raised when a tool invocation fails validation."""


def _get_repo(db_path: Path) -> tuple[sqlite3.Connection, Repository]:
    """Create a fresh connection and repository for each tool call."""
    conn = create_connection(db_path)
    return conn, Repository(conn)


def tc_report_progress(
    db_path: Path,
    task_id: str,
    status: str,
    message: str,
    percent_complete: int | None = None,
) -> dict[str, object]:
    """Report progress on a task."""
    conn, repo = _get_repo(db_path)
    try:
        task = repo.get_task(task_id)
        if task.status != TaskStatus.RUNNING:
            raise ToolError(f"Task {task_id} is not running (status: {task.status})")

        metadata = json.dumps({
            "status": status,
            "message": message,
            "percent_complete": percent_complete,
        })

        repo.create_event(
            project_id=task.project_id,
            entity_type="task",
            entity_id=task_id,
            event_type=EventType.STATUS_CHANGED,
            new_value=status,
            metadata=metadata,
        )

        return {"success": True, "message": f"Progress reported: {message}"}
    finally:
        conn.close()


def tc_report_completion(
    db_path: Path,
    task_id: str,
    summary: str,
    files_changed: list[str] | None = None,
    test_results: str | None = None,
) -> dict[str, object]:
    """Report task completion."""
    conn, repo = _get_repo(db_path)
    try:
        task = repo.get_task(task_id)
        if task.status != TaskStatus.RUNNING:
            raise ToolError(f"Task {task_id} is not running (status: {task.status})")

        metadata = json.dumps({
            "summary": summary,
            "files_changed": files_changed or [],
            "test_results": test_results,
        })

        repo.update_task_status(task_id, TaskStatus.COMPLETED)
        repo.create_event(
            project_id=task.project_id,
            entity_type="task",
            entity_id=task_id,
            event_type=EventType.STATUS_CHANGED,
            old_value="running",
            new_value="completed",
            metadata=metadata,
        )

        return {"success": True, "message": f"Task completed: {summary[:100]}"}
    finally:
        conn.close()


def tc_report_failure(
    db_path: Path,
    task_id: str,
    error_type: str,
    error_message: str,
    attempted_fixes: list[str] | None = None,
) -> dict[str, object]:
    """Report task failure."""
    conn, repo = _get_repo(db_path)
    try:
        task = repo.get_task(task_id)
        if task.status != TaskStatus.RUNNING:
            raise ToolError(f"Task {task_id} is not running (status: {task.status})")

        metadata = json.dumps({
            "error_type": error_type,
            "error_message": error_message,
            "attempted_fixes": attempted_fixes or [],
        })

        repo.update_task_error(task_id, error_message[:2000])

        repo.create_event(
            project_id=task.project_id,
            entity_type="task",
            entity_id=task_id,
            event_type=EventType.ERROR,
            new_value=error_type,
            metadata=metadata,
        )

        return {"success": True, "message": f"Failure reported: {error_type}"}
    finally:
        conn.close()


def tc_report_review(
    db_path: Path,
    task_id: str,
    verdict: str,
    findings: list[str],
    summary: str,
) -> dict[str, object]:
    """Report review results."""
    conn, repo = _get_repo(db_path)
    try:
        task = repo.get_task(task_id)
        if task.task_type not in (TaskType.REVIEW, TaskType.SECURITY_REVIEW):
            raise ToolError(f"Task {task_id} is not a review task (type: {task.task_type})")

        metadata = json.dumps({
            "verdict": verdict,
            "findings": findings,
            "summary": summary,
        })

        event_type = EventType.STATUS_CHANGED
        if verdict == "critical_issues":
            event_type = EventType.ERROR

        repo.create_event(
            project_id=task.project_id,
            entity_type="task",
            entity_id=task_id,
            event_type=event_type,
            new_value=verdict,
            metadata=metadata,
        )

        return {"success": True, "message": f"Review submitted: {verdict}"}
    finally:
        conn.close()


def tc_get_context(
    db_path: Path,
    task_id: str,
    include: list[str] | None = None,
) -> dict[str, object]:
    """Get context about the project state."""
    conn, repo = _get_repo(db_path)
    try:
        task = repo.get_task(task_id)
        include_all = include is None
        context: dict[str, object] = {}

        if include_all or "completed_tasks" in (include or []):
            completed = repo.get_tasks_by_status(task.project_id, TaskStatus.COMPLETED)
            context["completed_tasks"] = [
                {"id": t.id, "name": t.name, "type": t.task_type.value}
                for t in completed
            ]

        if include_all or "current_phase" in (include or []):
            phases = repo.get_phases_by_project(task.project_id)
            for phase in phases:
                if phase.id == task.phase_id:
                    context["current_phase"] = {
                        "name": phase.name,
                        "sequence": phase.sequence,
                        "status": phase.status.value,
                    }
                    break

        if include_all or "review_findings" in (include or []):
            events = repo.get_events_by_entity("task", task_id)
            findings = []
            for event in events:
                if event.metadata and "findings" in event.metadata:
                    try:
                        meta = json.loads(event.metadata)
                        findings.extend(meta.get("findings", []))
                    except (json.JSONDecodeError, TypeError):
                        pass
            context["review_findings"] = findings

        return context
    finally:
        conn.close()


def tc_request_human_input(
    db_path: Path,
    task_id: str,
    question: str,
    options: list[str] | None = None,
    context: str | None = None,
) -> dict[str, object]:
    """Request human input via the TUI."""
    conn, repo = _get_repo(db_path)
    try:
        task = repo.get_task(task_id)

        metadata = json.dumps({
            "question": question,
            "options": options or [],
            "context": context,
        })

        repo.create_event(
            project_id=task.project_id,
            entity_type="task",
            entity_id=task_id,
            event_type=EventType.HUMAN_INPUT_REQUESTED,
            metadata=metadata,
        )

        return {
            "success": True,
            "message": "Human input requested. Check the TUI dashboard for response.",
        }
    finally:
        conn.close()

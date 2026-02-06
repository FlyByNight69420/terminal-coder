"""Tests for MCP tool handlers."""

from __future__ import annotations

import sqlite3
from collections.abc import Generator
from pathlib import Path

import pytest

from tc.core.enums import EventType, TaskStatus, TaskType
from tc.db.connection import create_connection
from tc.db.repository import Repository
from tc.db.schema import SCHEMA_DDL
from tc.mcp.tools import (
    ToolError,
    tc_get_context,
    tc_report_completion,
    tc_report_failure,
    tc_report_progress,
    tc_report_review,
    tc_request_human_input,
)


@pytest.fixture
def db_path(tmp_path: Path) -> Path:
    path = tmp_path / "test.db"
    conn = create_connection(path)
    conn.executescript(SCHEMA_DDL)
    conn.commit()

    # Create test data
    repo = Repository(conn)
    repo.create_project(
        id="proj-1", name="Test", project_dir="/tmp/test", prd_path="prd.md",
    )
    phase = repo.create_phase(id="p1", project_id="proj-1", sequence=1, name="Phase 1")
    repo.create_task(
        id="t1", phase_id="p1", project_id="proj-1",
        sequence=1, name="Coding Task", task_type=TaskType.CODING,
    )
    # Set task to running
    repo.update_task_status("t1", TaskStatus.QUEUED)
    repo.update_task_status("t1", TaskStatus.RUNNING)

    repo.create_task(
        id="r1", phase_id="p1", project_id="proj-1",
        sequence=2, name="Review Task", task_type=TaskType.REVIEW,
    )
    repo.update_task_status("r1", TaskStatus.QUEUED)
    repo.update_task_status("r1", TaskStatus.RUNNING)

    conn.close()
    return path


class TestReportProgress:
    def test_report_progress(self, db_path: Path) -> None:
        result = tc_report_progress(
            db_path, task_id="t1", status="implementing", message="Writing tests",
        )
        assert result["success"] is True

    def test_report_progress_with_percent(self, db_path: Path) -> None:
        result = tc_report_progress(
            db_path, task_id="t1", status="coding", message="Halfway done",
            percent_complete=50,
        )
        assert result["success"] is True

    def test_fails_for_non_running_task(self, db_path: Path) -> None:
        # Create a pending task
        conn = create_connection(db_path)
        repo = Repository(conn)
        repo.create_task(
            id="t-pending", phase_id="p1", project_id="proj-1",
            sequence=3, name="Pending", task_type=TaskType.CODING,
        )
        conn.close()

        with pytest.raises(ToolError, match="not running"):
            tc_report_progress(db_path, task_id="t-pending", status="x", message="y")


class TestReportCompletion:
    def test_report_completion(self, db_path: Path) -> None:
        result = tc_report_completion(
            db_path, task_id="t1", summary="Implemented all endpoints",
            files_changed=["src/api.py", "tests/test_api.py"],
        )
        assert result["success"] is True

        # Verify task status changed
        conn = create_connection(db_path)
        repo = Repository(conn)
        task = repo.get_task("t1")
        assert task.status == TaskStatus.COMPLETED
        conn.close()

    def test_report_completion_creates_event(self, db_path: Path) -> None:
        tc_report_completion(db_path, task_id="t1", summary="Done")

        conn = create_connection(db_path)
        repo = Repository(conn)
        events = repo.get_events_by_entity("task", "t1")
        completion_events = [e for e in events if e.new_value == "completed"]
        assert len(completion_events) == 1
        conn.close()


class TestReportFailure:
    def test_report_failure(self, db_path: Path) -> None:
        result = tc_report_failure(
            db_path, task_id="t1",
            error_type="build_error", error_message="Module not found",
        )
        assert result["success"] is True

        conn = create_connection(db_path)
        repo = Repository(conn)
        task = repo.get_task("t1")
        assert task.error_context == "Module not found"
        assert task.retry_count == 1
        conn.close()


class TestReportReview:
    def test_report_review_approved(self, db_path: Path) -> None:
        result = tc_report_review(
            db_path, task_id="r1", verdict="approved",
            findings=[], summary="Code looks good",
        )
        assert result["success"] is True

    def test_report_review_changes_requested(self, db_path: Path) -> None:
        result = tc_report_review(
            db_path, task_id="r1", verdict="changes_requested",
            findings=["Missing error handling", "Add input validation"],
            summary="Needs some fixes",
        )
        assert result["success"] is True

    def test_report_review_critical_creates_error_event(self, db_path: Path) -> None:
        tc_report_review(
            db_path, task_id="r1", verdict="critical_issues",
            findings=["SQL injection in login endpoint"],
            summary="Critical security issue",
        )

        conn = create_connection(db_path)
        repo = Repository(conn)
        events = repo.get_events_by_entity("task", "r1")
        error_events = [e for e in events if e.event_type == EventType.ERROR]
        assert len(error_events) == 1
        conn.close()

    def test_fails_for_non_review_task(self, db_path: Path) -> None:
        with pytest.raises(ToolError, match="not a review"):
            tc_report_review(
                db_path, task_id="t1", verdict="approved",
                findings=[], summary="",
            )


class TestGetContext:
    def test_get_full_context(self, db_path: Path) -> None:
        context = tc_get_context(db_path, task_id="t1")
        assert "completed_tasks" in context
        assert "current_phase" in context
        assert "review_findings" in context

    def test_get_specific_context(self, db_path: Path) -> None:
        context = tc_get_context(
            db_path, task_id="t1", include=["current_phase"],
        )
        assert "current_phase" in context


class TestRequestHumanInput:
    def test_request_human_input(self, db_path: Path) -> None:
        result = tc_request_human_input(
            db_path, task_id="t1",
            question="Which database should I use?",
            options=["PostgreSQL", "SQLite", "MySQL"],
        )
        assert result["success"] is True

        conn = create_connection(db_path)
        repo = Repository(conn)
        events = repo.get_events_by_entity("task", "t1")
        human_events = [
            e for e in events
            if e.event_type == EventType.HUMAN_INPUT_REQUESTED
        ]
        assert len(human_events) == 1
        conn.close()

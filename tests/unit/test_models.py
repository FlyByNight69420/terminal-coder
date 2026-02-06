"""Tests for frozen dataclass models."""

from __future__ import annotations

from datetime import datetime

import pytest

from tc.core.enums import (
    PhaseStatus,
    ProjectStatus,
    SessionStatus,
    SessionType,
    TaskStatus,
    TaskType,
)
from tc.core.models import (
    BootstrapCheck,
    Event,
    Phase,
    Project,
    Session,
    Task,
    TaskDependency,
)


class TestProjectModel:
    def test_create_project(self) -> None:
        now = datetime.now()
        p = Project(
            id="proj-1", name="Test", project_dir="/tmp/test", prd_path="prd.md",
            bootstrap_path=None, claude_md_path=None,
            status=ProjectStatus.INITIALIZED, created_at=now, updated_at=now,
        )
        assert p.id == "proj-1"
        assert p.status == ProjectStatus.INITIALIZED

    def test_project_is_frozen(self) -> None:
        now = datetime.now()
        p = Project(
            id="proj-1", name="Test", project_dir="/tmp/test", prd_path="prd.md",
            bootstrap_path=None, claude_md_path=None,
            status=ProjectStatus.INITIALIZED, created_at=now, updated_at=now,
        )
        with pytest.raises(AttributeError):
            p.name = "Changed"  # type: ignore[misc]


class TestPhaseModel:
    def test_create_phase(self) -> None:
        now = datetime.now()
        phase = Phase(
            id="phase-1", project_id="proj-1", sequence=1, name="Setup",
            description="Initial setup", status=PhaseStatus.PENDING,
            started_at=None, completed_at=None, created_at=now,
        )
        assert phase.sequence == 1
        assert phase.status == PhaseStatus.PENDING

    def test_phase_is_frozen(self) -> None:
        now = datetime.now()
        phase = Phase(
            id="phase-1", project_id="proj-1", sequence=1, name="Setup",
            description=None, status=PhaseStatus.PENDING,
            started_at=None, completed_at=None, created_at=now,
        )
        with pytest.raises(AttributeError):
            phase.status = PhaseStatus.IN_PROGRESS  # type: ignore[misc]


class TestTaskModel:
    def test_create_task(self) -> None:
        now = datetime.now()
        task = Task(
            id="task-1", phase_id="phase-1", project_id="proj-1", sequence=1,
            name="Build API", description="Build the REST API",
            task_type=TaskType.CODING, brief_path=None,
            status=TaskStatus.PENDING, retry_count=0, max_retries=1,
            error_context=None, started_at=None, completed_at=None, created_at=now,
        )
        assert task.task_type == TaskType.CODING
        assert task.retry_count == 0

    def test_task_is_frozen(self) -> None:
        now = datetime.now()
        task = Task(
            id="task-1", phase_id="phase-1", project_id="proj-1", sequence=1,
            name="Build API", description=None,
            task_type=TaskType.CODING, brief_path=None,
            status=TaskStatus.PENDING, retry_count=0, max_retries=1,
            error_context=None, started_at=None, completed_at=None, created_at=now,
        )
        with pytest.raises(AttributeError):
            task.retry_count = 5  # type: ignore[misc]


class TestTaskDependencyModel:
    def test_create_dependency(self) -> None:
        dep = TaskDependency(task_id="task-2", depends_on_id="task-1")
        assert dep.task_id == "task-2"
        assert dep.depends_on_id == "task-1"

    def test_dependency_is_frozen(self) -> None:
        dep = TaskDependency(task_id="task-2", depends_on_id="task-1")
        with pytest.raises(AttributeError):
            dep.task_id = "task-3"  # type: ignore[misc]


class TestSessionModel:
    def test_create_session(self) -> None:
        now = datetime.now()
        session = Session(
            id="sess-1", task_id="task-1", project_id="proj-1",
            session_type=SessionType.CODING, tmux_pane=None, pid=None,
            status=SessionStatus.PENDING, exit_code=None,
            started_at=None, completed_at=None, duration_secs=None,
            log_path=None, error_output=None, created_at=now,
        )
        assert session.session_type == SessionType.CODING

    def test_session_is_frozen(self) -> None:
        now = datetime.now()
        session = Session(
            id="sess-1", task_id="task-1", project_id="proj-1",
            session_type=SessionType.CODING, tmux_pane=None, pid=None,
            status=SessionStatus.PENDING, exit_code=None,
            started_at=None, completed_at=None, duration_secs=None,
            log_path=None, error_output=None, created_at=now,
        )
        with pytest.raises(AttributeError):
            session.pid = 1234  # type: ignore[misc]


class TestBootstrapCheckModel:
    def test_create_check(self) -> None:
        now = datetime.now()
        check = BootstrapCheck(
            id="check-1", project_id="proj-1", check_name="python",
            check_type="tool", command="python --version",
            expected="Python 3", actual_output="Python 3.11", passed=True, run_at=now,
        )
        assert check.passed is True
        assert check.check_type == "tool"

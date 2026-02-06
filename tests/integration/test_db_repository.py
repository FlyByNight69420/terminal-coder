"""Integration tests for the database repository with in-memory SQLite."""

from __future__ import annotations

import sqlite3
from collections.abc import Generator

import pytest

from tc.core.enums import (
    EventType,
    PhaseStatus,
    ProjectStatus,
    SessionStatus,
    SessionType,
    TaskStatus,
    TaskType,
)
from tc.db.connection import create_connection, initialize_db
from tc.db.repository import Repository


@pytest.fixture
def db_conn() -> Generator[sqlite3.Connection]:
    conn = create_connection(":memory:")
    initialize_db_in_memory(conn)
    yield conn
    conn.close()


def initialize_db_in_memory(conn: sqlite3.Connection) -> None:
    """Run schema on an existing in-memory connection."""
    from tc.db.schema import SCHEMA_DDL
    conn.executescript(SCHEMA_DDL)
    conn.commit()


@pytest.fixture
def repo(db_conn: sqlite3.Connection) -> Repository:
    return Repository(db_conn)


@pytest.fixture
def project_id(repo: Repository) -> str:
    project = repo.create_project(
        id="proj-1", name="Test Project", project_dir="/tmp/test", prd_path="prd.md",
        bootstrap_path="bootstrap.md",
    )
    return project.id


@pytest.fixture
def phase_id(repo: Repository, project_id: str) -> str:
    phase = repo.create_phase(
        id="phase-1", project_id=project_id, sequence=1, name="Phase 1",
        description="First phase",
    )
    return phase.id


class TestProjectCRUD:
    def test_create_and_get_project(self, repo: Repository) -> None:
        project = repo.create_project(
            id="proj-test", name="My Project", project_dir="/tmp/proj",
            prd_path="prd.md", bootstrap_path="bootstrap.md",
        )
        assert project.id == "proj-test"
        assert project.name == "My Project"
        assert project.status == ProjectStatus.INITIALIZED
        assert project.bootstrap_path == "bootstrap.md"

    def test_get_nonexistent_project_raises(self, repo: Repository) -> None:
        with pytest.raises(ValueError, match="Project not found"):
            repo.get_project("nonexistent")

    def test_update_project_status(self, repo: Repository, project_id: str) -> None:
        updated = repo.update_project_status(project_id, ProjectStatus.PLANNING)
        assert updated.status == ProjectStatus.PLANNING


class TestPhaseCRUD:
    def test_create_and_list_phases(self, repo: Repository, project_id: str) -> None:
        repo.create_phase(id="p1", project_id=project_id, sequence=1, name="Phase 1")
        repo.create_phase(id="p2", project_id=project_id, sequence=2, name="Phase 2")
        phases = repo.get_phases_by_project(project_id)
        assert len(phases) == 2
        assert phases[0].sequence == 1
        assert phases[1].sequence == 2

    def test_update_phase_status_to_in_progress(
        self, repo: Repository, project_id: str
    ) -> None:
        phase = repo.create_phase(
            id="p-prog", project_id=project_id, sequence=1, name="Phase 1"
        )
        repo.update_phase_status(phase.id, PhaseStatus.IN_PROGRESS)
        phases = repo.get_phases_by_project(project_id)
        assert phases[0].status == PhaseStatus.IN_PROGRESS
        assert phases[0].started_at is not None

    def test_update_phase_status_to_completed(
        self, repo: Repository, project_id: str
    ) -> None:
        phase = repo.create_phase(
            id="p-comp", project_id=project_id, sequence=1, name="Phase 1"
        )
        repo.update_phase_status(phase.id, PhaseStatus.IN_PROGRESS)
        repo.update_phase_status(phase.id, PhaseStatus.COMPLETED)
        phases = repo.get_phases_by_project(project_id)
        assert phases[0].status == PhaseStatus.COMPLETED
        assert phases[0].completed_at is not None


class TestTaskCRUD:
    def test_create_and_get_task(
        self, repo: Repository, project_id: str, phase_id: str
    ) -> None:
        task = repo.create_task(
            id="t1", phase_id=phase_id, project_id=project_id,
            sequence=1, name="Build API", task_type=TaskType.CODING,
            description="Build the REST API",
        )
        assert task.id == "t1"
        assert task.task_type == TaskType.CODING
        assert task.status == TaskStatus.PENDING
        assert task.retry_count == 0

    def test_get_tasks_by_phase(
        self, repo: Repository, project_id: str, phase_id: str
    ) -> None:
        repo.create_task(
            id="t1", phase_id=phase_id, project_id=project_id,
            sequence=1, name="Task 1", task_type=TaskType.CODING,
        )
        repo.create_task(
            id="t2", phase_id=phase_id, project_id=project_id,
            sequence=2, name="Task 2", task_type=TaskType.REVIEW,
        )
        tasks = repo.get_tasks_by_phase(phase_id)
        assert len(tasks) == 2
        assert tasks[0].name == "Task 1"
        assert tasks[1].name == "Task 2"

    def test_get_tasks_by_status(
        self, repo: Repository, project_id: str, phase_id: str
    ) -> None:
        repo.create_task(
            id="t1", phase_id=phase_id, project_id=project_id,
            sequence=1, name="Task 1", task_type=TaskType.CODING,
        )
        tasks = repo.get_tasks_by_status(project_id, TaskStatus.PENDING)
        assert len(tasks) == 1
        assert tasks[0].id == "t1"

    def test_update_task_status_to_running(
        self, repo: Repository, project_id: str, phase_id: str
    ) -> None:
        repo.create_task(
            id="t1", phase_id=phase_id, project_id=project_id,
            sequence=1, name="Task 1", task_type=TaskType.CODING,
        )
        task = repo.update_task_status("t1", TaskStatus.RUNNING)
        assert task.status == TaskStatus.RUNNING
        assert task.started_at is not None

    def test_update_task_status_to_completed(
        self, repo: Repository, project_id: str, phase_id: str
    ) -> None:
        repo.create_task(
            id="t1", phase_id=phase_id, project_id=project_id,
            sequence=1, name="Task 1", task_type=TaskType.CODING,
        )
        repo.update_task_status("t1", TaskStatus.RUNNING)
        task = repo.update_task_status("t1", TaskStatus.COMPLETED)
        assert task.status == TaskStatus.COMPLETED
        assert task.completed_at is not None

    def test_update_task_error(
        self, repo: Repository, project_id: str, phase_id: str
    ) -> None:
        repo.create_task(
            id="t1", phase_id=phase_id, project_id=project_id,
            sequence=1, name="Task 1", task_type=TaskType.CODING,
        )
        task = repo.update_task_error("t1", "Build failed: missing module")
        assert task.error_context == "Build failed: missing module"
        assert task.retry_count == 1

    def test_update_task_brief_path(
        self, repo: Repository, project_id: str, phase_id: str
    ) -> None:
        repo.create_task(
            id="t1", phase_id=phase_id, project_id=project_id,
            sequence=1, name="Task 1", task_type=TaskType.CODING,
        )
        task = repo.update_task_brief_path("t1", ".tc/briefs/p1-t1-brief.md")
        assert task.brief_path == ".tc/briefs/p1-t1-brief.md"


class TestTaskDependencies:
    def test_add_and_get_dependencies(
        self, repo: Repository, project_id: str, phase_id: str
    ) -> None:
        repo.create_task(
            id="t1", phase_id=phase_id, project_id=project_id,
            sequence=1, name="Task 1", task_type=TaskType.CODING,
        )
        repo.create_task(
            id="t2", phase_id=phase_id, project_id=project_id,
            sequence=2, name="Task 2", task_type=TaskType.CODING,
        )
        dep = repo.add_task_dependency("t2", "t1")
        assert dep.task_id == "t2"
        assert dep.depends_on_id == "t1"

        deps = repo.get_task_dependencies("t2")
        assert len(deps) == 1
        assert deps[0].depends_on_id == "t1"

    def test_pending_tasks_with_met_dependencies(
        self, repo: Repository, project_id: str, phase_id: str
    ) -> None:
        repo.create_task(
            id="t1", phase_id=phase_id, project_id=project_id,
            sequence=1, name="Task 1", task_type=TaskType.CODING,
        )
        repo.create_task(
            id="t2", phase_id=phase_id, project_id=project_id,
            sequence=2, name="Task 2", task_type=TaskType.CODING,
        )
        repo.add_task_dependency("t2", "t1")

        # t1 has no deps, should be schedulable. t2 depends on t1, not schedulable yet.
        schedulable = repo.get_pending_tasks_with_met_deps(project_id)
        assert len(schedulable) == 1
        assert schedulable[0].id == "t1"

        # Complete t1, now t2 should be schedulable.
        repo.update_task_status("t1", TaskStatus.RUNNING)
        repo.update_task_status("t1", TaskStatus.COMPLETED)
        schedulable = repo.get_pending_tasks_with_met_deps(project_id)
        assert len(schedulable) == 1
        assert schedulable[0].id == "t2"

    def test_no_pending_when_all_complete(
        self, repo: Repository, project_id: str, phase_id: str
    ) -> None:
        repo.create_task(
            id="t1", phase_id=phase_id, project_id=project_id,
            sequence=1, name="Task 1", task_type=TaskType.CODING,
        )
        repo.update_task_status("t1", TaskStatus.RUNNING)
        repo.update_task_status("t1", TaskStatus.COMPLETED)
        schedulable = repo.get_pending_tasks_with_met_deps(project_id)
        assert len(schedulable) == 0


class TestSessionCRUD:
    def test_create_and_get_session(
        self, repo: Repository, project_id: str, phase_id: str
    ) -> None:
        repo.create_task(
            id="t1", phase_id=phase_id, project_id=project_id,
            sequence=1, name="Task 1", task_type=TaskType.CODING,
        )
        session = repo.create_session(
            id="sess-1", task_id="t1", project_id=project_id,
            session_type=SessionType.CODING, log_path=".tc/logs/sess-1.log",
        )
        assert session.id == "sess-1"
        assert session.status == SessionStatus.PENDING

    def test_get_active_sessions(
        self, repo: Repository, project_id: str, phase_id: str
    ) -> None:
        repo.create_task(
            id="t1", phase_id=phase_id, project_id=project_id,
            sequence=1, name="Task 1", task_type=TaskType.CODING,
        )
        repo.create_session(
            id="sess-1", task_id="t1", project_id=project_id,
            session_type=SessionType.CODING,
        )
        active = repo.get_active_sessions(project_id)
        assert len(active) == 1

    def test_update_session_started(
        self, repo: Repository, project_id: str, phase_id: str
    ) -> None:
        repo.create_task(
            id="t1", phase_id=phase_id, project_id=project_id,
            sequence=1, name="Task 1", task_type=TaskType.CODING,
        )
        repo.create_session(
            id="sess-1", task_id="t1", project_id=project_id,
            session_type=SessionType.CODING,
        )
        repo.update_session_started("sess-1", pid=12345)
        sessions = repo.get_sessions_by_task("t1")
        assert sessions[0].pid == 12345
        assert sessions[0].status == SessionStatus.RUNNING


class TestEventCRUD:
    def test_create_and_get_events(self, repo: Repository, project_id: str) -> None:
        event = repo.create_event(
            project_id=project_id, entity_type="task", entity_id="t1",
            event_type=EventType.STATUS_CHANGED,
            old_value="pending", new_value="running",
        )
        assert event.event_type == EventType.STATUS_CHANGED
        assert event.old_value == "pending"

        events = repo.get_events_by_project(project_id)
        assert len(events) == 1

    def test_get_events_by_entity(self, repo: Repository, project_id: str) -> None:
        repo.create_event(
            project_id=project_id, entity_type="task", entity_id="t1",
            event_type=EventType.STATUS_CHANGED,
        )
        repo.create_event(
            project_id=project_id, entity_type="task", entity_id="t2",
            event_type=EventType.CREATED,
        )
        events = repo.get_events_by_entity("task", "t1")
        assert len(events) == 1
        assert events[0].entity_id == "t1"


class TestBootstrapCheckCRUD:
    def test_create_and_get_checks(self, repo: Repository, project_id: str) -> None:
        check = repo.create_bootstrap_check(
            id="check-1", project_id=project_id,
            check_name="python", check_type="tool",
            command="python --version", expected="Python 3",
            actual_output="Python 3.11.0", passed=True,
        )
        assert check.passed is True
        assert check.check_name == "python"

        checks = repo.get_bootstrap_checks_by_project(project_id)
        assert len(checks) == 1


class TestCascadingDeletes:
    def test_delete_project_cascades(self, db_conn: sqlite3.Connection) -> None:
        repo = Repository(db_conn)
        repo.create_project(
            id="proj-del", name="Delete Me", project_dir="/tmp/del", prd_path="prd.md",
        )
        phase = repo.create_phase(
            id="p-del", project_id="proj-del", sequence=1, name="Phase 1",
        )
        repo.create_task(
            id="t-del", phase_id=phase.id, project_id="proj-del",
            sequence=1, name="Task 1", task_type=TaskType.CODING,
        )
        repo.create_session(
            id="s-del", task_id="t-del", project_id="proj-del",
            session_type=SessionType.CODING,
        )
        repo.create_event(
            project_id="proj-del", entity_type="task", entity_id="t-del",
            event_type=EventType.CREATED,
        )

        # Delete the project
        db_conn.execute("DELETE FROM projects WHERE id = 'proj-del'")
        db_conn.commit()

        # Everything should be gone
        assert db_conn.execute("SELECT COUNT(*) as c FROM phases").fetchone()["c"] == 0
        assert db_conn.execute("SELECT COUNT(*) as c FROM tasks").fetchone()["c"] == 0
        assert db_conn.execute("SELECT COUNT(*) as c FROM sessions").fetchone()["c"] == 0
        assert db_conn.execute("SELECT COUNT(*) as c FROM events").fetchone()["c"] == 0

"""Tests for the task scheduler."""

from __future__ import annotations

import sqlite3
from collections.abc import Generator
from datetime import datetime

import pytest

from tc.core.enums import PhaseStatus, TaskStatus, TaskType
from tc.core.models import Task
from tc.core.scheduler import Scheduler
from tc.db.connection import create_connection
from tc.db.repository import Repository
from tc.db.schema import SCHEMA_DDL


@pytest.fixture
def db_conn() -> Generator[sqlite3.Connection]:
    conn = create_connection(":memory:")
    conn.executescript(SCHEMA_DDL)
    conn.commit()
    yield conn
    conn.close()


@pytest.fixture
def repo(db_conn: sqlite3.Connection) -> Repository:
    return Repository(db_conn)


@pytest.fixture
def project_id(repo: Repository) -> str:
    project = repo.create_project(
        id="proj-1", name="Test", project_dir="/tmp/test", prd_path="prd.md",
    )
    return project.id


@pytest.fixture
def scheduler(repo: Repository) -> Scheduler:
    return Scheduler(repo)


class TestNextCodingTask:
    def test_returns_first_pending_task(
        self, scheduler: Scheduler, repo: Repository, project_id: str
    ) -> None:
        phase = repo.create_phase(id="p1", project_id=project_id, sequence=1, name="Phase 1")
        repo.create_task(
            id="t1", phase_id=phase.id, project_id=project_id,
            sequence=1, name="Task 1", task_type=TaskType.CODING,
        )
        result = scheduler.next_coding_task(project_id)
        assert result is not None
        assert result.id == "t1"

    def test_skips_review_tasks(
        self, scheduler: Scheduler, repo: Repository, project_id: str
    ) -> None:
        phase = repo.create_phase(id="p1", project_id=project_id, sequence=1, name="Phase 1")
        repo.create_task(
            id="t1", phase_id=phase.id, project_id=project_id,
            sequence=1, name="Review", task_type=TaskType.REVIEW,
        )
        result = scheduler.next_coding_task(project_id)
        assert result is None

    def test_respects_dependencies(
        self, scheduler: Scheduler, repo: Repository, project_id: str
    ) -> None:
        phase = repo.create_phase(id="p1", project_id=project_id, sequence=1, name="Phase 1")
        repo.create_task(
            id="t1", phase_id=phase.id, project_id=project_id,
            sequence=1, name="Task 1", task_type=TaskType.CODING,
        )
        repo.create_task(
            id="t2", phase_id=phase.id, project_id=project_id,
            sequence=2, name="Task 2", task_type=TaskType.CODING,
        )
        repo.add_task_dependency("t2", "t1")

        result = scheduler.next_coding_task(project_id)
        assert result is not None
        assert result.id == "t1"

    def test_respects_phase_boundaries(
        self, scheduler: Scheduler, repo: Repository, project_id: str
    ) -> None:
        p1 = repo.create_phase(id="p1", project_id=project_id, sequence=1, name="Phase 1")
        p2 = repo.create_phase(id="p2", project_id=project_id, sequence=2, name="Phase 2")
        repo.create_task(
            id="t1", phase_id=p1.id, project_id=project_id,
            sequence=1, name="Task 1", task_type=TaskType.CODING,
        )
        repo.create_task(
            id="t2", phase_id=p2.id, project_id=project_id,
            sequence=1, name="Task 2", task_type=TaskType.CODING,
        )

        # Phase 1 is pending, so Phase 2 tasks should not be schedulable
        result = scheduler.next_coding_task(project_id)
        assert result is not None
        assert result.id == "t1"


class TestNextReviewTask:
    def test_returns_queued_review(
        self, scheduler: Scheduler, repo: Repository, project_id: str
    ) -> None:
        phase = repo.create_phase(id="p1", project_id=project_id, sequence=1, name="Phase 1")
        repo.create_task(
            id="r1", phase_id=phase.id, project_id=project_id,
            sequence=1, name="Review", task_type=TaskType.REVIEW,
            status=TaskStatus.QUEUED,
        )
        result = scheduler.next_review_task(project_id)
        assert result is not None
        assert result.id == "r1"

    def test_ignores_non_review_tasks(
        self, scheduler: Scheduler, repo: Repository, project_id: str
    ) -> None:
        phase = repo.create_phase(id="p1", project_id=project_id, sequence=1, name="Phase 1")
        repo.create_task(
            id="t1", phase_id=phase.id, project_id=project_id,
            sequence=1, name="Coding", task_type=TaskType.CODING,
            status=TaskStatus.QUEUED,
        )
        result = scheduler.next_review_task(project_id)
        assert result is None


class TestAllComplete:
    def test_all_complete(
        self, scheduler: Scheduler, repo: Repository, project_id: str
    ) -> None:
        phase = repo.create_phase(id="p1", project_id=project_id, sequence=1, name="Phase 1")
        repo.create_task(
            id="t1", phase_id=phase.id, project_id=project_id,
            sequence=1, name="Task 1", task_type=TaskType.CODING,
        )
        repo.update_task_status("t1", TaskStatus.RUNNING)
        repo.update_task_status("t1", TaskStatus.COMPLETED)
        assert scheduler.all_complete(project_id) is True

    def test_not_all_complete(
        self, scheduler: Scheduler, repo: Repository, project_id: str
    ) -> None:
        phase = repo.create_phase(id="p1", project_id=project_id, sequence=1, name="Phase 1")
        repo.create_task(
            id="t1", phase_id=phase.id, project_id=project_id,
            sequence=1, name="Task 1", task_type=TaskType.CODING,
        )
        assert scheduler.all_complete(project_id) is False


class TestSecurityRelevance:
    def test_detects_auth_keywords(self, scheduler: Scheduler) -> None:
        task = Task(
            id="t1", phase_id="p1", project_id="proj-1", sequence=1,
            name="Implement authentication", description="Add JWT login",
            task_type=TaskType.CODING, brief_path=None, status=TaskStatus.PENDING,
            retry_count=0, max_retries=1, error_context=None,
            started_at=None, completed_at=None, created_at=datetime.now(),
        )
        assert scheduler.is_security_relevant(task) is True

    def test_detects_api_key_keywords(self, scheduler: Scheduler) -> None:
        task = Task(
            id="t1", phase_id="p1", project_id="proj-1", sequence=1,
            name="Add API endpoint", description="Store api_key in config",
            task_type=TaskType.CODING, brief_path=None, status=TaskStatus.PENDING,
            retry_count=0, max_retries=1, error_context=None,
            started_at=None, completed_at=None, created_at=datetime.now(),
        )
        assert scheduler.is_security_relevant(task) is True

    def test_non_security_task(self, scheduler: Scheduler) -> None:
        task = Task(
            id="t1", phase_id="p1", project_id="proj-1", sequence=1,
            name="Add readme", description="Write documentation",
            task_type=TaskType.CODING, brief_path=None, status=TaskStatus.PENDING,
            retry_count=0, max_retries=1, error_context=None,
            started_at=None, completed_at=None, created_at=datetime.now(),
        )
        assert scheduler.is_security_relevant(task) is False

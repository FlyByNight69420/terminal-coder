"""Integration test for the full orchestration flow with mock Claude and TMUX."""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Generator
from pathlib import Path

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
from tc.core.events import EventBus
from tc.core.retry_policy import RetryPolicy
from tc.core.scheduler import Scheduler
from tc.db.connection import create_connection
from tc.db.repository import Repository
from tc.db.schema import SCHEMA_DDL
from tc.orchestrator.review_coordinator import ReviewCoordinator
from tc.templates.renderer import BriefRenderer


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


def _setup_project(repo: Repository) -> str:
    """Create a project with phases and tasks."""
    project = repo.create_project(
        id="proj-flow", name="Flow Test", project_dir="/tmp/flow", prd_path="prd.md",
    )
    # Phase 1: Setup
    p1 = repo.create_phase(
        id="p1", project_id=project.id, sequence=1, name="Setup",
    )
    repo.create_task(
        id="t1", phase_id=p1.id, project_id=project.id,
        sequence=1, name="Init project", task_type=TaskType.CODING,
    )

    # Phase 2: Features (depends on Phase 1)
    p2 = repo.create_phase(
        id="p2", project_id=project.id, sequence=2, name="Features",
    )
    repo.create_task(
        id="t2", phase_id=p2.id, project_id=project.id,
        sequence=1, name="Build auth", task_type=TaskType.CODING,
        description="Implement authentication with JWT tokens",
    )
    repo.create_task(
        id="t3", phase_id=p2.id, project_id=project.id,
        sequence=2, name="Build API", task_type=TaskType.CODING,
    )
    repo.add_task_dependency("t3", "t2")

    return project.id


class TestSchedulerFlow:
    def test_task_ordering_respects_phases(self, repo: Repository) -> None:
        project_id = _setup_project(repo)
        scheduler = Scheduler(repo)

        # Only Phase 1 tasks should be schedulable
        task = scheduler.next_coding_task(project_id)
        assert task is not None
        assert task.id == "t1"

        # Complete t1 and mark phase 1 complete
        repo.update_task_status("t1", TaskStatus.QUEUED)
        repo.update_task_status("t1", TaskStatus.RUNNING)
        repo.update_task_status("t1", TaskStatus.COMPLETED)
        repo.update_phase_status("p1", PhaseStatus.IN_PROGRESS)
        repo.update_phase_status("p1", PhaseStatus.COMPLETED)

        # Now Phase 2 tasks should be schedulable, t2 first (t3 depends on t2)
        task = scheduler.next_coding_task(project_id)
        assert task is not None
        assert task.id == "t2"

    def test_dependency_chain(self, repo: Repository) -> None:
        project_id = _setup_project(repo)
        scheduler = Scheduler(repo)

        # Complete phase 1
        repo.update_task_status("t1", TaskStatus.QUEUED)
        repo.update_task_status("t1", TaskStatus.RUNNING)
        repo.update_task_status("t1", TaskStatus.COMPLETED)
        repo.update_phase_status("p1", PhaseStatus.IN_PROGRESS)
        repo.update_phase_status("p1", PhaseStatus.COMPLETED)

        # t2 is schedulable, t3 is not (depends on t2)
        task = scheduler.next_coding_task(project_id)
        assert task is not None
        assert task.id == "t2"

        # Complete t2
        repo.update_task_status("t2", TaskStatus.QUEUED)
        repo.update_task_status("t2", TaskStatus.RUNNING)
        repo.update_task_status("t2", TaskStatus.COMPLETED)

        # Now t3 should be schedulable
        task = scheduler.next_coding_task(project_id)
        assert task is not None
        assert task.id == "t3"


class TestReviewScheduling:
    def test_review_auto_scheduled_after_coding(self, repo: Repository) -> None:
        project_id = _setup_project(repo)
        renderer = BriefRenderer()
        coordinator = ReviewCoordinator(repo, renderer)

        # Complete a coding task
        repo.update_task_status("t1", TaskStatus.QUEUED)
        repo.update_task_status("t1", TaskStatus.RUNNING)
        repo.update_task_status("t1", TaskStatus.COMPLETED)
        task = repo.get_task("t1")

        # Schedule review
        review = coordinator.schedule_review(task, ["src/init.py"])
        assert review.task_type == TaskType.REVIEW
        assert review.status == TaskStatus.QUEUED
        assert "Review:" in review.name

        # Review should be in scheduler
        scheduler = Scheduler(repo)
        review_task = scheduler.next_review_task(project_id)
        assert review_task is not None
        assert review_task.id == review.id

    def test_security_review_for_auth_tasks(self, repo: Repository) -> None:
        project_id = _setup_project(repo)
        renderer = BriefRenderer()
        coordinator = ReviewCoordinator(repo, renderer)
        scheduler = Scheduler(repo)

        # Complete phase 1
        repo.update_task_status("t1", TaskStatus.QUEUED)
        repo.update_task_status("t1", TaskStatus.RUNNING)
        repo.update_task_status("t1", TaskStatus.COMPLETED)
        repo.update_phase_status("p1", PhaseStatus.IN_PROGRESS)
        repo.update_phase_status("p1", PhaseStatus.COMPLETED)

        # Complete auth task
        repo.update_task_status("t2", TaskStatus.QUEUED)
        repo.update_task_status("t2", TaskStatus.RUNNING)
        repo.update_task_status("t2", TaskStatus.COMPLETED)
        task = repo.get_task("t2")

        # Check security relevance
        assert scheduler.is_security_relevant(task) is True

        # Schedule security review
        sec_review = coordinator.schedule_security_review(
            task, ["src/auth.py"], "authentication code"
        )
        assert sec_review.task_type == TaskType.SECURITY_REVIEW


class TestRetryFlow:
    def test_retry_policy_integration(self, repo: Repository) -> None:
        project_id = _setup_project(repo)
        policy = RetryPolicy(max_retries=1)

        # Start and fail a task
        repo.update_task_status("t1", TaskStatus.QUEUED)
        repo.update_task_status("t1", TaskStatus.RUNNING)
        repo.update_task_status("t1", TaskStatus.FAILED)
        repo.update_task_error("t1", "Build failed: missing module")

        task = repo.get_task("t1")
        assert policy.should_retry(task) is False  # retry_count is now 1 (from update_task_error)

    def test_retry_count_increments(self, repo: Repository) -> None:
        project_id = _setup_project(repo)

        repo.update_task_status("t1", TaskStatus.QUEUED)
        repo.update_task_status("t1", TaskStatus.RUNNING)
        repo.update_task_status("t1", TaskStatus.FAILED)
        repo.update_task_error("t1", "Error 1")

        task = repo.get_task("t1")
        assert task.retry_count == 1
        assert task.error_context == "Error 1"


class TestEventFlow:
    def test_events_recorded_for_lifecycle(self, repo: Repository) -> None:
        project_id = _setup_project(repo)
        event_bus = EventBus()

        # Create events for task lifecycle
        repo.create_event(
            project_id=project_id, entity_type="task", entity_id="t1",
            event_type=EventType.STATUS_CHANGED, old_value="pending", new_value="running",
        )
        repo.create_event(
            project_id=project_id, entity_type="task", entity_id="t1",
            event_type=EventType.STATUS_CHANGED, old_value="running", new_value="completed",
        )

        events = repo.get_events_by_project(project_id)
        assert len(events) == 2


class TestCompletionDetection:
    def test_all_complete_after_all_tasks_done(self, repo: Repository) -> None:
        project_id = _setup_project(repo)
        scheduler = Scheduler(repo)

        assert scheduler.all_complete(project_id) is False

        # Complete all tasks
        for task_id in ["t1", "t2", "t3"]:
            repo.update_task_status(task_id, TaskStatus.QUEUED)
            repo.update_task_status(task_id, TaskStatus.RUNNING)
            repo.update_task_status(task_id, TaskStatus.COMPLETED)

        assert scheduler.all_complete(project_id) is True

    def test_skipped_counts_as_complete(self, repo: Repository) -> None:
        project_id = _setup_project(repo)
        scheduler = Scheduler(repo)

        repo.update_task_status("t1", TaskStatus.QUEUED)
        repo.update_task_status("t1", TaskStatus.RUNNING)
        repo.update_task_status("t1", TaskStatus.COMPLETED)

        repo.update_task_status("t2", TaskStatus.SKIPPED)

        repo.update_task_status("t3", TaskStatus.QUEUED)
        repo.update_task_status("t3", TaskStatus.RUNNING)
        repo.update_task_status("t3", TaskStatus.COMPLETED)

        assert scheduler.all_complete(project_id) is True

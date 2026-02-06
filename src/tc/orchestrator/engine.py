"""Main orchestration engine - the core loop that drives everything."""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path

from tc.config.constants import POLL_INTERVAL_SECS
from tc.core.enums import (
    EventType,
    PhaseStatus,
    ProjectStatus,
    SessionStatus,
    TaskStatus,
    TaskType,
)
from tc.core.events import EngineEvent, EventBus
from tc.core.retry_policy import RetryPolicy
from tc.core.scheduler import Scheduler
from tc.db.repository import Repository
from tc.orchestrator.review_coordinator import ReviewCoordinator
from tc.orchestrator.session_manager import SessionManager
from tc.templates.renderer import BriefRenderer

logger = logging.getLogger(__name__)


class OrchestrationEngine:
    """The main orchestration loop that drives task execution."""

    def __init__(
        self,
        repository: Repository,
        session_manager: SessionManager,
        scheduler: Scheduler,
        review_coordinator: ReviewCoordinator,
        event_bus: EventBus,
        project_id: str,
        project_dir: Path,
    ) -> None:
        self._repo = repository
        self._sessions = session_manager
        self._scheduler = scheduler
        self._reviews = review_coordinator
        self._events = event_bus
        self._project_id = project_id
        self._project_dir = project_dir
        self._renderer = BriefRenderer()
        self._retry_policy = RetryPolicy()
        self._paused = False
        self._stopped = False

    async def run(self) -> None:
        """Main orchestration loop."""
        self._repo.update_project_status(self._project_id, ProjectStatus.RUNNING)
        self._publish(EventType.STATUS_CHANGED, "project", self._project_id, "Engine started")

        try:
            while not self._stopped:
                await self._tick()
                await asyncio.sleep(POLL_INTERVAL_SECS)
        except Exception as e:
            logger.exception("Engine error")
            self._repo.update_project_status(self._project_id, ProjectStatus.FAILED)
            self._publish(EventType.ERROR, "project", self._project_id, f"Engine error: {e}")
            raise

    async def _tick(self) -> None:
        """Single iteration of the orchestration loop."""
        # 1. Check active sessions for exit
        self._check_sessions()

        # 2. Check for completion
        if self._scheduler.all_complete(self._project_id):
            self._repo.update_project_status(self._project_id, ProjectStatus.COMPLETED)
            self._publish(
                EventType.STATUS_CHANGED, "project", self._project_id,
                "All tasks completed",
            )
            self._stopped = True
            return

        # 3. If paused, don't schedule new work
        if self._paused:
            return

        # 4. Dispatch review if review pane is free
        if not self._sessions.has_active_review():
            review_task = self._scheduler.next_review_task(self._project_id)
            if review_task is not None:
                self._dispatch_task(review_task)

        # 5. Dispatch coding task if coding pane is free
        if not self._sessions.has_active_coding():
            coding_task = self._scheduler.next_coding_task(self._project_id)
            if coding_task is not None:
                self._start_phase_if_needed(coding_task)
                self._dispatch_task(coding_task)

        # 6. Check for deadlock
        if (
            not self._sessions.get_active_sessions()
            and not self._scheduler.has_schedulable(self._project_id)
            and not self._scheduler.all_complete(self._project_id)
        ):
            # Check if anything is running or retrying
            running = self._repo.get_tasks_by_status(self._project_id, TaskStatus.RUNNING)
            retrying = self._repo.get_tasks_by_status(self._project_id, TaskStatus.RETRYING)
            if not running and not retrying:
                self._publish(
                    EventType.PAUSED, "project", self._project_id,
                    "Deadlock detected: no schedulable tasks and not all complete",
                )
                self._paused = True

    def _check_sessions(self) -> None:
        """Check active sessions and handle completions/failures."""
        for session, result in self._sessions.check_active():
            if not result.exited:
                continue

            task = self._repo.get_task(session.task_id)

            if result.exit_code == 0:
                self._handle_completion(task, session)
            else:
                self._handle_failure(task, session, result.stderr)

    def _handle_completion(self, task: object, session: object) -> None:
        """Handle a successfully completed session."""
        from tc.core.models import Session, Task
        task_obj: Task = task  # type: ignore[assignment]
        session_obj: Session = session  # type: ignore[assignment]

        self._repo.update_session_completed(session_obj.id, SessionStatus.COMPLETED, 0)
        self._repo.update_task_status(task_obj.id, TaskStatus.COMPLETED)

        self._publish(
            EventType.STATUS_CHANGED, "task", task_obj.id,
            f"Task completed: {task_obj.name}",
        )

        # Check if phase is complete
        self._check_phase_completion(task_obj)

        # Schedule review for coding tasks
        if task_obj.task_type == TaskType.CODING:
            files = self._reviews.get_files_changed(task_obj)
            self._reviews.schedule_review(task_obj, files)

            # Also schedule security review if relevant
            if self._scheduler.is_security_relevant(task_obj):
                self._reviews.schedule_security_review(
                    task_obj, files, "security-relevant code detected"
                )

    def _handle_failure(self, task: object, session: object, error: str) -> None:
        """Handle a failed session."""
        from tc.core.models import Session, Task
        task_obj: Task = task  # type: ignore[assignment]
        session_obj: Session = session  # type: ignore[assignment]

        self._repo.update_session_completed(session_obj.id, SessionStatus.FAILED, 1)
        self._repo.update_task_status(task_obj.id, TaskStatus.FAILED)
        self._repo.update_task_error(task_obj.id, error[:2000])

        self._publish(
            EventType.ERROR, "task", task_obj.id,
            f"Task failed: {task_obj.name}",
        )

        # Retry if eligible
        refreshed_task = self._repo.get_task(task_obj.id)
        if self._retry_policy.should_retry(refreshed_task):
            self._repo.update_task_status(task_obj.id, TaskStatus.RETRYING)
            self._repo.update_task_status(task_obj.id, TaskStatus.RUNNING)

            self._publish(
                EventType.RETRIED, "task", task_obj.id,
                f"Retrying task: {task_obj.name} (attempt {refreshed_task.retry_count + 1})",
            )

            # Re-dispatch with error context
            retry_context = self._retry_policy.prepare_retry_context(refreshed_task, error)
            # The retry will be picked up in the next tick via the scheduler
        else:
            self._repo.update_task_status(task_obj.id, TaskStatus.PAUSED)
            self._publish(
                EventType.PAUSED, "task", task_obj.id,
                f"Task paused after max retries: {task_obj.name}",
            )

    def _dispatch_task(self, task: object) -> None:
        """Dispatch a task to a TMUX pane."""
        from tc.core.models import Task
        task_obj: Task = task  # type: ignore[assignment]

        # Update status
        if task_obj.status == TaskStatus.PENDING:
            self._repo.update_task_status(task_obj.id, TaskStatus.QUEUED)
        self._repo.update_task_status(task_obj.id, TaskStatus.RUNNING)

        # Get or generate brief
        brief_path = task_obj.brief_path
        if brief_path is None:
            brief_path = str(
                self._project_dir / ".tc" / "briefs" / f"{task_obj.id}-brief.md"
            )

        brief_file = Path(brief_path)
        if not brief_file.exists():
            # Generate a minimal brief
            brief_content = f"# Task: {task_obj.name}\n\n{task_obj.description or ''}\n"
            brief_file.parent.mkdir(parents=True, exist_ok=True)
            brief_file.write_text(brief_content)

        self._sessions.spawn(
            self._repo.get_task(task_obj.id),
            brief_file,
        )

        self._publish(
            EventType.STATUS_CHANGED, "task", task_obj.id,
            f"Task dispatched: {task_obj.name}",
        )

    def _check_phase_completion(self, task: object) -> None:
        """Check if completing this task completes its phase."""
        from tc.core.models import Task
        task_obj: Task = task  # type: ignore[assignment]

        phase_tasks = self._repo.get_tasks_by_phase(task_obj.phase_id)
        all_done = all(
            t.status in (TaskStatus.COMPLETED, TaskStatus.SKIPPED)
            for t in phase_tasks
        )

        if all_done:
            self._repo.update_phase_status(task_obj.phase_id, PhaseStatus.COMPLETED)
            self._publish(
                EventType.STATUS_CHANGED, "phase", task_obj.phase_id,
                "Phase completed",
            )

    def _start_phase_if_needed(self, task: object) -> None:
        """Start the phase if it's still pending."""
        from tc.core.models import Task
        task_obj: Task = task  # type: ignore[assignment]

        phases = self._repo.get_phases_by_project(task_obj.project_id)
        for phase in phases:
            if phase.id == task_obj.phase_id and phase.status == PhaseStatus.PENDING:
                self._repo.update_phase_status(phase.id, PhaseStatus.IN_PROGRESS)
                self._publish(
                    EventType.STATUS_CHANGED, "phase", phase.id,
                    f"Phase started: {phase.name}",
                )
                break

    def pause(self) -> None:
        """Pause the engine (stop scheduling new tasks)."""
        self._paused = True
        self._publish(EventType.PAUSED, "project", self._project_id, "Engine paused")

    def resume(self) -> None:
        """Resume the engine."""
        self._paused = False
        self._publish(EventType.RESUMED, "project", self._project_id, "Engine resumed")

    def stop(self) -> None:
        """Stop the engine gracefully."""
        self._stopped = True
        self._publish(
            EventType.STATUS_CHANGED, "project", self._project_id, "Engine stopped"
        )

    @property
    def is_paused(self) -> bool:
        return self._paused

    @property
    def is_stopped(self) -> bool:
        return self._stopped

    def _publish(
        self, event_type: EventType, entity_type: str, entity_id: str, message: str
    ) -> None:
        """Publish an event."""
        self._events.publish(EngineEvent(
            event_type=event_type,
            entity_type=entity_type,
            entity_id=entity_id,
            message=message,
        ))

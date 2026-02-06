"""Coordinates automatic code review scheduling."""

from __future__ import annotations

import uuid

from tc.core.enums import EventType, TaskStatus, TaskType
from tc.core.models import Task
from tc.db.repository import Repository
from tc.templates.renderer import BriefRenderer


class ReviewCoordinator:
    """Schedules review tasks after coding tasks complete."""

    def __init__(self, repository: Repository, renderer: BriefRenderer) -> None:
        self._repo = repository
        self._renderer = renderer

    def schedule_review(self, completed_task: Task, files_changed: list[str]) -> Task:
        """Create a review task for a completed coding task."""
        review_id = str(uuid.uuid4())
        review_name = f"Review: {completed_task.name}"

        # Determine sequence - place review right after the coding task
        phase_tasks = self._repo.get_tasks_by_phase(completed_task.phase_id)
        max_seq = max((t.sequence for t in phase_tasks), default=0)

        review_task = self._repo.create_task(
            id=review_id,
            phase_id=completed_task.phase_id,
            project_id=completed_task.project_id,
            sequence=max_seq + 1,
            name=review_name,
            task_type=TaskType.REVIEW,
            description=f"Code review for: {completed_task.name}",
        )

        # Set dependency on the completed task
        self._repo.add_task_dependency(review_id, completed_task.id)

        # Mark as queued (dependency is already met since source task is completed)
        self._repo.update_task_status(review_id, TaskStatus.QUEUED)

        # Log event
        self._repo.create_event(
            project_id=completed_task.project_id,
            entity_type="task",
            entity_id=review_id,
            event_type=EventType.REVIEW_SCHEDULED,
            new_value=f"Review scheduled for {completed_task.name}",
        )

        return self._repo.get_task(review_id)

    def schedule_security_review(
        self, completed_task: Task, files_changed: list[str], security_concern: str,
    ) -> Task:
        """Create a security review task for a security-relevant task."""
        review_id = str(uuid.uuid4())
        review_name = f"Security Review: {completed_task.name}"

        phase_tasks = self._repo.get_tasks_by_phase(completed_task.phase_id)
        max_seq = max((t.sequence for t in phase_tasks), default=0)

        review_task = self._repo.create_task(
            id=review_id,
            phase_id=completed_task.phase_id,
            project_id=completed_task.project_id,
            sequence=max_seq + 1,
            name=review_name,
            task_type=TaskType.SECURITY_REVIEW,
            description=f"Security review for: {completed_task.name} (concern: {security_concern})",
        )

        self._repo.add_task_dependency(review_id, completed_task.id)
        self._repo.update_task_status(review_id, TaskStatus.QUEUED)

        self._repo.create_event(
            project_id=completed_task.project_id,
            entity_type="task",
            entity_id=review_id,
            event_type=EventType.REVIEW_SCHEDULED,
            new_value=f"Security review scheduled for {completed_task.name}",
        )

        return self._repo.get_task(review_id)

    def get_files_changed(self, task: Task) -> list[str]:
        """Extract files changed from task completion events."""
        events = self._repo.get_events_by_entity("task", task.id)
        for event in events:
            if event.metadata and "files_changed" in event.metadata:
                import json
                try:
                    meta = json.loads(event.metadata)
                    return list(meta.get("files_changed", []))
                except (json.JSONDecodeError, TypeError):
                    pass
        return []

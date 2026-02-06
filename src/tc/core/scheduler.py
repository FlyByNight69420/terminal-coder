"""Task scheduler for the orchestration engine."""

from __future__ import annotations

import re

from tc.core.enums import PhaseStatus, TaskStatus, TaskType
from tc.core.models import Task
from tc.db.repository import Repository

_SECURITY_KEYWORDS = re.compile(
    r"auth|login|password|credential|secret|token|jwt|oauth|session|permission|"
    r"api[_\s-]?key|encrypt|decrypt|certificate|ssl|tls|csrf|xss|injection|"
    r"security|vulnerable|sanitiz",
    re.IGNORECASE,
)


class Scheduler:
    """Determines which tasks are eligible to run next."""

    def __init__(self, repository: Repository) -> None:
        self._repo = repository

    def next_coding_task(self, project_id: str) -> Task | None:
        """Find the next eligible coding/deployment/verification task."""
        eligible = self._repo.get_pending_tasks_with_met_deps(project_id)

        # Filter to coding-type tasks and check phase readiness
        for task in eligible:
            if task.task_type in (
                TaskType.CODING, TaskType.DEPLOYMENT, TaskType.VERIFICATION, TaskType.PLANNING,
            ):
                if self._phase_ready(task):
                    return task
        return None

    def next_review_task(self, project_id: str) -> Task | None:
        """Find the next queued review task."""
        queued = self._repo.get_tasks_by_status(project_id, TaskStatus.QUEUED)
        for task in queued:
            if task.task_type in (TaskType.REVIEW, TaskType.SECURITY_REVIEW):
                return task
        return None

    def has_schedulable(self, project_id: str) -> bool:
        """Check if any tasks can be scheduled."""
        eligible = self._repo.get_pending_tasks_with_met_deps(project_id)
        if eligible:
            return True
        queued = self._repo.get_tasks_by_status(project_id, TaskStatus.QUEUED)
        return len(queued) > 0

    def all_complete(self, project_id: str) -> bool:
        """Check if all tasks in the project are completed or skipped."""
        tasks = self._repo.get_tasks_by_project(project_id)
        return all(
            t.status in (TaskStatus.COMPLETED, TaskStatus.SKIPPED)
            for t in tasks
        )

    def dependencies_met(self, task_id: str) -> bool:
        """Check if all dependencies of a task are completed."""
        deps = self._repo.get_task_dependencies(task_id)
        for dep in deps:
            dep_task = self._repo.get_task(dep.depends_on_id)
            if dep_task.status != TaskStatus.COMPLETED:
                return False
        return True

    def is_security_relevant(self, task: Task) -> bool:
        """Detect if a task involves security-sensitive code."""
        text = f"{task.name} {task.description or ''}"
        return bool(_SECURITY_KEYWORDS.search(text))

    def _phase_ready(self, task: Task) -> bool:
        """Check that the task's phase is ready (previous phases completed)."""
        phases = self._repo.get_phases_by_project(task.project_id)

        # Find this task's phase
        task_phase = None
        for phase in phases:
            if phase.id == task.phase_id:
                task_phase = phase
                break

        if task_phase is None:
            return False

        # All prior phases must be completed
        for phase in phases:
            if phase.sequence < task_phase.sequence:
                if phase.status not in (PhaseStatus.COMPLETED, PhaseStatus.SKIPPED):
                    return False

        return True

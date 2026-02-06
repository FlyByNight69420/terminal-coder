"""Phase tree widget showing phases and tasks with status indicators."""

from __future__ import annotations

from textual.widgets import Tree

from tc.core.enums import PhaseStatus, TaskStatus
from tc.core.models import Phase, Task


_PHASE_ICONS: dict[str, str] = {
    PhaseStatus.COMPLETED: "[OK]",
    PhaseStatus.IN_PROGRESS: "[>>]",
    PhaseStatus.FAILED: "[!!]",
    PhaseStatus.PENDING: "[--]",
    PhaseStatus.SKIPPED: "[~~]",
}

_TASK_ICONS: dict[str, str] = {
    TaskStatus.COMPLETED: "[x]",
    TaskStatus.RUNNING: "[>]",
    TaskStatus.FAILED: "[!]",
    TaskStatus.PENDING: "[ ]",
    TaskStatus.QUEUED: "[ ]",
    TaskStatus.RETRYING: "[~]",
    TaskStatus.PAUSED: "[!]",
    TaskStatus.SKIPPED: "[-]",
}


class PhaseTree(Tree[str]):
    """Tree widget showing phases and their tasks."""

    def __init__(self, **kwargs: object) -> None:
        super().__init__("Phases", id="phase-tree", **kwargs)  # type: ignore[arg-type]

    def refresh_data(
        self,
        phases: list[Phase],
        tasks_by_phase: dict[str, list[Task]],
    ) -> None:
        """Rebuild the tree with current data."""
        self.clear()

        for phase in phases:
            icon = _PHASE_ICONS.get(phase.status, "[--]")
            style = _phase_style(phase.status)
            label = f"{icon} [{style}]{phase.name}[/{style}]"
            node = self.root.add(label, expand=phase.status == PhaseStatus.IN_PROGRESS)

            phase_tasks = tasks_by_phase.get(phase.id, [])
            for task in phase_tasks:
                task_icon = _TASK_ICONS.get(task.status, "[ ]")
                task_style = _task_style(task.status)
                task_label = f"{task_icon} [{task_style}]{task.name}[/{task_style}]"
                node.add_leaf(task_label)

        self.root.expand()


def _phase_style(status: PhaseStatus) -> str:
    styles = {
        PhaseStatus.COMPLETED: "green",
        PhaseStatus.IN_PROGRESS: "yellow bold",
        PhaseStatus.FAILED: "red",
        PhaseStatus.PENDING: "dim",
        PhaseStatus.SKIPPED: "dim",
    }
    return styles.get(status, "white")


def _task_style(status: TaskStatus) -> str:
    styles = {
        TaskStatus.COMPLETED: "green",
        TaskStatus.RUNNING: "yellow bold",
        TaskStatus.FAILED: "red",
        TaskStatus.PENDING: "dim",
        TaskStatus.QUEUED: "dim",
        TaskStatus.RETRYING: "yellow",
        TaskStatus.PAUSED: "red",
        TaskStatus.SKIPPED: "dim",
    }
    return styles.get(status, "white")

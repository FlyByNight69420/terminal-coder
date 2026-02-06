"""State machine for task, phase, and session status transitions."""

from __future__ import annotations

from tc.core.enums import PhaseStatus, SessionStatus, TaskStatus

VALID_TASK_TRANSITIONS: dict[TaskStatus, frozenset[TaskStatus]] = {
    TaskStatus.PENDING: frozenset({TaskStatus.QUEUED, TaskStatus.SKIPPED}),
    TaskStatus.QUEUED: frozenset({TaskStatus.RUNNING, TaskStatus.SKIPPED}),
    TaskStatus.RUNNING: frozenset({TaskStatus.COMPLETED, TaskStatus.FAILED}),
    TaskStatus.FAILED: frozenset({TaskStatus.RETRYING, TaskStatus.PAUSED, TaskStatus.SKIPPED}),
    TaskStatus.RETRYING: frozenset({TaskStatus.RUNNING}),
    TaskStatus.PAUSED: frozenset({TaskStatus.QUEUED, TaskStatus.SKIPPED}),
    TaskStatus.COMPLETED: frozenset(),
    TaskStatus.SKIPPED: frozenset(),
}

VALID_PHASE_TRANSITIONS: dict[PhaseStatus, frozenset[PhaseStatus]] = {
    PhaseStatus.PENDING: frozenset({PhaseStatus.IN_PROGRESS, PhaseStatus.SKIPPED}),
    PhaseStatus.IN_PROGRESS: frozenset({
        PhaseStatus.COMPLETED,
        PhaseStatus.FAILED,
        PhaseStatus.SKIPPED,
    }),
    PhaseStatus.COMPLETED: frozenset(),
    PhaseStatus.FAILED: frozenset({PhaseStatus.IN_PROGRESS}),
    PhaseStatus.SKIPPED: frozenset(),
}

VALID_SESSION_TRANSITIONS: dict[SessionStatus, frozenset[SessionStatus]] = {
    SessionStatus.PENDING: frozenset({SessionStatus.STARTING, SessionStatus.FAILED}),
    SessionStatus.STARTING: frozenset({SessionStatus.RUNNING, SessionStatus.FAILED}),
    SessionStatus.RUNNING: frozenset({
        SessionStatus.COMPLETED,
        SessionStatus.FAILED,
        SessionStatus.KILLED,
        SessionStatus.TIMED_OUT,
    }),
    SessionStatus.COMPLETED: frozenset(),
    SessionStatus.FAILED: frozenset(),
    SessionStatus.KILLED: frozenset(),
    SessionStatus.TIMED_OUT: frozenset(),
}


class InvalidTransitionError(Exception):
    """Raised when an invalid state transition is attempted."""

    def __init__(self, entity_type: str, current: str, target: str) -> None:
        self.entity_type = entity_type
        self.current = current
        self.target = target
        super().__init__(
            f"Invalid {entity_type} transition: {current} -> {target}"
        )


def validate_transition(
    current: TaskStatus | PhaseStatus | SessionStatus,
    target: TaskStatus | PhaseStatus | SessionStatus,
    entity_type: str,
) -> bool:
    """Validate a state transition. Returns True if valid, raises InvalidTransitionError if not."""
    if isinstance(current, TaskStatus) and isinstance(target, TaskStatus):
        transitions = VALID_TASK_TRANSITIONS
    elif isinstance(current, PhaseStatus) and isinstance(target, PhaseStatus):
        transitions = VALID_PHASE_TRANSITIONS  # type: ignore[assignment]
    elif isinstance(current, SessionStatus) and isinstance(target, SessionStatus):
        transitions = VALID_SESSION_TRANSITIONS  # type: ignore[assignment]
    else:
        raise InvalidTransitionError(entity_type, str(current), str(target))

    allowed = transitions.get(current, frozenset())
    if target not in allowed:
        raise InvalidTransitionError(entity_type, str(current), str(target))
    return True

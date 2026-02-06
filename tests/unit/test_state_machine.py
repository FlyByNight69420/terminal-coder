"""Tests for state machine transitions."""

from __future__ import annotations

import pytest

from tc.core.enums import PhaseStatus, SessionStatus, TaskStatus
from tc.core.state_machine import InvalidTransitionError, validate_transition


class TestTaskTransitions:
    def test_pending_to_queued(self) -> None:
        assert validate_transition(TaskStatus.PENDING, TaskStatus.QUEUED, "task")

    def test_pending_to_skipped(self) -> None:
        assert validate_transition(TaskStatus.PENDING, TaskStatus.SKIPPED, "task")

    def test_queued_to_running(self) -> None:
        assert validate_transition(TaskStatus.QUEUED, TaskStatus.RUNNING, "task")

    def test_queued_to_skipped(self) -> None:
        assert validate_transition(TaskStatus.QUEUED, TaskStatus.SKIPPED, "task")

    def test_running_to_completed(self) -> None:
        assert validate_transition(TaskStatus.RUNNING, TaskStatus.COMPLETED, "task")

    def test_running_to_failed(self) -> None:
        assert validate_transition(TaskStatus.RUNNING, TaskStatus.FAILED, "task")

    def test_failed_to_retrying(self) -> None:
        assert validate_transition(TaskStatus.FAILED, TaskStatus.RETRYING, "task")

    def test_failed_to_paused(self) -> None:
        assert validate_transition(TaskStatus.FAILED, TaskStatus.PAUSED, "task")

    def test_failed_to_skipped(self) -> None:
        assert validate_transition(TaskStatus.FAILED, TaskStatus.SKIPPED, "task")

    def test_retrying_to_running(self) -> None:
        assert validate_transition(TaskStatus.RETRYING, TaskStatus.RUNNING, "task")

    def test_paused_to_queued(self) -> None:
        assert validate_transition(TaskStatus.PAUSED, TaskStatus.QUEUED, "task")

    def test_paused_to_skipped(self) -> None:
        assert validate_transition(TaskStatus.PAUSED, TaskStatus.SKIPPED, "task")

    def test_completed_is_terminal(self) -> None:
        with pytest.raises(InvalidTransitionError):
            validate_transition(TaskStatus.COMPLETED, TaskStatus.PENDING, "task")

    def test_skipped_is_terminal(self) -> None:
        with pytest.raises(InvalidTransitionError):
            validate_transition(TaskStatus.SKIPPED, TaskStatus.PENDING, "task")

    def test_invalid_pending_to_running(self) -> None:
        with pytest.raises(InvalidTransitionError) as exc_info:
            validate_transition(TaskStatus.PENDING, TaskStatus.RUNNING, "task")
        assert exc_info.value.entity_type == "task"
        assert exc_info.value.current == "pending"
        assert exc_info.value.target == "running"

    def test_invalid_pending_to_completed(self) -> None:
        with pytest.raises(InvalidTransitionError):
            validate_transition(TaskStatus.PENDING, TaskStatus.COMPLETED, "task")

    def test_invalid_running_to_queued(self) -> None:
        with pytest.raises(InvalidTransitionError):
            validate_transition(TaskStatus.RUNNING, TaskStatus.QUEUED, "task")


class TestPhaseTransitions:
    def test_pending_to_in_progress(self) -> None:
        assert validate_transition(PhaseStatus.PENDING, PhaseStatus.IN_PROGRESS, "phase")

    def test_pending_to_skipped(self) -> None:
        assert validate_transition(PhaseStatus.PENDING, PhaseStatus.SKIPPED, "phase")

    def test_in_progress_to_completed(self) -> None:
        assert validate_transition(PhaseStatus.IN_PROGRESS, PhaseStatus.COMPLETED, "phase")

    def test_in_progress_to_failed(self) -> None:
        assert validate_transition(PhaseStatus.IN_PROGRESS, PhaseStatus.FAILED, "phase")

    def test_failed_to_in_progress(self) -> None:
        assert validate_transition(PhaseStatus.FAILED, PhaseStatus.IN_PROGRESS, "phase")

    def test_completed_is_terminal(self) -> None:
        with pytest.raises(InvalidTransitionError):
            validate_transition(PhaseStatus.COMPLETED, PhaseStatus.PENDING, "phase")

    def test_invalid_pending_to_completed(self) -> None:
        with pytest.raises(InvalidTransitionError):
            validate_transition(PhaseStatus.PENDING, PhaseStatus.COMPLETED, "phase")


class TestSessionTransitions:
    def test_pending_to_starting(self) -> None:
        assert validate_transition(SessionStatus.PENDING, SessionStatus.STARTING, "session")

    def test_pending_to_failed(self) -> None:
        assert validate_transition(SessionStatus.PENDING, SessionStatus.FAILED, "session")

    def test_starting_to_running(self) -> None:
        assert validate_transition(SessionStatus.STARTING, SessionStatus.RUNNING, "session")

    def test_running_to_completed(self) -> None:
        assert validate_transition(SessionStatus.RUNNING, SessionStatus.COMPLETED, "session")

    def test_running_to_killed(self) -> None:
        assert validate_transition(SessionStatus.RUNNING, SessionStatus.KILLED, "session")

    def test_running_to_timed_out(self) -> None:
        assert validate_transition(SessionStatus.RUNNING, SessionStatus.TIMED_OUT, "session")

    def test_completed_is_terminal(self) -> None:
        with pytest.raises(InvalidTransitionError):
            validate_transition(SessionStatus.COMPLETED, SessionStatus.RUNNING, "session")

    def test_killed_is_terminal(self) -> None:
        with pytest.raises(InvalidTransitionError):
            validate_transition(SessionStatus.KILLED, SessionStatus.RUNNING, "session")

    def test_timed_out_is_terminal(self) -> None:
        with pytest.raises(InvalidTransitionError):
            validate_transition(SessionStatus.TIMED_OUT, SessionStatus.RUNNING, "session")

    def test_invalid_pending_to_running(self) -> None:
        with pytest.raises(InvalidTransitionError):
            validate_transition(SessionStatus.PENDING, SessionStatus.RUNNING, "session")


class TestMixedTypeErrors:
    def test_task_and_phase_mixed_raises(self) -> None:
        with pytest.raises(InvalidTransitionError):
            validate_transition(TaskStatus.PENDING, PhaseStatus.PENDING, "mixed")  # type: ignore[arg-type]

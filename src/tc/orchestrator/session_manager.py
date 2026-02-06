"""Manages Claude Code sessions in TMUX panes."""

from __future__ import annotations

import uuid
from pathlib import Path

from tc.core.enums import SessionStatus, SessionType, TaskType
from tc.core.models import Session, Task
from tc.db.repository import Repository
from tc.tmux.manager import TmuxManager
from tc.tmux.monitor import SessionCheckResult, check_session

_TASK_TYPE_TO_SESSION_TYPE: dict[TaskType, SessionType] = {
    TaskType.CODING: SessionType.CODING,
    TaskType.REVIEW: SessionType.REVIEW,
    TaskType.SECURITY_REVIEW: SessionType.SECURITY_REVIEW,
    TaskType.DEPLOYMENT: SessionType.DEPLOYMENT,
    TaskType.VERIFICATION: SessionType.VERIFICATION,
    TaskType.PLANNING: SessionType.PLANNING,
}


class SessionManager:
    """Manages Claude Code session lifecycle in TMUX panes."""

    def __init__(
        self,
        tmux: TmuxManager,
        repository: Repository,
        project_dir: Path,
    ) -> None:
        self._tmux = tmux
        self._repo = repository
        self._project_dir = project_dir
        self._active: dict[str, str] = {}  # session_id -> pane_id

    def spawn(self, task: Task, brief_path: Path) -> Session:
        """Spawn a Claude Code session for a task."""
        session_id = str(uuid.uuid4())
        pane_id = self._tmux.allocate_pane(task.task_type)
        session_type = _TASK_TYPE_TO_SESSION_TYPE.get(task.task_type, SessionType.CODING)

        log_path = str(self._project_dir / ".tc" / "logs" / f"session-{session_id}.log")

        # Build the claude command
        result_path = self._project_dir / ".tc" / "logs" / f"session-{session_id}-result.json"
        command = (
            f"claude -p"
            f" --output-format text"
            f" --project-dir {self._project_dir}"
            f" < {brief_path}"
            f" 2>&1 | tee {log_path}"
            f"; echo 'exit code:' $?"
        )

        # Create session record
        session = self._repo.create_session(
            id=session_id,
            task_id=task.id,
            project_id=task.project_id,
            session_type=session_type,
            tmux_pane=pane_id,
            log_path=log_path,
        )

        # Send command to TMUX pane
        self._tmux.send_command(pane_id, command)

        # Update session status
        self._repo.update_session_status(session_id, SessionStatus.RUNNING)
        self._repo.update_session_started(session_id, pid=0)

        self._active[session_id] = pane_id

        return session

    def check_active(self) -> list[tuple[Session, SessionCheckResult]]:
        """Check all active sessions and return their current state."""
        results: list[tuple[Session, SessionCheckResult]] = []

        for session_id, pane_id in list(self._active.items()):
            try:
                sessions = self._repo.get_sessions_by_task("")  # We need to fetch by session
                # Get session from active sessions list
                active_sessions = self._repo.get_active_sessions(
                    self._get_project_id_from_session(session_id)
                )
                session = None
                for s in active_sessions:
                    if s.id == session_id:
                        session = s
                        break

                if session is None:
                    self._active.pop(session_id, None)
                    continue

                result = check_session(self._tmux, pane_id)
                results.append((session, result))

                if result.exited:
                    self._active.pop(session_id, None)
            except Exception:
                self._active.pop(session_id, None)

        return results

    def kill_session(self, session_id: str, *, force: bool = False) -> None:
        """Kill a running session."""
        pane_id = self._active.get(session_id)
        if pane_id is None:
            return

        if force:
            self._tmux.send_keys(pane_id, "C-c")
        else:
            self._tmux.send_keys(pane_id, "C-c")

        self._repo.update_session_status(session_id, SessionStatus.KILLED)
        self._active.pop(session_id, None)

    def get_active_sessions(self) -> list[str]:
        """Get list of active session IDs."""
        return list(self._active.keys())

    def has_active_coding(self) -> bool:
        """Check if there's an active coding session."""
        return any(
            pane_id == "coding" for pane_id in self._active.values()
        )

    def has_active_review(self) -> bool:
        """Check if there's an active review session."""
        return any(
            pane_id == "review" for pane_id in self._active.values()
        )

    def _get_project_id_from_session(self, session_id: str) -> str:
        """Helper to get project ID - we store it on spawn."""
        # In practice, all sessions belong to the same project
        # The engine passes the project_id, but for simplicity here
        # we can query any active session
        return ""  # Will be populated by the engine

"""TMUX pane management for Claude Code sessions."""

from __future__ import annotations

import libtmux

from tc.core.enums import TaskType


class TmuxError(Exception):
    """Raised when TMUX operations fail."""


class TmuxManager:
    """Manages TMUX sessions and panes for orchestration."""

    def __init__(self, project_name: str) -> None:
        self._session_name = f"tc-{project_name}"
        self._server: libtmux.Server | None = None
        self._session: libtmux.Session | None = None
        self._panes: dict[str, libtmux.Pane] = {}

    @property
    def session_name(self) -> str:
        return self._session_name

    def setup(self) -> None:
        """Create TMUX session with 2 panes (coding + review)."""
        self._server = libtmux.Server()

        if self.session_exists():
            self._session = self._server.sessions.get(session_name=self._session_name)
        else:
            self._session = self._server.new_session(
                session_name=self._session_name,
                attach=False,
            )

        if self._session is None:
            raise TmuxError(f"Failed to create TMUX session: {self._session_name}")

        window = self._session.active_window
        if window is None:
            raise TmuxError("No active window in TMUX session")

        panes = window.panes
        if len(panes) < 2:
            window.split()
            panes = window.panes

        self._panes["coding"] = panes[0]
        self._panes["review"] = panes[1]

    def teardown(self) -> None:
        """Kill the TMUX session."""
        if self._session is not None:
            try:
                self._session.kill()
            except Exception:
                pass
            self._session = None
            self._panes.clear()

    def session_exists(self) -> bool:
        """Check if the TMUX session already exists."""
        if self._server is None:
            try:
                self._server = libtmux.Server()
            except Exception:
                return False

        try:
            return self._server.sessions.get(session_name=self._session_name) is not None
        except Exception:
            return False

    def allocate_pane(self, task_type: TaskType) -> str:
        """Return the pane ID for the given task type. Coding=pane0, review=pane1."""
        if task_type in (TaskType.REVIEW, TaskType.SECURITY_REVIEW):
            return "review"
        return "coding"

    def send_command(self, pane_id: str, command: str) -> None:
        """Send a command to a TMUX pane."""
        pane = self._panes.get(pane_id)
        if pane is None:
            raise TmuxError(f"Pane not found: {pane_id}")
        pane.send_keys(command)

    def is_pane_busy(self, pane_id: str) -> bool:
        """Check if a command is still running in a pane."""
        pane = self._panes.get(pane_id)
        if pane is None:
            return False
        try:
            # Check if the pane has a running process besides the shell
            pane_pid = pane.get("pane_pid")
            if pane_pid is None:
                return False
            # Check for child processes of the pane
            import subprocess
            result = subprocess.run(
                ["pgrep", "-P", str(pane_pid)],
                capture_output=True, text=True, timeout=5,
            )
            return result.returncode == 0
        except Exception:
            return False

    def capture_output(self, pane_id: str, lines: int = 50) -> str:
        """Capture recent output from a pane."""
        pane = self._panes.get(pane_id)
        if pane is None:
            return ""
        try:
            output = pane.capture_pane()
            if isinstance(output, list):
                return "\n".join(output[-lines:])
            return str(output)
        except Exception:
            return ""

    def send_keys(self, pane_id: str, keys: str) -> None:
        """Send raw keys to a pane (e.g., for Ctrl+C)."""
        pane = self._panes.get(pane_id)
        if pane is None:
            raise TmuxError(f"Pane not found: {pane_id}")
        pane.send_keys(keys, enter=False)

"""Session panel widget showing active Claude Code sessions."""

from __future__ import annotations

from textual.widgets import Static

from tc.core.models import Session


class SessionPanel(Static):
    """Shows active sessions with their status."""

    def __init__(self) -> None:
        super().__init__(id="session-panel")
        self._sessions: list[Session] = []

    def refresh_data(self, sessions: list[Session]) -> None:
        self._sessions = sessions
        self.update(self._render())

    def _render(self) -> str:
        if not self._sessions:
            return "[dim]No active sessions[/dim]"

        lines: list[str] = []
        for session in self._sessions:
            badge = _type_badge(session.session_type.value)
            status_style = _status_style(session.status.value)
            line = (
                f"{badge} "
                f"[{status_style}]{session.status}[/{status_style}]  "
                f"task: {session.task_id[:8]}..."
            )
            if session.pid:
                line += f"  pid: {session.pid}"
            lines.append(line)

        return "\n".join(lines)


def _type_badge(session_type: str) -> str:
    badges = {
        "coding": "[bold blue]CODING[/bold blue]",
        "review": "[bold magenta]REVIEW[/bold magenta]",
        "security_review": "[bold yellow]SECURITY[/bold yellow]",
        "deployment": "[bold cyan]DEPLOY[/bold cyan]",
        "verification": "[bold green]VERIFY[/bold green]",
        "planning": "[bold white]PLAN[/bold white]",
    }
    return badges.get(session_type, f"[bold]{session_type}[/bold]")


def _status_style(status: str) -> str:
    styles = {
        "running": "yellow",
        "pending": "dim",
        "starting": "yellow",
        "completed": "green",
        "failed": "red",
        "killed": "red",
        "timed_out": "red",
    }
    return styles.get(status, "white")

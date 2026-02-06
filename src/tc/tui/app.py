"""Terminal Coder TUI application."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from textual.app import App
from textual.binding import Binding

from tc.config.settings import project_paths
from tc.core.enums import ProjectStatus, TaskStatus
from tc.db.connection import create_connection
from tc.db.repository import Repository
from tc.tui.screens.dashboard import DashboardScreen
from tc.tui.widgets.log_panel import LogPanel
from tc.tui.widgets.phase_tree import PhaseTree
from tc.tui.widgets.session_panel import SessionPanel
from tc.tui.widgets.status_bar import StatusBar


class TerminalCoderApp(App[None]):
    """The Terminal Coder TUI dashboard."""

    TITLE = "Terminal Coder"

    BINDINGS = [
        Binding("p", "pause", "Pause"),
        Binding("r", "resume_engine", "Resume"),
        Binding("k", "kill_sessions", "Kill"),
        Binding("q", "quit", "Quit"),
        Binding("a", "toggle_scroll", "Auto-scroll"),
    ]

    def __init__(
        self,
        project_dir: Path,
        engine: object | None = None,
    ) -> None:
        super().__init__()
        self._project_dir = project_dir
        self._engine = engine
        self._paths = project_paths(project_dir)
        self._conn: sqlite3.Connection | None = None
        self._repo: Repository | None = None

    def compose(self):  # type: ignore[override]
        yield from DashboardScreen().compose()

    def on_mount(self) -> None:
        self._conn = create_connection(self._paths.db_path)
        self._repo = Repository(self._conn)
        self._refresh_data()
        self.set_interval(1.0, self._refresh_data)

    def _refresh_data(self) -> None:
        """Refresh all widgets from the database."""
        if self._repo is None or self._conn is None:
            return

        try:
            row = self._conn.execute("SELECT id, name, status FROM projects LIMIT 1").fetchone()
            if row is None:
                return

            project_id = str(row["id"])
            project_name = str(row["name"])
            project_status = str(row["status"])

            # Refresh phase tree
            phases = self._repo.get_phases_by_project(project_id)
            tasks_by_phase: dict[str, list[object]] = {}
            for phase in phases:
                tasks_by_phase[phase.id] = self._repo.get_tasks_by_phase(phase.id)

            try:
                phase_tree = self.query_one(PhaseTree)
                phase_tree.refresh_data(phases, tasks_by_phase)  # type: ignore[arg-type]
            except Exception:
                pass

            # Refresh session panel
            try:
                session_panel = self.query_one(SessionPanel)
                active = self._repo.get_active_sessions(project_id)
                session_panel.refresh_data(active)
            except Exception:
                pass

            # Refresh log panel
            try:
                log_panel = self.query_one(LogPanel)
                events = self._repo.get_events_by_project(project_id, limit=100)
                log_panel.add_events(events)
            except Exception:
                pass

            # Refresh status bar
            try:
                status_bar = self.query_one(StatusBar)
                failed = self._repo.get_tasks_by_status(project_id, TaskStatus.FAILED)
                paused = project_status == "paused"
                status_bar.refresh_data(paused=paused, failed_count=len(failed))
            except Exception:
                pass

        except Exception:
            pass

    def action_pause(self) -> None:
        if self._engine is not None and hasattr(self._engine, "pause"):
            self._engine.pause()
        elif self._repo is not None and self._conn is not None:
            row = self._conn.execute("SELECT id FROM projects LIMIT 1").fetchone()
            if row:
                self._repo.update_project_status(
                    str(row["id"]), ProjectStatus.PAUSED
                )

    def action_resume_engine(self) -> None:
        if self._engine is not None and hasattr(self._engine, "resume"):
            self._engine.resume()
        elif self._repo is not None and self._conn is not None:
            row = self._conn.execute("SELECT id FROM projects LIMIT 1").fetchone()
            if row:
                self._repo.update_project_status(
                    str(row["id"]), ProjectStatus.RUNNING
                )

    def action_kill_sessions(self) -> None:
        if self._engine is not None and hasattr(self._engine, "stop"):
            self._engine.stop()

    def action_toggle_scroll(self) -> None:
        try:
            log_panel = self.query_one(LogPanel)
            log_panel.toggle_auto_scroll()
        except Exception:
            pass

    def on_unmount(self) -> None:
        if self._conn is not None:
            self._conn.close()

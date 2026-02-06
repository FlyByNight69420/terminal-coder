"""Full-screen log viewer for session logs."""

from __future__ import annotations

from pathlib import Path

from textual.screen import Screen
from textual.widgets import Footer, Header, RichLog


class LogViewerScreen(Screen[None]):
    """Full-screen session log viewer."""

    BINDINGS = [
        ("escape", "dismiss", "Back"),
    ]

    def __init__(self, log_path: Path) -> None:
        super().__init__()
        self._log_path = log_path

    def compose(self):  # type: ignore[override]
        yield Header()
        yield RichLog(id="log-content", wrap=True, highlight=True)
        yield Footer()

    def on_mount(self) -> None:
        log_widget = self.query_one("#log-content", RichLog)
        if self._log_path.exists():
            content = self._log_path.read_text()
            for line in content.split("\n"):
                log_widget.write(line)
        else:
            log_widget.write("[dim]Log file not found[/dim]")

    def action_dismiss(self) -> None:
        self.app.pop_screen()

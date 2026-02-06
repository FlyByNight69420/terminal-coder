"""Status bar widget showing keyboard shortcuts."""

from __future__ import annotations

from textual.widgets import Static


class StatusBar(Static):
    """Bottom bar showing keyboard shortcuts and status indicators."""

    def __init__(self) -> None:
        super().__init__()
        self._paused = False
        self._failed_count = 0

    def refresh_data(self, *, paused: bool = False, failed_count: int = 0) -> None:
        self._paused = paused
        self._failed_count = failed_count
        self.update(self._render())

    def _render(self) -> str:
        parts = [
            "[bold][P][/bold]ause",
            "[bold][R][/bold]esume",
            "[bold][K][/bold]ill",
            "[bold][Q][/bold]uit",
        ]
        line = "  ".join(parts)

        if self._paused:
            line += "  [bold yellow]PAUSED[/bold yellow]"
        if self._failed_count > 0:
            line += f"  [bold red]{self._failed_count} failed[/bold red]"

        return line

    def on_mount(self) -> None:
        self.update(self._render())

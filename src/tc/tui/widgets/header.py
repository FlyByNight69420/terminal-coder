"""Header widget showing project name and overall status."""

from __future__ import annotations

from textual.widgets import Static


class ProjectHeader(Static):
    """Displays project name, current phase, and status."""

    def __init__(
        self,
        project_name: str = "",
        status: str = "",
        phase_info: str = "",
    ) -> None:
        super().__init__()
        self._project_name = project_name
        self._status = status
        self._phase_info = phase_info

    def compose_text(self) -> str:
        status_style = _status_color(self._status)
        return (
            f" {self._project_name}  "
            f"[{status_style}]{self._status}[/{status_style}]  "
            f"{self._phase_info}"
        )

    def on_mount(self) -> None:
        self.update(self.compose_text())

    def refresh_data(
        self,
        project_name: str,
        status: str,
        phase_info: str,
    ) -> None:
        self._project_name = project_name
        self._status = status
        self._phase_info = phase_info
        self.update(self.compose_text())


def _status_color(status: str) -> str:
    colors = {
        "running": "bold yellow",
        "paused": "bold yellow",
        "completed": "bold green",
        "failed": "bold red",
        "initialized": "dim",
        "planning": "yellow",
        "planned": "cyan",
    }
    return colors.get(status, "white")

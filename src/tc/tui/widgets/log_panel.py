"""Log panel widget showing event history."""

from __future__ import annotations

from textual.widgets import RichLog

from tc.core.enums import EventType
from tc.core.models import Event


_EVENT_STYLES: dict[str, str] = {
    EventType.STATUS_CHANGED: "blue",
    EventType.CREATED: "green",
    EventType.RETRIED: "yellow",
    EventType.ERROR: "red",
    EventType.PAUSED: "yellow",
    EventType.RESUMED: "green",
    EventType.REVIEW_SCHEDULED: "magenta",
    EventType.DEPLOYMENT_STARTED: "cyan",
    EventType.VERIFICATION_RESULT: "green",
    EventType.HUMAN_INPUT_REQUESTED: "bold yellow",
}


class LogPanel(RichLog):
    """Scrollable event log panel."""

    def __init__(self) -> None:
        super().__init__(id="log-panel", wrap=True, highlight=True, markup=True)
        self._seen_ids: set[int] = set()
        self._auto_scroll = True

    def add_events(self, events: list[Event]) -> None:
        """Add new events to the log."""
        for event in reversed(events):  # Show oldest first
            if event.id in self._seen_ids:
                continue
            self._seen_ids.add(event.id)
            style = _EVENT_STYLES.get(event.event_type, "white")
            timestamp = event.created_at.strftime("%H:%M:%S") if event.created_at else "??:??:??"
            line = f"[dim]{timestamp}[/dim] [{style}]{event.event_type}[/{style}] {event.entity_type}/{event.entity_id[:8]}"
            if event.new_value:
                line += f" -> {event.new_value}"
            self.write(line)

    def toggle_auto_scroll(self) -> None:
        self._auto_scroll = not self._auto_scroll
        self.auto_scroll = self._auto_scroll

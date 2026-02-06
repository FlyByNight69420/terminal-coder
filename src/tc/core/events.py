"""Event system for inter-component communication."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from threading import Lock

from tc.core.enums import EventType


@dataclass(frozen=True)
class EngineEvent:
    event_type: EventType
    entity_type: str
    entity_id: str
    message: str
    old_value: str | None = None
    new_value: str | None = None
    metadata: str | None = None
    timestamp: datetime | None = None


EventCallback = Callable[[EngineEvent], None]


class EventBus:
    """Publish-subscribe event bus for engine events."""

    def __init__(self) -> None:
        self._subscribers: list[EventCallback] = []
        self._queue: list[EngineEvent] = []
        self._lock = Lock()

    def subscribe(self, callback: EventCallback) -> None:
        """Register an event callback."""
        with self._lock:
            self._subscribers.append(callback)

    def publish(self, event: EngineEvent) -> None:
        """Publish an event to all subscribers and buffer it."""
        timestamped = EngineEvent(
            event_type=event.event_type,
            entity_type=event.entity_type,
            entity_id=event.entity_id,
            message=event.message,
            old_value=event.old_value,
            new_value=event.new_value,
            metadata=event.metadata,
            timestamp=event.timestamp or datetime.now(),
        )

        with self._lock:
            self._queue.append(timestamped)

        for callback in self._subscribers:
            try:
                callback(timestamped)
            except Exception:
                pass  # Don't let subscriber errors break the bus

    def drain(self) -> list[EngineEvent]:
        """Drain and return all buffered events."""
        with self._lock:
            events = list(self._queue)
            self._queue.clear()
            return events

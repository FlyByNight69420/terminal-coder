"""Tests for the event bus."""

from __future__ import annotations

from tc.core.enums import EventType
from tc.core.events import EngineEvent, EventBus


class TestEventBus:
    def test_publish_and_subscribe(self) -> None:
        bus = EventBus()
        received: list[EngineEvent] = []
        bus.subscribe(received.append)

        event = EngineEvent(
            event_type=EventType.STATUS_CHANGED,
            entity_type="task",
            entity_id="t1",
            message="Task started",
        )
        bus.publish(event)

        assert len(received) == 1
        assert received[0].message == "Task started"
        assert received[0].timestamp is not None

    def test_drain_returns_all_events(self) -> None:
        bus = EventBus()
        bus.publish(EngineEvent(
            event_type=EventType.CREATED, entity_type="task",
            entity_id="t1", message="Created",
        ))
        bus.publish(EngineEvent(
            event_type=EventType.STATUS_CHANGED, entity_type="task",
            entity_id="t1", message="Changed",
        ))

        events = bus.drain()
        assert len(events) == 2

        # Drain should clear the queue
        events = bus.drain()
        assert len(events) == 0

    def test_subscriber_error_doesnt_break_bus(self) -> None:
        bus = EventBus()

        def _bad_callback(event: EngineEvent) -> None:
            raise RuntimeError("oops")

        good_received: list[EngineEvent] = []
        bus.subscribe(_bad_callback)
        bus.subscribe(good_received.append)

        bus.publish(EngineEvent(
            event_type=EventType.ERROR, entity_type="task",
            entity_id="t1", message="Error",
        ))

        # Good subscriber should still receive the event
        assert len(good_received) == 1

    def test_multiple_subscribers(self) -> None:
        bus = EventBus()
        list1: list[EngineEvent] = []
        list2: list[EngineEvent] = []

        bus.subscribe(list1.append)
        bus.subscribe(list2.append)

        bus.publish(EngineEvent(
            event_type=EventType.CREATED, entity_type="project",
            entity_id="p1", message="Created",
        ))

        assert len(list1) == 1
        assert len(list2) == 1

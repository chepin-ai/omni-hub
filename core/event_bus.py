"""
OMNI-HUB Event Bus v14.1
Unified inter-module communication via publish-subscribe pattern.
Inspired by BabyAGI 3: "everything is a message".
"""

from typing import Dict, List, Callable, Any
from dataclasses import dataclass, field
from datetime import datetime
import threading


@dataclass
class Event:
    """Unified event message format."""
    topic: str
    payload: Dict[str, Any]
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    source: str = "unknown"
    priority: int = 0  # 0=normal, 1=high, -1=low


class EventBus:
    """Central event bus for OMNI-HUB module communication."""

    def __init__(self):
        self._subscribers: Dict[str, List[Callable[[Event], None]]] = {}
        self._history: List[Event] = []
        self._lock = threading.Lock()

    def subscribe(self, topic: str, handler: Callable[[Event], None]):
        """Subscribe a handler to a topic."""
        with self._lock:
            if topic not in self._subscribers:
                self._subscribers[topic] = []
            self._subscribers[topic].append(handler)

    def publish(self, event: Event):
        """Publish an event to all subscribers."""
        with self._lock:
            self._history.append(event)
            handlers = self._subscribers.get(event.topic, []).copy()
        for handler in handlers:
            try:
                handler(event)
            except Exception as e:
                print(f"[EventBus] Handler error on {event.topic}: {e}")

    def publish_simple(self, topic: str, payload: Dict[str, Any], source: str = "unknown"):
        """Convenience method to publish without creating Event object."""
        self.publish(Event(topic=topic, payload=payload, source=source))

    def get_history(self, topic: str = None, limit: int = 100) -> List[Event]:
        """Get event history, optionally filtered by topic."""
        with self._lock:
            events = self._history[-limit:] if limit else self._history
            if topic:
                events = [e for e in events if e.topic == topic]
            return events

    def stats(self) -> Dict[str, Any]:
        """Return bus statistics."""
        with self._lock:
            topic_counts = {}
            for e in self._history:
                topic_counts[e.topic] = topic_counts.get(e.topic, 0) + 1
            return {
                "total_events": len(self._history),
                "topics": list(self._subscribers.keys()),
                "topic_counts": topic_counts,
                "subscriber_count": sum(len(h) for h in self._subscribers.values()),
            }


# Global singleton instance
_GLOBAL_BUS: EventBus = None


def get_bus() -> EventBus:
    """Get the global event bus instance."""
    global _GLOBAL_BUS
    if _GLOBAL_BUS is None:
        _GLOBAL_BUS = EventBus()
    return _GLOBAL_BUS


def reset_bus():
    """Reset the global event bus (for testing)."""
    global _GLOBAL_BUS
    _GLOBAL_BUS = EventBus()


# Standard topic definitions
class Topics:
    CYCLE_START = "cycle.start"
    CYCLE_END = "cycle.end"
    STATE_CHANGE = "state.change"
    LEVEL_UP = "level.up"
    ALERT = "alert"
    ACTION_SELECTED = "action.selected"
    PERSISTENCE_SAVE = "persistence.save"
    GIT_COMMIT = "git.commit"
    MONITOR_CHECK = "monitor.check"


if __name__ == "__main__":
    # Demonstration
    bus = EventBus()

    def on_level_up(event: Event):
        print(f"🎉 LEVEL UP: {event.payload}")

    def on_alert(event: Event):
        print(f"⚠️ ALERT: {event.payload}")

    bus.subscribe(Topics.LEVEL_UP, on_level_up)
    bus.subscribe(Topics.ALERT, on_alert)

    bus.publish_simple(Topics.LEVEL_UP, {"old": 14, "new": 15}, source="north_star")
    bus.publish_simple(Topics.ALERT, {"type": "phi_low", "value": 0.1}, source="monitor")

    print(f"\nBus stats: {bus.stats()}")

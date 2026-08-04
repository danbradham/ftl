from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass, field


@dataclass
class Event:
    type: str
    payload: dict = field(default_factory=dict)


@dataclass
class Signals:
    map: dict[str, set[Callable]] = field(
        default_factory=lambda: defaultdict(set), init=False
    )
    docs: dict[str, str | None] = field(default_factory=dict, init=False)

    def define(self, name: str, description: str | None = None):
        """Define and describe a new signal."""

        self.docs[name] = description

    def on(self, name: str, handler: Callable):
        """Register a handler for a named signal."""

        self.map[name].add(handler)

    def off(self, handler: Callable, name: str | None):
        """Unregister a handler."""

        if name:
            self.map[name].discard(handler)
        else:
            for handlers in self.map.values():
                handlers.discard(handler)

    def send(self, name: str, payload: dict | None = None):
        """Dispatch an event to all the registered handlers"""

        event = Event(name, payload or {})
        for handler in self.map[name]:
            handler(event)

    def describe(self):
        """Return a dictionary of signal names and their descriptions."""

        return self.docs.copy()

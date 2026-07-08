from __future__ import annotations

from collections import defaultdict
from typing import Callable

from travelos.events.domain_event import DomainEvent
from travelos.logging.travel_logger import TravelLogger

Handler = Callable[[DomainEvent], None]

_logger = TravelLogger.for_service("EventBus")


class EventBus:
    """
    Synchronous, in-process pub/sub event bus.

    Handlers are registered per event type.  Publishing an event calls
    all registered handlers synchronously before returning.

    A handler that raises an exception is logged and skipped â€” it must
    not crash the publisher.

    Sprint 3+: replace with an async bus backed by Redis Streams or RabbitMQ.
    """

    def __init__(self) -> None:
        self._handlers: dict[str, list[Handler]] = defaultdict(list)

    # ------------------------------------------------------------------
    # Subscription
    # ------------------------------------------------------------------

    def subscribe(self, event_type: type | str, handler: Handler) -> None:
        """Register a handler for a specific event type."""
        name = event_type if isinstance(event_type, str) else event_type.__name__
        self._handlers[name].append(handler)
        _logger.debug("Handler registered", event_type=name, handler=handler.__qualname__)

    def subscribe_all(self, handler: Handler) -> None:
        """Register a handler that receives every event (wildcard)."""
        self._handlers["*"].append(handler)

    def unsubscribe(self, event_type: type | str, handler: Handler) -> None:
        name = event_type if isinstance(event_type, str) else event_type.__name__
        self._handlers[name] = [h for h in self._handlers[name] if h is not handler]

    # ------------------------------------------------------------------
    # Publishing
    # ------------------------------------------------------------------

    def publish(self, event: DomainEvent) -> int:
        """
        Dispatch event to all subscribers.

        Returns the count of handlers invoked.
        """
        name = event.event_type
        handlers = list(self._handlers.get(name, []))
        wildcard = list(self._handlers.get("*", []))
        all_handlers = handlers + wildcard

        count = 0
        for handler in all_handlers:
            try:
                handler(event)
                count += 1
            except Exception as exc:
                _logger.exception(
                    "Handler raised an exception",
                    exc,
                    event_type=name,
                    handler=handler.__qualname__,
                )
        _logger.debug("Event published", event_type=name, handlers_called=count)
        return count

    # ------------------------------------------------------------------
    # Introspection
    # ------------------------------------------------------------------

    def subscribers(self, event_type: type | str) -> list[Handler]:
        name = event_type if isinstance(event_type, str) else event_type.__name__
        return list(self._handlers.get(name, []))

    def all_subscriptions(self) -> dict[str, int]:
        return {k: len(v) for k, v in self._handlers.items() if v}

    def clear(self) -> None:
        """Remove all subscriptions. Primarily for use in tests."""
        self._handlers.clear()


event_bus = EventBus()

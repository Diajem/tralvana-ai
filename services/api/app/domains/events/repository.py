from __future__ import annotations

from app.domains.events.models import EventOption


class EventRepository:
    """In-memory event recommendation store; live listings are not persisted."""

    def __init__(self) -> None:
        self._store: dict[str, EventOption] = {}

    def save_many(self, options: list[EventOption]) -> list[EventOption]:
        for option in options:
            self._store[option.event_option_id] = option
        return options

    def get(self, event_option_id: str) -> EventOption | None:
        return self._store.get(event_option_id)

    def list_by_trip(self, trip_id: str) -> list[EventOption]:
        return [
            option for option in self._store.values()
            if option.trip_id == trip_id
        ]

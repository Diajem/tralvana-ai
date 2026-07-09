from __future__ import annotations

from app.domains.destinations.models import DestinationOption


class DestinationRepository:
    """In-memory store. Replace with a PostgreSQL adapter in Sprint 3."""

    def __init__(self) -> None:
        self._store: dict[str, DestinationOption] = {}

    def save(self, destination: DestinationOption) -> DestinationOption:
        self._store[destination.destination_option_id] = destination
        return destination

    def save_many(self, options: list[DestinationOption]) -> list[DestinationOption]:
        for o in options:
            self._store[o.destination_option_id] = o
        return options

    def get(self, destination_option_id: str) -> DestinationOption | None:
        return self._store.get(destination_option_id)

    def list_by_trip(self, trip_id: str) -> list[DestinationOption]:
        return [o for o in self._store.values() if o.trip_id == trip_id]

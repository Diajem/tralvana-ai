from __future__ import annotations

from app.domains.accommodation.models import AccommodationOption


class AccommodationRepository:
    """In-memory store. Replace with a PostgreSQL adapter in Sprint 3."""

    def __init__(self) -> None:
        self._store: dict[str, AccommodationOption] = {}

    def save(self, accommodation: AccommodationOption) -> AccommodationOption:
        self._store[accommodation.accommodation_option_id] = accommodation
        return accommodation

    def save_many(self, options: list[AccommodationOption]) -> list[AccommodationOption]:
        for o in options:
            self._store[o.accommodation_option_id] = o
        return options

    def get(self, accommodation_option_id: str) -> AccommodationOption | None:
        return self._store.get(accommodation_option_id)

    def list_by_trip(self, trip_id: str) -> list[AccommodationOption]:
        return [o for o in self._store.values() if o.trip_id == trip_id]

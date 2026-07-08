from __future__ import annotations

from typing import Any

from app.domains.trips.models import TripPlan


class TripRepository:
    """In-memory store. Replace with a PostgreSQL adapter in Sprint 3."""

    def __init__(self) -> None:
        self._store: dict[str, TripPlan] = {}

    def save(self, trip: TripPlan) -> TripPlan:
        self._store[trip.trip_id] = trip
        return trip

    def get(self, trip_id: str) -> TripPlan | None:
        return self._store.get(trip_id)

    def list_by_traveller(self, traveller_id: str) -> list[TripPlan]:
        return [t for t in self._store.values() if t.traveller_id == traveller_id]

    def update(self, trip_id: str, updates: dict[str, Any]) -> TripPlan | None:
        trip = self._store.get(trip_id)
        if not trip:
            return None
        for key, value in updates.items():
            if hasattr(trip, key) and value is not None:
                setattr(trip, key, value)
        return trip

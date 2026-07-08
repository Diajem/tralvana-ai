from __future__ import annotations

from app.domains.flights.models import FlightOption


class FlightRepository:
    """In-memory store. Replace with a PostgreSQL adapter in Sprint 3."""

    def __init__(self) -> None:
        self._store: dict[str, FlightOption] = {}

    def save(self, flight: FlightOption) -> FlightOption:
        self._store[flight.flight_option_id] = flight
        return flight

    def save_many(self, flights: list[FlightOption]) -> list[FlightOption]:
        for f in flights:
            self._store[f.flight_option_id] = f
        return flights

    def get(self, flight_option_id: str) -> FlightOption | None:
        return self._store.get(flight_option_id)

    def list_by_trip(self, trip_id: str) -> list[FlightOption]:
        return [f for f in self._store.values() if f.trip_id == trip_id]

"""Traveller profile repository adapters."""

from __future__ import annotations

from app.domains.traveller.models import TravellerProfile


class TravellerRepository:
    """Zero-setup in-memory Traveller profile repository."""

    def __init__(self) -> None:
        self._store: dict[str, TravellerProfile] = {}

    def save(self, profile: TravellerProfile) -> TravellerProfile:
        self._store[profile.id] = profile
        return profile

    def get(self, traveller_id: str) -> TravellerProfile | None:
        return self._store.get(traveller_id)

    def list_all(self) -> list[TravellerProfile]:
        return list(self._store.values())

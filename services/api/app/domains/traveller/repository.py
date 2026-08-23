"""Traveller profile repository adapters."""

from __future__ import annotations

from app.domains.traveller.models import TravellerProfile
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.database.session import create_engine_from_url, create_session_factory, database_url
from app.domains.traveller.orm import TravellerProfileRow


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


class SqlAlchemyTravellerRepository:
    """Persistent traveller profile adapter keyed by the Clerk subject."""

    def __init__(self, factory: sessionmaker[Session]) -> None:
        self._factory = factory

    def save(self, profile: TravellerProfile) -> TravellerProfile:
        with self._factory.begin() as database:
            database.merge(
                TravellerProfileRow(
                    traveller_id=profile.id,
                    created_at=profile.created_at,
                    updated_at=profile.updated_at,
                    identity=profile.identity,
                    preferences=profile.preferences,
                    loyalty=profile.loyalty,
                    travel_history=profile.travel_history,
                )
            )
        return profile

    def get(self, traveller_id: str) -> TravellerProfile | None:
        with self._factory() as database:
            row = database.get(TravellerProfileRow, traveller_id)
            return _profile(row) if row else None

    def list_all(self) -> list[TravellerProfile]:
        with self._factory() as database:
            return [
                _profile(row)
                for row in database.scalars(
                    select(TravellerProfileRow).order_by(TravellerProfileRow.created_at)
                ).all()
            ]


def build_traveller_repository():
    url = database_url()
    if not url:
        return TravellerRepository()
    engine = create_engine_from_url(url)
    return SqlAlchemyTravellerRepository(create_session_factory(engine))


def _profile(row: TravellerProfileRow) -> TravellerProfile:
    return TravellerProfile(
        id=row.traveller_id,
        created_at=row.created_at,
        updated_at=row.updated_at,
        identity=dict(row.identity),
        preferences=dict(row.preferences),
        loyalty=dict(row.loyalty),
        travel_history=list(row.travel_history),
    )

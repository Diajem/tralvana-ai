from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.database.session import (
    create_engine_from_url,
    create_session_factory,
    database_url,
)
from app.domains.trips.models import TripPlan
from app.domains.trips.orm import TripPlanRow


class TripRepository:
    """Zero-setup in-memory adapter used when DATABASE_URL is absent."""

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


class SqlAlchemyTripRepository:
    """Persistent TripPlan adapter sharing Tralvana's SQLAlchemy stack."""

    def __init__(self, factory: sessionmaker[Session]) -> None:
        self._factory = factory

    def save(self, trip: TripPlan) -> TripPlan:
        with self._factory.begin() as session:
            session.merge(_row(trip))
        return trip

    def get(self, trip_id: str) -> TripPlan | None:
        with self._factory() as session:
            row = session.get(TripPlanRow, trip_id)
            return _entity(row) if row else None

    def list_by_traveller(self, traveller_id: str) -> list[TripPlan]:
        with self._factory() as session:
            rows = session.scalars(
                select(TripPlanRow)
                .where(TripPlanRow.traveller_id == traveller_id)
                .order_by(TripPlanRow.created_at, TripPlanRow.trip_id)
            ).all()
            return [_entity(row) for row in rows]

    def update(
        self,
        trip_id: str,
        updates: dict[str, Any],
    ) -> TripPlan | None:
        with self._factory.begin() as session:
            row = session.get(TripPlanRow, trip_id)
            if row is None:
                return None
            for key, value in updates.items():
                if hasattr(row, key) and value is not None:
                    setattr(row, key, value)
            session.flush()
            return _entity(row)


def build_trip_repository():
    url = database_url()
    if not url:
        return TripRepository()
    engine = create_engine_from_url(url)
    return SqlAlchemyTripRepository(create_session_factory(engine))


def _row(trip: TripPlan) -> TripPlanRow:
    return TripPlanRow(**trip.to_dict())


def _entity(row: TripPlanRow) -> TripPlan:
    return TripPlan(
        trip_id=row.trip_id,
        traveller_id=row.traveller_id,
        goal_id=row.goal_id,
        title=row.title,
        origin=row.origin,
        destination=row.destination,
        duration_days=row.duration_days,
        budget=dict(row.budget),
        travellers=dict(row.travellers),
        interests=list(row.interests),
        travel_style=row.travel_style,
        assumptions=list(row.assumptions),
        missing_information=list(row.missing_information),
        recommended_destinations=list(row.recommended_destinations),
        draft_itinerary=list(row.draft_itinerary),
        estimated_budget_breakdown=dict(row.estimated_budget_breakdown),
        risks=list(row.risks),
        confidence=row.confidence,
        status=row.status,
        created_at=row.created_at,
        updated_at=row.updated_at,
        recommended_agents=list(row.recommended_agents),
        next_actions=list(row.next_actions),
        trip_summary=row.trip_summary,
    )

"""T-064 durable planner-memory adapter acceptance tests."""

from __future__ import annotations

from app.adapters.conversation_session_store import SqlAlchemySessionStore
from app.database.base import Base
from app.database.session import create_engine_from_url, create_session_factory
from app.domains.traveller.models import TravellerProfile
from app.domains.traveller.repository import SqlAlchemyTravellerRepository


def test_sql_store_survives_adapter_recreation_and_filters_by_account(tmp_path):
    engine = create_engine_from_url(f"sqlite+pysqlite:///{tmp_path / 'sessions.db'}")
    Base.metadata.create_all(engine)
    factory = create_session_factory(engine)

    first_worker = SqlAlchemySessionStore(factory)
    saved = first_worker.create("account-owner")
    saved.trip_id = "trip-persisted"
    saved.planning_entities = {"destination": "Lisbon"}
    saved.last_planner_response = {
        "conversation_id": saved.conversation_id,
        "intent": "PLAN_TRIP",
        "response": "Your Lisbon plan",
        "confidence": 0.9,
        "assumptions": [],
        "missing_information": [],
        "next_actions": [],
        "goal_id": None,
        "trip_id": saved.trip_id,
        "itinerary": {"trip_brief": {"destination": "Lisbon"}},
    }
    first_worker.save(saved)

    second_worker = SqlAlchemySessionStore(factory)
    restored = second_worker.get(saved.conversation_id)

    assert restored is not None
    assert restored.last_planner_response == saved.last_planner_response
    assert second_worker.find_by_trip_id("trip-persisted") == restored
    assert second_worker.list_by_traveller("account-owner") == [restored]
    assert second_worker.list_by_traveller("another-account") == []
    engine.dispose()


def test_traveller_profile_survives_repository_recreation(tmp_path):
    engine = create_engine_from_url(f"sqlite+pysqlite:///{tmp_path / 'profiles.db'}")
    Base.metadata.create_all(engine)
    factory = create_session_factory(engine)
    profile = TravellerProfile(
        id="clerk-account-1",
        created_at="2026-08-23T10:00:00+00:00",
        updated_at="2026-08-23T10:00:00+00:00",
        identity={"name": "Returning Traveller"},
        preferences={"budget_style": "comfort", "travel_interests": ["food"]},
        loyalty={"airline_programs": []},
    )

    SqlAlchemyTravellerRepository(factory).save(profile)
    restored = SqlAlchemyTravellerRepository(factory).get("clerk-account-1")

    assert restored == profile
    engine.dispose()

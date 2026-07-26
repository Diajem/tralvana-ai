from app.database.base import Base
from app.database.session import create_engine_from_url, create_session_factory
from app.domains.goals.models import Goal
from app.domains.goals.repository import (
    GoalRepository,
    SqlAlchemyGoalRepository,
    build_goal_repository,
)
from app.domains.trips.models import TripPlan
from app.domains.trips.repository import (
    SqlAlchemyTripRepository,
    TripRepository,
    build_trip_repository,
)


def _goal(goal_id="goal-1", traveller_id="traveller-1"):
    return Goal(
        goal_id=goal_id,
        traveller_id=traveller_id,
        title="New York holiday",
        goal_type="GENERAL_TRAVEL",
        priority=3,
        budget={"min_usd": 2_000, "max_usd": 5_000, "currency": "USD"},
        timeframe={
            "earliest": "2026-08-07",
            "latest": "2026-08-22",
            "duration_days": 15,
            "flexible": False,
        },
        travellers={"adults": 2, "children": 0, "infants": 0},
        interests=["fashion", "soccer"],
        constraints=["average hotel"],
        success_criteria=["complete itinerary"],
        flexibility={"dates": False, "duration": False, "budget": True},
        status="ACTIVE",
        created_at="2026-07-26T10:00:00+00:00",
        updated_at="2026-07-26T10:00:00+00:00",
    )


def _trip(trip_id="trip-1", traveller_id="traveller-1", goal_id="goal-1"):
    return TripPlan(
        trip_id=trip_id,
        traveller_id=traveller_id,
        goal_id=goal_id,
        title="Holiday — New York (15 days)",
        origin="Leeds",
        destination="New York",
        duration_days=15,
        budget={"min_usd": 2_000, "max_usd": 5_000, "currency": "USD"},
        travellers={"adults": 2, "children": 0, "infants": 0},
        interests=["fashion", "soccer"],
        travel_style="balanced",
        assumptions=["estimated prices"],
        missing_information=[],
        recommended_destinations=[],
        draft_itinerary=[{"day": 1, "title": "Arrival"}],
        estimated_budget_breakdown={"total_estimate_usd": 5_700},
        risks=[{"type": "PRICE", "severity": "MEDIUM"}],
        confidence=0.8,
        status="READY",
        created_at="2026-07-26T10:00:00+00:00",
        updated_at="2026-07-26T10:00:00+00:00",
        recommended_agents=["flight_agent"],
        next_actions=["check live prices"],
        trip_summary="A grounded New York plan.",
    )


def _repositories(tmp_path):
    url = f"sqlite+pysqlite:///{tmp_path / 'persistence.db'}"
    engine = create_engine_from_url(url)
    Base.metadata.create_all(engine)
    factory = create_session_factory(engine)
    return (
        engine,
        SqlAlchemyGoalRepository(factory),
        SqlAlchemyTripRepository(factory),
    )


def test_goal_persists_across_repository_instances(tmp_path):
    engine, goals, _ = _repositories(tmp_path)
    factory = create_session_factory(engine)
    goals.save(_goal())

    reloaded = SqlAlchemyGoalRepository(factory).get("goal-1")

    assert reloaded == _goal()
    assert SqlAlchemyGoalRepository(factory).list_by_traveller(
        "traveller-1"
    ) == [_goal()]
    engine.dispose()


def test_goal_update_and_delete_are_transactional(tmp_path):
    engine, goals, _ = _repositories(tmp_path)
    goals.save(_goal())

    updated = goals.update(
        "goal-1",
        {"title": "Updated holiday", "budget": {"max_usd": 6_000}},
    )

    assert updated.title == "Updated holiday"
    assert goals.get("goal-1").budget == {"max_usd": 6_000}
    assert goals.delete("goal-1") is True
    assert goals.delete("goal-1") is False
    assert goals.get("goal-1") is None
    engine.dispose()


def test_trip_persists_nested_plan_across_repository_instances(tmp_path):
    engine, _, trips = _repositories(tmp_path)
    factory = create_session_factory(engine)
    trips.save(_trip())

    reloaded = SqlAlchemyTripRepository(factory).get("trip-1")

    assert reloaded == _trip()
    assert reloaded.draft_itinerary == [{"day": 1, "title": "Arrival"}]
    assert SqlAlchemyTripRepository(factory).list_by_traveller(
        "traveller-1"
    ) == [_trip()]
    engine.dispose()


def test_trip_update_is_persistent(tmp_path):
    engine, _, trips = _repositories(tmp_path)
    trips.save(_trip())

    updated = trips.update(
        "trip-1",
        {"destination": "Brooklyn", "status": "ARCHIVED"},
    )

    assert updated.destination == "Brooklyn"
    assert trips.get("trip-1").status == "ARCHIVED"
    assert trips.update("missing", {"status": "READY"}) is None
    engine.dispose()


def test_repository_factories_use_memory_without_database(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)

    assert isinstance(build_goal_repository(), GoalRepository)
    assert isinstance(build_trip_repository(), TripRepository)


def test_repository_factories_use_sqlalchemy_when_configured(
    monkeypatch,
    tmp_path,
):
    monkeypatch.setenv(
        "DATABASE_URL",
        f"sqlite+pysqlite:///{tmp_path / 'configured.db'}",
    )

    assert isinstance(build_goal_repository(), SqlAlchemyGoalRepository)
    assert isinstance(build_trip_repository(), SqlAlchemyTripRepository)

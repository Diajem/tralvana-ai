"""T-036 dependency direction and PlanningPort acceptance tests."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

from ai.concierge.conversation_engine import ConversationEngine
from ai.concierge.session_store import InMemorySessionStore
from ai.trip_brain.context import ContextBuilder

ROOT = Path(__file__).parents[2]


class StubPlanningPort:
    def __init__(self) -> None:
        self.goals = {"goal-1": {"goal_id": "goal-1", "budget": {"max_usd": 3000}}}
        self.trips = {"trip-1": {"trip_id": "trip-1", "destination": "Tokyo"}}

    def create_goal(self, traveller_id, message, entities):
        return {"goal_id": "goal-created"}

    def create_trip(self, traveller_id, goal_id, entities, profile):
        return {"trip_id": "trip-created"}

    def get_goal(self, goal_id):
        return self.goals.get(goal_id)

    def get_trip(self, trip_id):
        return self.trips.get(trip_id)

    def recommend_flights(self, **kwargs: Any):
        return {
            "origin": "London",
            "destination": "Tokyo",
            "flight_options": [],
            "assumptions": [],
            "next_actions": [],
        }

    def __getattr__(self, name: str):
        def empty(**_kwargs: Any):
            return {}

        return empty


def test_ai_production_code_never_imports_fastapi_application_modules():
    offenders = []
    for path in (ROOT / "ai").rglob("*.py"):
        if "tests" in path.parts:
            continue
        source = path.read_text(encoding="utf-8")
        if "from app." in source or "import app." in source:
            offenders.append(str(path.relative_to(ROOT)))

    assert offenders == []


def test_context_builder_reads_goal_and_trip_through_injected_port():
    context = ContextBuilder(StubPlanningPort()).build(
        traveller_id="traveller-1",
        trip_id="trip-1",
        goal_id="goal-1",
        entities={},
        profile=None,
    )

    assert context.goal["goal_id"] == "goal-1"
    assert context.trip["trip_id"] == "trip-1"
    assert context.destination == "Tokyo"


def test_conversation_engine_uses_injected_port_for_narrow_intelligence():
    engine = ConversationEngine(
        store=InMemorySessionStore(),
        planning_port=StubPlanningPort(),
    )

    result = asyncio.run(engine.process("Find flights from London to Tokyo"))

    assert result["intent"] == "FLIGHT_SEARCH"
    assert result["conversation_id"]

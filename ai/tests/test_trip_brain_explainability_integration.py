"""
Trip Brain integration — the Explainability Engine runs after merge/
conflict resolution and attaches one explanation block to
UnifiedRecommendation, without changing any module's score or
recommendation (docs/EXPLAINABILITY_ENGINE.md's Trip Brain Integration
section). Mirrors test_trip_brain_coordinator.py's monkeypatched-runner
style so these tests don't depend on the real mock Discovery providers.
"""

from __future__ import annotations

import asyncio

import pytest

from ai.shared.agent_result import AgentResult
from ai.shared.agent_status import AgentStatus
from ai.trip_brain import coordinator as coordinator_module
from ai.trip_brain.context import TripBrainContext
from ai.trip_brain.coordinator import TripBrain

_EXPECTED_KEYS = {
    "summary", "recommendation_drivers", "tradeoffs", "assumptions", "risks",
    "missing_information", "confidence", "confidence_explanation",
    "alternatives_considered", "what_would_change_the_result", "source_modules",
}


def _success(name: str, confidence: float, **data) -> AgentResult:
    return AgentResult(agent_name=f"{name}_intelligence", status=AgentStatus.SUCCESS, confidence=confidence, data=data)


class _StubContextBuilder:
    def __init__(self, context: TripBrainContext) -> None:
        self._context = context

    def build(self, *args, **kwargs) -> TripBrainContext:
        return self._context


FULL_SHAPE_CONTEXT = TripBrainContext(
    traveller_id="t-1",
    trip_id=None,
    goal_id="g-1",
    entities={"destination": "Tokyo", "date_hint": "in october", "nationality": "Nigerian"},
    profile=None,
    goal={"budget": {"max_usd": 3000}, "travellers": {"adults": 2}},
    trip=None,
)


@pytest.fixture
def full_shape_brain() -> TripBrain:
    return TripBrain(context_builder=_StubContextBuilder(FULL_SHAPE_CONTEXT))


class TestExplanationAttached:
    def test_unified_recommendation_carries_full_explanation(self, monkeypatch, full_shape_brain):
        for name in ("flight", "accommodation", "destination", "budget", "visa", "weather"):
            monkeypatch.setitem(coordinator_module.MODULE_RUNNERS, name, lambda ctx, _n=name: _success(_n, 0.8))

        unified = asyncio.run(
            full_shape_brain.plan(traveller_id="t-1", trip_id=None, goal_id="g-1", entities={}, profile=None)
        )
        assert set(unified.explanation.keys()) == _EXPECTED_KEYS
        assert unified.explanation["confidence"] == unified.overall_confidence
        assert unified.destination == "Tokyo"

    def test_explanation_does_not_mutate_module_results(self, monkeypatch, full_shape_brain):
        # A dedicated invariant check: nothing about the Explainability
        # Engine call is allowed to touch AgentResult.confidence or
        # AgentResult.data — it only reads them.
        original = _success("flight", 0.8, top_option={"match_score": 0.8})
        monkeypatch.setitem(coordinator_module.MODULE_RUNNERS, "flight", lambda ctx: original)

        unified = asyncio.run(
            full_shape_brain.plan(traveller_id="t-1", trip_id=None, goal_id="g-1", entities={}, profile=None)
        )
        flight_result = next(r for r in unified.results if r.agent_name == "flight_intelligence")
        assert flight_result.confidence == 0.8
        assert flight_result.data == {"top_option": {"match_score": 0.8}}


class TestPartialFailureVisibility:
    def test_failed_module_visible_in_explanation_risks_and_source_modules(self, monkeypatch, full_shape_brain):
        for name in ("flight", "accommodation", "destination", "budget", "visa"):
            monkeypatch.setitem(coordinator_module.MODULE_RUNNERS, name, lambda ctx, _n=name: _success(_n, 0.8))

        def _weather_boom(ctx):
            raise RuntimeError("timeout")

        monkeypatch.setitem(coordinator_module.MODULE_RUNNERS, "weather", _weather_boom)

        unified = asyncio.run(
            full_shape_brain.plan(traveller_id="t-1", trip_id=None, goal_id="g-1", entities={}, profile=None)
        )
        assert any("weather could not be completed" in r for r in unified.explanation["risks"])
        weather_source = next(
            s for s in unified.explanation["source_modules"] if s["module"] == "weather_intelligence"
        )
        assert weather_source["status"] == "failed"


class TestConflictsPropagateToExplanation:
    def test_budget_accommodation_conflict_surfaces_as_tradeoff(self, monkeypatch, full_shape_brain):
        for name in ("flight", "destination", "visa", "weather"):
            monkeypatch.setitem(coordinator_module.MODULE_RUNNERS, name, lambda ctx, _n=name: _success(_n, 0.8))

        monkeypatch.setitem(
            coordinator_module.MODULE_RUNNERS, "budget",
            lambda ctx: _success("budget", 0.8, top_option={"budget_style": "backpacker"}),
        )
        monkeypatch.setitem(
            coordinator_module.MODULE_RUNNERS, "accommodation",
            lambda ctx: _success("accommodation", 0.8, top_option={"star_rating": 4}),
        )

        unified = asyncio.run(
            full_shape_brain.plan(traveller_id="t-1", trip_id=None, goal_id="g-1", entities={}, profile=None)
        )
        assert len(unified.conflicts) == 1
        assert unified.conflicts[0] in unified.explanation["tradeoffs"]


class TestNoSelectableModules:
    def test_empty_unified_recommendation_has_empty_explanation_shape(self):
        brain = TripBrain()
        unified = asyncio.run(
            brain.plan(traveller_id="t-1", trip_id=None, goal_id=None, entities={}, profile=None)
        )
        assert unified.explanation == {}

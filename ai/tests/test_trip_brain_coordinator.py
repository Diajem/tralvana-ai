"""
Coordinator tests — module selection, parallel execution, partial/total
failure isolation, and confidence aggregation, exercised end-to-end
through TripBrain.plan() with the six module runners monkeypatched so
these tests are independent of the real mock Discovery providers. A stub
ContextBuilder supplies a pre-built TripBrainContext for the "full trip
shape" scenarios, so these tests don't depend on real Goal/Trip
persistence either.
"""

import asyncio
import time

import pytest

from ai.shared.agent_result import AgentResult
from ai.shared.agent_status import AgentStatus
from ai.trip_brain import coordinator as coordinator_module
from ai.trip_brain.context import TripBrainContext
from ai.trip_brain.coordinator import TripBrain


def _success(name: str, confidence: float) -> AgentResult:
    return AgentResult(agent_name=f"{name}_intelligence", status=AgentStatus.SUCCESS, confidence=confidence)


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


@pytest.fixture
def brain() -> TripBrain:
    return TripBrain()


class TestTripBrainPlan:
    def test_no_selectable_modules_returns_empty_recommendation(self, brain):
        unified = asyncio.run(
            brain.plan(traveller_id="t-1", trip_id=None, goal_id=None, entities={}, profile=None)
        )
        assert unified.results == []
        assert unified.modules_selected == []
        assert unified.overall_confidence == 0.0
        assert unified.synthesis_note == ""

    def test_all_modules_succeed(self, monkeypatch, full_shape_brain):
        for name in ("flight", "accommodation", "destination", "budget", "visa", "weather"):
            monkeypatch.setitem(coordinator_module.MODULE_RUNNERS, name, lambda ctx, _n=name: _success(_n, 0.8))

        unified = asyncio.run(
            full_shape_brain.plan(
                traveller_id="t-1", trip_id=None, goal_id="g-1", entities={}, profile=None
            )
        )
        assert set(unified.modules_selected) == {
            "flight", "accommodation", "destination", "budget", "visa", "weather"
        }
        assert set(unified.modules_succeeded) == set(unified.modules_selected)
        assert unified.modules_failed == []
        assert unified.overall_confidence == 0.8
        assert len(unified.results) == 6
        assert "Tokyo" in unified.synthesis_note

    def test_partial_failure_isolates_one_module(self, monkeypatch, full_shape_brain):
        for name in ("flight", "accommodation", "destination", "budget", "visa"):
            monkeypatch.setitem(coordinator_module.MODULE_RUNNERS, name, lambda ctx, _n=name: _success(_n, 0.8))

        def _weather_boom(ctx):
            raise RuntimeError("timeout")

        monkeypatch.setitem(coordinator_module.MODULE_RUNNERS, "weather", _weather_boom)

        unified = asyncio.run(
            full_shape_brain.plan(
                traveller_id="t-1", trip_id=None, goal_id="g-1", entities={}, profile=None
            )
        )
        assert unified.modules_failed == ["weather"]
        assert len(unified.modules_succeeded) == 5
        # Confidence is reduced by the completion penalty (5/6), not zeroed.
        assert 0 < unified.overall_confidence < 0.8
        # The response is still returned — never a hard failure.
        assert len(unified.results) == 6
        weather_result = next(r for r in unified.results if r.agent_name == "weather_intelligence")
        assert weather_result.status == AgentStatus.FAILED

    def test_total_failure_returns_zero_confidence_and_all_failed_results(
        self, monkeypatch, full_shape_brain
    ):
        for name in ("flight", "accommodation", "destination", "budget", "visa", "weather"):
            def _boom(ctx, _name=name):
                raise RuntimeError("down")
            monkeypatch.setitem(coordinator_module.MODULE_RUNNERS, name, _boom)

        unified = asyncio.run(
            full_shape_brain.plan(
                traveller_id="t-1", trip_id=None, goal_id="g-1", entities={}, profile=None
            )
        )
        assert unified.modules_succeeded == []
        assert set(unified.modules_failed) == set(unified.modules_selected)
        assert unified.overall_confidence == 0.0
        assert all(r.status == AgentStatus.FAILED for r in unified.results)

    def test_narrow_destination_only_request_runs_two_modules(self, monkeypatch, brain):
        monkeypatch.setitem(coordinator_module.MODULE_RUNNERS, "destination", lambda ctx: _success("destination", 0.7))
        monkeypatch.setitem(coordinator_module.MODULE_RUNNERS, "weather", lambda ctx: _success("weather", 0.5))

        unified = asyncio.run(
            brain.plan(
                traveller_id="t-1", trip_id=None, goal_id=None,
                # nationality matches destination — isolates this request to
                # the destination-only signal, no Visa trigger.
                entities={"destination": "Lagos", "nationality": "Lagos"}, profile=None,
            )
        )
        assert set(unified.modules_selected) == {"destination", "weather"}
        assert len(unified.results) == 2

    def test_modules_run_concurrently_not_sequentially(self, monkeypatch, full_shape_brain):
        # Each fake runner sleeps; if the coordinator ran them sequentially
        # this test would take ~6x a single module's delay instead of ~1x.
        DELAY = 0.05

        def _slow(name):
            def _runner(ctx):
                time.sleep(DELAY)
                return _success(name, 0.8)
            return _runner

        for name in ("flight", "accommodation", "destination", "budget", "visa", "weather"):
            monkeypatch.setitem(coordinator_module.MODULE_RUNNERS, name, _slow(name))

        start = time.monotonic()
        asyncio.run(
            full_shape_brain.plan(
                traveller_id="t-1", trip_id=None, goal_id="g-1", entities={}, profile=None
            )
        )
        elapsed = time.monotonic() - start
        assert elapsed < DELAY * 3  # comfortably less than sequential (6x)

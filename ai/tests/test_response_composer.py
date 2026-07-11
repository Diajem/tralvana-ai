"""
ResponseComposer's additive extension for Trip Brain: an optional
`synthesis_note` preamble override, and the Total Failure Floor fix (the
"no results" fallback must also fire when every result present is
FAILED, not only when the results list is literally empty).
"""

import pytest

from ai.concierge.decision_engine import Decision
from ai.concierge.intent_classifier import Intent
from ai.concierge.response_composer import ResponseComposer
from ai.shared.agent_result import AgentResult
from ai.shared.agent_status import AgentStatus


@pytest.fixture
def composer() -> ResponseComposer:
    return ResponseComposer()


@pytest.fixture
def ready_decision() -> Decision:
    return Decision(
        has_enough_information=True,
        requires_agents=[],
        follow_up_questions=[],
        is_safety_sensitive=False,
        requires_live_data=True,
        reasoning="ready",
    )


class TestSynthesisNote:
    def test_synthesis_note_replaces_default_preamble(self, composer, ready_decision):
        text = composer.compose(
            Intent.PLAN_TRIP, ready_decision, [], synthesis_note="Custom synthesis sentence."
        )
        assert text.startswith("Custom synthesis sentence.")
        assert "Here's what I've put together for your trip." not in text

    def test_no_synthesis_note_keeps_default_preamble_unchanged(self, composer, ready_decision):
        text = composer.compose(Intent.PLAN_TRIP, ready_decision, [])
        assert text.startswith("Here's what I've put together for your trip.")

    def test_narrow_intent_callers_unaffected_by_new_param(self, composer, ready_decision):
        result = AgentResult(agent_name="flight_intelligence", status=AgentStatus.SUCCESS, confidence=0.8, data={})
        text = composer.compose(Intent.FLIGHT_SEARCH, ready_decision, [result])
        assert text.startswith("Here are your ranked flight options.")


class TestTotalFailureFloor:
    def test_all_failed_results_trigger_no_results_fallback(self, composer, ready_decision):
        results = [
            AgentResult(agent_name="flight_intelligence", status=AgentStatus.FAILED, confidence=0.0),
            AgentResult(agent_name="weather_intelligence", status=AgentStatus.FAILED, confidence=0.0),
        ]
        text = composer.compose(Intent.PLAN_TRIP, ready_decision, results)
        assert "I'll bring in live data for flights, hotels, and pricing" in text

    def test_partial_failure_does_not_trigger_no_results_fallback(self, composer, ready_decision):
        results = [
            AgentResult(agent_name="flight_intelligence", status=AgentStatus.SUCCESS, confidence=0.8, data={
                "count": 1, "origin": "London", "destination": "Tokyo",
                "top_option": {"airline": "AL", "flight_number": "1", "cabin_class": "economy",
                                "stops": 0, "currency": "USD", "estimated_price": 500,
                                "match_score": 0.8, "reasoning": "good"},
            }),
            AgentResult(agent_name="weather_intelligence", status=AgentStatus.FAILED, confidence=0.0),
        ]
        text = composer.compose(Intent.PLAN_TRIP, ready_decision, results)
        assert "I'll bring in live data for flights, hotels, and pricing" not in text
        assert "**Flights:**" in text

    def test_empty_results_still_triggers_fallback(self, composer, ready_decision):
        text = composer.compose(Intent.PLAN_TRIP, ready_decision, [])
        assert "I'll bring in live data for flights, hotels, and pricing" in text

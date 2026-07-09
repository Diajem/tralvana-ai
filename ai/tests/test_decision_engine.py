import pytest

from ai.concierge.decision_engine import DecisionEngine
from ai.concierge.intent_classifier import Intent


@pytest.fixture
def engine() -> DecisionEngine:
    return DecisionEngine()


class TestDecisionEngine:
    def test_plan_trip_without_destination_is_not_ready(self, engine):
        decision = engine.decide(Intent.PLAN_TRIP, {}, None)
        assert not decision.has_enough_information
        assert "Where would you like to go?" in decision.follow_up_questions

    def test_plan_trip_without_date_is_not_ready(self, engine):
        decision = engine.decide(Intent.PLAN_TRIP, {"destination": "Tokyo"}, None)
        assert not decision.has_enough_information
        assert "When are you planning to travel?" in decision.follow_up_questions

    def test_plan_trip_with_full_info_is_ready(self, engine):
        decision = engine.decide(
            Intent.PLAN_TRIP,
            {"destination": "Tokyo", "date_hint": "in october"},
            None,
        )
        assert decision.has_enough_information
        assert len(decision.follow_up_questions) == 0

    def test_plan_trip_dispatches_agents(self, engine):
        decision = engine.decide(
            Intent.PLAN_TRIP,
            {"destination": "Tokyo", "date_hint": "in october"},
            None,
        )
        assert len(decision.requires_agents) > 0
        assert "flight_agent" in decision.requires_agents

    def test_not_ready_means_no_agents(self, engine):
        decision = engine.decide(Intent.PLAN_TRIP, {}, None)
        assert decision.requires_agents == []

    def test_general_conversation_is_always_ready(self, engine):
        decision = engine.decide(Intent.GENERAL_CONVERSATION, {}, None)
        assert decision.has_enough_information
        assert decision.requires_agents == []

    def test_view_profile_is_always_ready(self, engine):
        decision = engine.decide(Intent.VIEW_PROFILE, {}, None)
        assert decision.has_enough_information

    def test_safety_sensitive_destination_flagged(self, engine):
        decision = engine.decide(
            Intent.PLAN_TRIP,
            {"destination": "kabul", "date_hint": "next month"},
            None,
        )
        assert decision.is_safety_sensitive

    def test_safe_destination_not_flagged(self, engine):
        decision = engine.decide(
            Intent.PLAN_TRIP,
            {"destination": "Tokyo", "date_hint": "in october"},
            None,
        )
        assert not decision.is_safety_sensitive

    def test_plan_trip_requires_live_data(self, engine):
        decision = engine.decide(Intent.PLAN_TRIP, {}, None)
        assert decision.requires_live_data

    def test_general_conversation_no_live_data(self, engine):
        decision = engine.decide(Intent.GENERAL_CONVERSATION, {}, None)
        assert not decision.requires_live_data

    def test_no_profile_adds_assumption(self, engine, football_profile):
        decision_no_profile = engine.decide(
            Intent.PLAN_TRIP,
            {"destination": "Tokyo", "date_hint": "in october"},
            None,
        )
        assert any("profile" in a.lower() for a in decision_no_profile.assumptions)

    def test_reasoning_is_non_empty(self, engine):
        decision = engine.decide(Intent.PLAN_TRIP, {}, None)
        assert len(decision.reasoning) > 0

    def test_flight_search_without_destination_is_not_ready(self, engine):
        decision = engine.decide(Intent.FLIGHT_SEARCH, {}, None)
        assert not decision.has_enough_information
        assert "Where would you like to fly to?" in decision.follow_up_questions

    def test_flight_search_with_destination_only_is_ready(self, engine):
        # Unlike PLAN_TRIP, FLIGHT_SEARCH does not require a date_hint —
        # Flight Intelligence defaults the departure date itself.
        decision = engine.decide(Intent.FLIGHT_SEARCH, {"destination": "Tokyo"}, None)
        assert decision.has_enough_information

    def test_flight_search_does_not_dispatch_specialist_agents(self, engine):
        # Routed directly to Flight Intelligence by ConversationEngine, not TravelManager.
        decision = engine.decide(Intent.FLIGHT_SEARCH, {"destination": "Tokyo"}, None)
        assert decision.requires_agents == []

    def test_flight_search_requires_live_data(self, engine):
        decision = engine.decide(Intent.FLIGHT_SEARCH, {"destination": "Tokyo"}, None)
        assert decision.requires_live_data

    def test_accommodation_search_without_destination_is_not_ready(self, engine):
        decision = engine.decide(Intent.ACCOMMODATION_SEARCH, {}, None)
        assert not decision.has_enough_information
        assert "Which destination would you like accommodation for?" in decision.follow_up_questions

    def test_accommodation_search_with_destination_only_is_ready(self, engine):
        # Unlike PLAN_TRIP, ACCOMMODATION_SEARCH does not require a date_hint —
        # Accommodation Intelligence defaults the check-in date itself.
        decision = engine.decide(Intent.ACCOMMODATION_SEARCH, {"destination": "Tokyo"}, None)
        assert decision.has_enough_information

    def test_accommodation_search_does_not_dispatch_specialist_agents(self, engine):
        decision = engine.decide(Intent.ACCOMMODATION_SEARCH, {"destination": "Tokyo"}, None)
        assert decision.requires_agents == []

    def test_accommodation_search_requires_live_data(self, engine):
        decision = engine.decide(Intent.ACCOMMODATION_SEARCH, {"destination": "Tokyo"}, None)
        assert decision.requires_live_data

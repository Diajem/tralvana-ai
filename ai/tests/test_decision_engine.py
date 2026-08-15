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

    def test_country_only_trip_asks_for_a_precise_stay_area(self, engine):
        decision = engine.decide(
            Intent.PLAN_TRIP,
            {"destination": "Jamaica", "date_hint": "September 2026"},
            None,
        )

        assert not decision.has_enough_information
        assert decision.follow_up_questions == [
            "Which city, town, or resort area in Jamaica would you like to stay in?"
        ]

    def test_country_trip_with_named_local_areas_is_ready(self, engine):
        decision = engine.decide(
            Intent.PLAN_TRIP,
            {
                "destination": "Jamaica",
                "local_areas": "St Mary Parish,Ocho Rios",
                "date_hint": "10 October 2026 to 22 October 2026",
            },
            None,
        )

        assert decision.has_enough_information
        assert decision.follow_up_questions == []

    def test_plan_trip_dispatches_agents(self, engine):
        decision = engine.decide(
            Intent.PLAN_TRIP,
            {"destination": "Tokyo", "date_hint": "in october"},
            None,
        )
        assert len(decision.requires_agents) > 0
        assert "flight_intelligence" in decision.requires_agents

    def test_legacy_intents_name_real_intelligence_paths(self, engine):
        assert engine.decide(
            Intent.DESTINATION_QUESTION,
            {"destination": "Tokyo"},
            None,
        ).requires_agents == ["destination_intelligence"]
        assert engine.decide(
            Intent.TRAVEL_ADVICE,
            {"destination": "Tokyo"},
            None,
        ).requires_agents == ["destination_intelligence"]
        assert engine.decide(
            Intent.BUDGET_ADVICE,
            {"destination": "Tokyo"},
            None,
        ).requires_agents == ["budget_intelligence"]

    def test_modify_trip_requires_trip_and_change_details(self, engine):
        decision = engine.decide(Intent.MODIFY_TRIP, {}, None)

        assert not decision.has_enough_information
        assert decision.requires_agents == []
        assert len(decision.follow_up_questions) == 2

    def test_modify_trip_with_context_and_detail_uses_trip_brain(self, engine):
        decision = engine.decide(
            Intent.MODIFY_TRIP,
            {
                "trip_id": "trip-1",
                "destination": "Tokyo",
                "modification_detail": "change my flight to 15 November",
            },
            None,
        )

        assert decision.has_enough_information
        assert decision.requires_agents == ["trip_brain"]

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
        # Routed directly to Flight Intelligence by ConversationEngine.
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

    def test_destination_discovery_is_always_ready_without_destination(self, engine):
        # Unlike the other Discovery intents, DESTINATION_DISCOVERY has a
        # useful "no city" catalogue mode, so it never blocks on missing info.
        decision = engine.decide(Intent.DESTINATION_DISCOVERY, {}, None)
        assert decision.has_enough_information
        assert decision.follow_up_questions == []

    def test_destination_discovery_does_not_dispatch_specialist_agents(self, engine):
        decision = engine.decide(Intent.DESTINATION_DISCOVERY, {}, None)
        assert decision.requires_agents == []

    def test_destination_discovery_requires_live_data(self, engine):
        decision = engine.decide(Intent.DESTINATION_DISCOVERY, {}, None)
        assert decision.requires_live_data

    def test_budget_analysis_is_always_ready_without_destination(self, engine):
        # Same rationale as DESTINATION_DISCOVERY — comparing tiers at
        # default global rates is a useful answer without a destination.
        decision = engine.decide(Intent.BUDGET_ANALYSIS, {}, None)
        assert decision.has_enough_information
        assert decision.follow_up_questions == []

    def test_budget_analysis_does_not_dispatch_specialist_agents(self, engine):
        decision = engine.decide(Intent.BUDGET_ANALYSIS, {}, None)
        assert decision.requires_agents == []

    def test_budget_analysis_requires_live_data(self, engine):
        decision = engine.decide(Intent.BUDGET_ANALYSIS, {}, None)
        assert decision.requires_live_data

    def test_visa_check_without_nationality_or_destination_is_not_ready(self, engine):
        decision = engine.decide(Intent.VISA_CHECK, {}, None)
        assert not decision.has_enough_information
        assert "What is your passport country or nationality?" in decision.follow_up_questions
        assert "Which destination would you like to check entry requirements for?" in decision.follow_up_questions

    def test_visa_check_missing_nationality_only_asks_for_nationality(self, engine):
        decision = engine.decide(Intent.VISA_CHECK, {"destination": "Japan"}, None)
        assert not decision.has_enough_information
        assert decision.follow_up_questions == ["What is your passport country or nationality?"]

    def test_visa_check_missing_destination_only_asks_for_destination(self, engine):
        decision = engine.decide(Intent.VISA_CHECK, {"nationality": "Irish"}, None)
        assert not decision.has_enough_information
        assert decision.follow_up_questions == ["Which destination would you like to check entry requirements for?"]

    def test_visa_check_with_both_entities_is_ready(self, engine):
        decision = engine.decide(Intent.VISA_CHECK, {"nationality": "Irish", "destination": "Japan"}, None)
        assert decision.has_enough_information

    def test_visa_check_does_not_dispatch_specialist_agents(self, engine):
        decision = engine.decide(Intent.VISA_CHECK, {"nationality": "Irish", "destination": "Japan"}, None)
        assert decision.requires_agents == []

    def test_visa_check_requires_live_data(self, engine):
        decision = engine.decide(Intent.VISA_CHECK, {"nationality": "Irish", "destination": "Japan"}, None)
        assert decision.requires_live_data

    def test_weather_analysis_without_destination_is_not_ready(self, engine):
        decision = engine.decide(Intent.WEATHER_ANALYSIS, {}, None)
        assert not decision.has_enough_information
        assert "Which destination would you like a weather and safety assessment for?" in decision.follow_up_questions

    def test_weather_analysis_with_destination_only_is_ready(self, engine):
        # Unlike VISA_CHECK, no month is required — Weather Intelligence
        # finds the best month itself when one isn't supplied.
        decision = engine.decide(Intent.WEATHER_ANALYSIS, {"destination": "Japan"}, None)
        assert decision.has_enough_information

    def test_weather_analysis_does_not_dispatch_specialist_agents(self, engine):
        decision = engine.decide(Intent.WEATHER_ANALYSIS, {"destination": "Japan"}, None)
        assert decision.requires_agents == []

    def test_weather_analysis_requires_live_data(self, engine):
        decision = engine.decide(Intent.WEATHER_ANALYSIS, {"destination": "Japan"}, None)
        assert decision.requires_live_data

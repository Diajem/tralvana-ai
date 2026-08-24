from __future__ import annotations

import asyncio
from types import SimpleNamespace

from ai.concierge.intent_classifier import ClassifiedIntent, Intent
from ai.concierge.conversation_engine import ConversationEngine
from ai.concierge.conversation_session import ConversationSession
from ai.concierge.openai_trip_intelligence import (
    OpenAITripIntelligence,
    PersonalisedDay,
    PersonalisedItinerary,
    TripInterpretation,
    merge_interpretations,
    should_use_openai_interpretation,
)


def _florida_interpretation(**overrides) -> TripInterpretation:
    values = {
        "intent": "PLAN_TRIP",
        "confidence": 0.98,
        "destination": "Orlando",
        "destination_region": "Florida",
        "origin": "London",
        "departure_options": ["London Heathrow", "London Gatwick"],
        "local_areas": ["Orlando"],
        "start_date": "2026-09-10",
        "end_date": "2026-09-20",
        "duration_days": 10,
        "month": 9,
        "travel_year": 2026,
        "departure_day": 10,
        "year_explicit": False,
        "adults": 2,
        "children": 3,
        "infants": 0,
        "minor_ages": [],
        "nationalities": [],
        "budget_amount": None,
        "budget_currency": None,
        "cabin_class": "economy",
        "accommodation_preferences": ["Family-friendly hotel"],
        "interests": [
            "theme parks",
            "water parks",
            "fashion shopping",
            "family dining",
            "history",
        ],
        "requested_activities": [
            "Walt Disney World",
            "Family water park",
            "Victoria's Secret store",
            "Historical family attraction",
        ],
        "requested_event": "Victoria's Secret Fashion Show",
        "requested_event_type": "Fashion show",
        "ticket_requested": True,
        "dining_out_count": 4,
        "baggage_information_requested": True,
        "accessibility_needs": [],
        "special_occasion": None,
        "special_occasion_date": None,
        "special_occasion_notes": None,
        "companion_relationship": None,
        "companion_origin": None,
        "clarification_notes": [
            "Children's ages were not supplied.",
        ],
    }
    values.update(overrides)
    return TripInterpretation(**values)


def _days(count: int) -> list[PersonalisedDay]:
    return [
        PersonalisedDay(
            day=day,
            title=f"Day {day}: Orlando family plan",
            theme="Family discovery",
            morning="A requested family activity",
            afternoon="Rest and a second local activity",
            evening="Family dinner" if day in {2, 4, 6, 9} else "Relaxed evening",
            accommodation="Family-friendly hotel requested, not booked",
            notes="Confirm official opening times and tickets.",
        )
        for day in range(1, count + 1)
    ]


class _FakeResponses:
    def __init__(self, parsed_outputs):
        self._parsed_outputs = list(parsed_outputs)
        self.calls = []

    async def parse(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(output_parsed=self._parsed_outputs.pop(0))


class _FakeClient:
    def __init__(self, *parsed_outputs):
        self.responses = _FakeResponses(parsed_outputs)


def test_florida_brief_becomes_complete_planner_entities():
    result = _florida_interpretation().to_classified_intent()

    assert result.intent == Intent.PLAN_TRIP
    assert result.entities["destination"] == "Orlando"
    assert result.entities["destination_region"] == "Florida"
    assert result.entities["origin"] == "London"
    assert result.entities["start_date"] == "2026-09-10"
    assert result.entities["end_date"] == "2026-09-20"
    assert result.entities["duration_days"] == "10"
    assert result.entities["adults"] == "2"
    assert result.entities["children"] == "3"
    assert result.entities["dining_out_count"] == "4"
    assert result.entities["baggage_information_requested"] == "true"
    assert result.entities["ticket_requested"] == "true"
    assert result.entities["date_inference_note"] == (
        "Year not supplied; using the next occurrence in 2026."
    )
    assert "Walt Disney World" in result.entities["requested_activities"]


def test_relationship_mention_without_distinct_origin_is_not_a_separate_trip():
    result = _florida_interpretation(
        companion_relationship="Wife and three children",
        companion_origin=None,
    ).to_classified_intent()

    assert "companion_relationship" not in result.entities
    assert "companion_origin" not in result.entities


def test_transport_and_dining_do_not_leak_into_requested_activities():
    result = merge_interpretations(
        ClassifiedIntent(Intent.PLAN_TRIP, 0.9, {}),
        _florida_interpretation(
            requested_activities=[
                "connect through a major European hub",
                "hike along the Dolomiti Lucane trails",
                "dine at an authentic family-run trattoria",
            ],
        ).to_classified_intent(),
    )

    assert result.entities["requested_activities"] == (
        "hike along the Dolomiti Lucane trails"
    )
    assert "family-run trattoria" in result.entities["dining_preferences"]


def test_mixed_party_long_stay_visa_is_preserved_per_nationality():
    message = (
        "One Italian national and one Nigerian national currently residing "
        "in Milan on a long-term visa are travelling to Ronda."
    )
    result = merge_interpretations(
        ClassifiedIntent(Intent.PLAN_TRIP, 0.9, {}),
        _florida_interpretation(
            nationalities=["Italian", "Nigerian"],
            country_of_residence="Italy",
        ).to_classified_intent(),
        message=message,
    )

    assert result.entities["residency_documents"] == (
        "Nigerian: Italian long term visa"
    )


def test_equivalent_residency_documents_and_generic_dining_are_deduplicated():
    result = merge_interpretations(
        ClassifiedIntent(
            Intent.PLAN_TRIP,
            0.9,
            {"residency_documents": "Nigerian: Italian long term visa"},
        ),
        _florida_interpretation(
            residency_documents=["Nigerian: Italian long-stay visa"],
            dining_preferences=["traditional tapas bar", "dining together"],
        ).to_classified_intent(),
    )

    assert result.entities["residency_documents"] == (
        "Nigerian: Italian long-stay visa"
    )
    assert result.entities["dining_preferences"] == "traditional tapas bar"


def test_explicit_companion_origin_is_preserved_as_a_separate_trip():
    result = _florida_interpretation(
        companion_relationship="Wife",
        companion_origin="Manchester",
    ).to_classified_intent()

    assert result.entities["companion_relationship"] == "Wife"
    assert result.entities["companion_origin"] == "Manchester"


def test_responses_api_parses_trip_brief_without_storing_provider_response():
    client = _FakeClient(_florida_interpretation())
    intelligence = OpenAITripIntelligence(client=client, model="gpt-5.6")

    result = asyncio.run(
        intelligence.interpret(
            message="Plan our ten-day Florida family holiday",
            existing_entities={},
            history=[],
        )
    )

    assert result is not None
    assert result.entities["destination"] == "Orlando"
    call = client.responses.calls[0]
    assert call["model"] == "gpt-5.6"
    assert call["text_format"] is TripInterpretation
    assert call["reasoning"] == {"effort": "low"}
    assert call["store"] is False


def test_personalised_itinerary_requires_exact_consecutive_day_count():
    invalid = PersonalisedItinerary(
        daily_outline=_days(9),
        planning_notes=[],
    )
    client = _FakeClient(invalid)
    intelligence = OpenAITripIntelligence(client=client, model="gpt-5.6")

    result = asyncio.run(
        intelligence.personalise_itinerary(
            trip_brief={"destination": "Orlando", "duration_days": 10},
            provider_evidence={},
            fallback_outline=[],
        )
    )

    assert result is None


def test_personalised_itinerary_preserves_all_ten_days():
    expected = PersonalisedItinerary(
        daily_outline=_days(10),
        planning_notes=["Baggage allowance must be checked against the selected fare."],
    )
    client = _FakeClient(expected)
    intelligence = OpenAITripIntelligence(client=client, model="gpt-5.6")

    result = asyncio.run(
        intelligence.personalise_itinerary(
            trip_brief={"destination": "Orlando", "duration_days": 10},
            provider_evidence={},
            fallback_outline=[],
        )
    )

    assert result is not None
    assert len(result.daily_outline) == 10
    assert sum("Family dinner" in day.evening for day in result.daily_outline) == 4
    assert client.responses.calls[0]["store"] is False


def test_ai_entities_override_bad_regex_fragments_but_keep_proven_fields():
    rule = ClassifiedIntent(
        intent=Intent.PLAN_TRIP,
        confidence=0.95,
        entities={"destination": "New", "budget_style": "balanced"},
    )
    ai = _florida_interpretation(
        destination="New York",
        destination_region=None,
        start_date="2026-10-10",
        end_date="2026-10-17",
        duration_days=7,
        month=10,
        departure_day=10,
        year_explicit=True,
    ).to_classified_intent()

    merged = merge_interpretations(rule, ai)

    assert merged.entities["destination"] == "New York"
    assert merged.entities["duration_days"] == "7"
    assert merged.entities["budget_style"] == "balanced"


def test_openai_is_used_for_plans_and_active_plan_refinements_not_greetings():
    assert should_use_openai_interpretation(
        rule_intent=Intent.PLAN_TRIP,
        active_goal=None,
        message="Plan a trip",
    )
    assert should_use_openai_interpretation(
        rule_intent=Intent.GENERAL_CONVERSATION,
        active_goal=Intent.PLAN_TRIP.value,
        message="Make that four dinners",
    )
    assert not should_use_openai_interpretation(
        rule_intent=Intent.GENERAL_CONVERSATION,
        active_goal=None,
        message="Hello",
    )


class _RefinementIntelligence:
    async def interpret(self, **kwargs):
        return ClassifiedIntent(
            intent=Intent.MODIFY_TRIP,
            confidence=0.96,
            entities={"dining_out_count": "4"},
        )


def test_active_plan_modification_is_treated_as_a_persisted_replan():
    engine = ConversationEngine(trip_intelligence=_RefinementIntelligence())
    session = ConversationSession(
        conversation_id="conversation-1",
        created_at="2026-08-24T00:00:00+00:00",
        updated_at="2026-08-24T00:00:00+00:00",
        active_goal=Intent.PLAN_TRIP.value,
        planning_entities={"destination": "Orlando"},
    )
    rule = ClassifiedIntent(
        intent=Intent.MODIFY_TRIP,
        confidence=0.85,
        entities={},
    )

    result = asyncio.run(
        engine._interpret_trip_turn(
            session=session,
            message="Change the plan to four family dinners",
            rule_classified=rule,
        )
    )

    assert result.intent == Intent.PLAN_TRIP
    assert result.entities["dining_out_count"] == "4"

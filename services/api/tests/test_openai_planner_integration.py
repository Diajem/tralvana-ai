from __future__ import annotations

from ai.concierge.intent_classifier import ClassifiedIntent, Intent
from ai.concierge.openai_trip_intelligence import (
    PersonalisedDay,
    PersonalisedItinerary,
)


FLORIDA_REQUEST = (
    "plan 10 days trip to Florida for a family of 5, 2 adults and 3 children. "
    "the children would like to visit Disney world and water parks; they would "
    "like to make the journey an unforgettable trip. we would like to fly from "
    "any of the airports in London since we live in London. My wife is interested "
    "in Victoria secreat and would like to attend their show room/shop and also "
    "their fashion show. We would like to dine out as a family 4 times during the "
    "trip and would love to stay in a family-friendly hotel. We would like to know "
    "our baggage allowance and a proper plan for the holiday. Maybe a water park "
    "or water showplace for the kids and a visit to historical places for us as a "
    "family. Traveling out on the 10 of September and would like to spend 10 full "
    "days in Florida."
)


class _FloridaTripIntelligence:
    async def interpret(self, **kwargs):
        assert kwargs["message"] == FLORIDA_REQUEST
        return ClassifiedIntent(
            intent=Intent.PLAN_TRIP,
            confidence=0.99,
            entities={
                "origin": "London",
                "departure_options": (
                    "London Heathrow,London Gatwick,London Stansted,"
                    "London Luton,London City"
                ),
                "destination": "Orlando",
                "destination_region": "Florida",
                "local_areas": "Orlando",
                "start_date": "2026-09-10",
                "end_date": "2026-09-20",
                "duration_days": "10",
                "month": "9",
                "travel_year": "2026",
                "departure_day": "10",
                "date_hint": "10 September 2026",
                "date_precision": "EXACT",
                "date_year_inferred": "true",
                "date_inference_note": "Year not supplied; using 2026.",
                "adults": "2",
                "children": "3",
                "infants": "0",
                "accommodation_preference": "Family-friendly hotel",
                "interests": (
                    "theme parks,water parks,fashion shopping,family dining,history"
                ),
                "requested_activities": (
                    "Walt Disney World,Family water park,Victoria's Secret store,"
                    "Historical family attraction"
                ),
                "requested_event": "Victoria's Secret Fashion Show",
                "requested_event_type": "Fashion show",
                "requested_event_status": "REQUESTED_NOT_CONFIRMED",
                "ticket_requested": "true",
                "dining_out_count": "4",
                "baggage_information_requested": "true",
            },
        )

    async def personalise_itinerary(self, **kwargs):
        assert kwargs["trip_brief"]["duration_days"] == 10
        themes = [
            "Arrival and settle in",
            "Walt Disney World family day",
            "Pool and recovery day",
            "Orlando water park",
            "Central Florida history",
            "Walt Disney World second park",
            "Flexible family morning and shopping",
            "Water attraction alternative",
            "Final family highlights",
            "Departure",
        ]
        dinner_days = {2, 4, 6, 9}
        outline = []
        for day, theme in enumerate(themes, start=1):
            afternoon = "A family activity at a comfortable pace"
            notes = "Confirm official opening times and tickets before booking."
            if day == 2:
                afternoon = "Continue the selected Walt Disney World park visit"
            elif day == 4:
                afternoon = "Visit a selected Orlando water park"
            elif day == 5:
                afternoon = "Choose a family-suitable historical attraction"
            elif day == 7:
                afternoon = "Visit a Victoria's Secret store if the family wants shopping time"
                notes = (
                    "The requested fashion show is not scheduled because no current "
                    "provider listing confirms it."
                )
            elif day == 10:
                afternoon = "Travel to the selected London-bound flight"
                notes = (
                    "Baggage allowance depends on the selected live airline fare; "
                    "check it before payment."
                )
            outline.append(
                PersonalisedDay(
                    day=day,
                    title=f"Day {day}: {theme}",
                    theme=theme,
                    morning="A practical family start",
                    afternoon=afternoon,
                    evening=(
                        "One of four planned family dinners"
                        if day in dinner_days
                        else "Relaxed family evening"
                    ),
                    accommodation="Family-friendly hotel requested, not booked",
                    notes=notes,
                )
            )
        return PersonalisedItinerary(
            daily_outline=outline,
            planning_notes=[
                "Children's ages are still needed for age-specific ticket and pace checks."
            ],
        )


def test_exact_florida_family_request_is_understood_and_adapted(client, monkeypatch):
    from ai.concierge.conversation_engine import conversation_engine

    monkeypatch.setattr(
        conversation_engine,
        "_trip_intelligence",
        _FloridaTripIntelligence(),
    )

    response = client.post("/planner/plan", json={"message": FLORIDA_REQUEST})

    assert response.status_code == 200
    body = response.json()
    assert body["intent"] == "PLAN_TRIP"
    itinerary = body["itinerary"]
    assert itinerary is not None
    brief = itinerary["trip_brief"]
    assert brief["destination"] == "Orlando"
    assert brief["destination_region"] == "Florida"
    assert brief["origin"] == "London"
    assert len(brief["departure_options"]) == 5
    assert brief["start_date"] == "2026-09-10"
    assert brief["end_date"] == "2026-09-20"
    assert brief["duration_days"] == 10
    assert brief["travellers"] == {
        "adults": 2,
        "children": 3,
        "infants": 0,
    }
    assert brief["dining_out_count"] == 4
    assert brief["baggage_information_requested"] is True
    assert brief["accommodation_preferences"] == ["Family-friendly hotel"]
    assert brief["requested_events"][0]["name"] == (
        "Victoria's Secret Fashion Show"
    )
    assert len(itinerary["daily_outline"]) == 10

    outline_text = str(itinerary["daily_outline"])
    assert "Walt Disney World" in outline_text
    assert "water park" in outline_text
    assert "historical attraction" in outline_text
    assert "Victoria's Secret store" in outline_text
    assert outline_text.count("One of four planned family dinners") == 4
    assert "fashion show is not scheduled" in outline_text
    assert "Baggage allowance depends on the selected live airline fare" in outline_text
    assert "openai_trip_intelligence" in itinerary["modules_used"]

    assert itinerary["visa_summary"]["destination_country"] == "United States"
    assert itinerary["weather_expectations"]["destination"] == "Florida"
    assert itinerary["weather_expectations"]["month_of_travel"] == 9

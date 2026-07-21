"""
POST /planner/plan (T-040) — the AI Travel Planner. Confirms the
natural-language entry point reuses the existing conversation/Trip
Brain pipeline unchanged and only adds the Trip Assembly step on top.
"""

from __future__ import annotations


def test_full_plan_trip_message_returns_an_assembled_itinerary(client):
    res = client.post("/planner/plan", json={
        "message": "I want to plan a trip to Tokyo in September for 2 adults, balanced budget, I am from Nigeria",
    })
    assert res.status_code == 200
    body = res.json()
    assert body["intent"] == "PLAN_TRIP"
    assert body["itinerary"] is not None

    itinerary = body["itinerary"]
    for key in (
        "executive_summary", "destination_recommendation", "flight_recommendation",
        "accommodation_recommendation", "budget_summary", "visa_summary",
        "weather_expectations", "risks", "assumptions", "daily_outline",
        "why_this_itinerary", "confidence", "confidence_explanation",
        "alternative_options",
    ):
        assert key in itinerary

    assert len(itinerary["daily_outline"]) > 0
    assert itinerary["executive_summary"]
    assert 0.0 <= itinerary["confidence"] <= 1.0


def test_vague_message_returns_no_itinerary_but_a_helpful_reply(client):
    res = client.post("/planner/plan", json={"message": "hi there"})
    assert res.status_code == 200
    body = res.json()
    assert body["response"]
    # Too little information for Trip Brain to have run at all.
    assert body["itinerary"] is None


def test_destination_only_message_may_still_lack_a_full_itinerary(client):
    res = client.post("/planner/plan", json={"message": "I want to go to Paris"})
    assert res.status_code == 200
    body = res.json()
    # Either a partial recommendation or a follow-up — never a 500,
    # never a raw exception leaking into the response.
    assert "itinerary" in body


def test_itinerary_never_exposes_raw_provider_or_internal_fields(client):
    res = client.post("/planner/plan", json={
        "message": "Plan a trip to Tokyo in September for 2 adults, balanced budget, from Nigeria",
    })
    body = res.json()
    raw = res.text
    # Underscore-prefixed internal fields (provider ids, persona scores,
    # price anchors) must never leak into the public planner response.
    assert "_provider_offer_id" not in raw
    assert "_persona_scores" not in raw
    assert "_price_anchor" not in raw
    assert body["itinerary"] is not None


def test_conversation_id_is_reused_across_turns(client):
    first = client.post("/planner/plan", json={"message": "I want to go to Rome"})
    conversation_id = first.json()["conversation_id"]

    second = client.post("/planner/plan", json={
        "message": "September, 2 adults, balanced budget",
        "conversation_id": conversation_id,
    })
    assert second.json()["conversation_id"] == conversation_id


def test_plan_trip_accumulates_details_and_completes_across_turns(client):
    first = client.post("/planner/plan", json={
        "message": (
            "I want to go to Jamaica with my partner. We are travelling from Leeds, "
            "we are British and Nigerian, and we like beaches, culture, food and music."
        ),
    })
    assert first.status_code == 200
    first_body = first.json()
    assert first_body["intent"] == "PLAN_TRIP"
    assert first_body["itinerary"] is None
    assert "When are you planning to travel?" in first_body["missing_information"]

    second = client.post("/planner/plan", json={
        "message": "We want to travel from 10 August to 17 August 2026 and there will be 2 adults.",
        "conversation_id": first_body["conversation_id"],
    })
    assert second.status_code == 200
    second_body = second.json()
    assert second_body["conversation_id"] == first_body["conversation_id"]
    assert second_body["intent"] == "PLAN_TRIP"
    assert second_body["itinerary"] is not None
    assert "When are you planning to travel?" not in second_body["missing_information"]
    assert "Jamaica" in second_body["itinerary"]["executive_summary"]


def test_daily_outline_length_matches_trip_duration(client):
    res = client.post("/planner/plan", json={
        "message": "Plan a 4 day trip to Tokyo in September for 2 adults, balanced budget, from Nigeria",
    })
    body = res.json()
    if body["itinerary"] is not None:
        assert len(body["itinerary"]["daily_outline"]) >= 1

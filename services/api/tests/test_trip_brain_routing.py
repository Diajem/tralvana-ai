"""
PLAN_TRIP routing through Trip Brain, and narrow-intent regression —
docs/ADR/ADR-017-trip-brain.md's central guarantee: narrow, single-domain
intents are untouched by construction (they never reach TripBrain or
TravelManager), while PLAN_TRIP now reaches the six real Discovery
modules instead of the Sprint-1 placeholder agents.
"""


def test_plan_trip_synthesizes_across_multiple_modules(client):
    res = client.post("/conversation/message", json={
        "message": "I want to plan a trip to Tokyo in October",
    })
    body = res.json()
    assert body["intent"] == "PLAN_TRIP"
    # Real Discovery module sections, not Sprint-1 placeholder agent output.
    assert "**Flights:**" in body["response"]
    assert "**Accommodation:**" in body["response"]
    assert "**Weather:**" in body["response"]
    assert "**Destinations:**" in body["response"]
    assert "Here's what I found for your Tokyo trip" in body["response"]
    assert 0.0 <= body["confidence"] <= 1.0


def test_plan_trip_no_longer_returns_placeholder_agent_sections(client):
    res = client.post("/conversation/message", json={
        "message": "I want to plan a trip to Tokyo in October",
    })
    body = res.json()
    # Sprint-1 placeholder phrasing ("Live pricing available in Sprint 4"
    # per-section, from flight_agent/hotel_agent) must not appear — Trip
    # Brain calls the real Discovery modules, not TravelManager, for
    # PLAN_TRIP.
    assert "Live pricing available in Sprint 4." not in body["response"]


def test_plan_trip_without_enough_information_still_asks_clarifying_questions(client):
    res = client.post("/conversation/message", json={
        "message": "I want to go somewhere",
    })
    body = res.json()
    assert body["intent"] == "PLAN_TRIP"
    assert body["missing_information"] != []


def test_plan_trip_response_includes_recommended_agents_field_for_rollback_visibility(client):
    # requires_agents (TravelManager's dispatch list) is still computed by
    # DecisionEngine unchanged and surfaced, even though PLAN_TRIP no
    # longer dispatches through it — this is a read-only, informational
    # field, not evidence TravelManager ran.
    res = client.post("/conversation/message", json={
        "message": "I want to plan a trip to Tokyo in October",
    })
    body = res.json()
    assert "flight_agent" in body["recommended_agents"]


class TestNarrowIntentRegression:
    """Every narrow, single-domain intent must behave exactly as it did
    before Trip Brain existed — none of them route through TripBrain."""

    def test_flight_search_unaffected(self, client):
        res = client.post("/conversation/message", json={
            "message": "recommend flights to Tokyo",
        })
        body = res.json()
        assert body["intent"] == "FLIGHT_SEARCH"
        assert "**Flights:**" in body["response"]
        assert "Here's what I found for your" not in body["response"]

    def test_accommodation_search_unaffected(self, client):
        res = client.post("/conversation/message", json={
            "message": "find hotels in Tokyo",
        })
        body = res.json()
        assert body["intent"] == "ACCOMMODATION_SEARCH"
        assert "**Accommodation:**" in body["response"]

    def test_destination_discovery_unaffected(self, client):
        res = client.post("/conversation/message", json={
            "message": "where should i go",
        })
        assert res.json()["intent"] == "DESTINATION_DISCOVERY"

    def test_budget_analysis_unaffected(self, client):
        res = client.post("/conversation/message", json={
            "message": "compare budget options in Tokyo",
        })
        assert res.json()["intent"] == "BUDGET_ANALYSIS"

    def test_visa_check_unaffected(self, client):
        res = client.post("/conversation/message", json={
            "message": "Will my Irish passport work in Japan?",
        })
        assert res.json()["intent"] == "VISA_CHECK"

    def test_weather_analysis_unaffected(self, client):
        res = client.post("/conversation/message", json={
            "message": "Is July a good time to visit Japan?",
        })
        assert res.json()["intent"] == "WEATHER_ANALYSIS"

    def test_modify_trip_still_uses_legacy_travel_manager_path(self, client):
        # MODIFY_TRIP is explicitly out of scope for T-022 — only PLAN_TRIP
        # is repointed at Trip Brain (docs/ADR/ADR-017-trip-brain.md).
        res = client.post("/conversation/message", json={
            "message": "I need to change my trip",
        })
        body = res.json()
        assert body["intent"] == "MODIFY_TRIP"
        assert "Sprint 4" in body["response"]

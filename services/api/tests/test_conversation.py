def test_conversation_returns_200(client):
    res = client.post("/conversation/message", json={
        "message": "I want to travel to Tokyo",
    })
    assert res.status_code == 200


def test_conversation_detects_plan_trip_intent(client):
    res = client.post("/conversation/message", json={
        "message": "I want to plan a trip to Japan",
    })
    body = res.json()
    assert body["intent"] == "PLAN_TRIP"
    assert body["confidence"] > 0


def test_conversation_returns_required_fields(client):
    res = client.post("/conversation/message", json={
        "message": "Hello, can you help me?",
    })
    body = res.json()
    assert "conversation_id" in body
    assert "intent" in body
    assert "response" in body
    assert "confidence" in body
    assert "assumptions" in body
    assert "missing_information" in body
    assert "next_actions" in body
    assert "recommended_agents" in body


def test_conversation_general_intent_for_greeting(client):
    res = client.post("/conversation/message", json={
        "message": "Hello there",
    })
    assert res.json()["intent"] == "GENERAL_CONVERSATION"


def test_conversation_flight_search_intent(client):
    res = client.post("/conversation/message", json={
        "message": "recommend flights to Tokyo",
    })
    body = res.json()
    assert body["intent"] == "FLIGHT_SEARCH"
    assert "Flights" in body["response"]


def test_conversation_flight_search_without_destination_asks_for_it(client):
    res = client.post("/conversation/message", json={
        "message": "find me flights",
    })
    body = res.json()
    assert body["intent"] == "FLIGHT_SEARCH"
    assert "Where would you like to fly to?" in body["missing_information"]


def test_conversation_accommodation_search_intent(client):
    res = client.post("/conversation/message", json={
        "message": "find hotels in Tokyo",
    })
    body = res.json()
    assert body["intent"] == "ACCOMMODATION_SEARCH"
    assert "Accommodation" in body["response"]


def test_conversation_accommodation_search_without_destination_asks_for_it(client):
    res = client.post("/conversation/message", json={
        "message": "find me a place to stay",
    })
    body = res.json()
    assert body["intent"] == "ACCOMMODATION_SEARCH"
    assert "Which destination would you like accommodation for?" in body["missing_information"]


def test_conversation_destination_discovery_intent(client):
    res = client.post("/conversation/message", json={
        "message": "where should i go",
    })
    body = res.json()
    assert body["intent"] == "DESTINATION_DISCOVERY"
    assert "Destinations" in body["response"]


def test_conversation_destination_discovery_without_city_still_ready(client):
    # Unlike flights/accommodation, no city is required — catalogue mode is useful on its own.
    res = client.post("/conversation/message", json={
        "message": "recommend a destination",
    })
    body = res.json()
    assert body["intent"] == "DESTINATION_DISCOVERY"
    assert body["missing_information"] == []


def test_conversation_destination_discovery_with_city(client):
    res = client.post("/conversation/message", json={
        "message": "things to do in Tokyo",
    })
    body = res.json()
    assert body["intent"] == "DESTINATION_DISCOVERY"
    assert "Tokyo" in body["response"]


def test_conversation_budget_analysis_intent(client):
    res = client.post("/conversation/message", json={
        "message": "compare budget options in Tokyo",
    })
    body = res.json()
    assert body["intent"] == "BUDGET_ANALYSIS"
    assert "Budget" in body["response"]


def test_conversation_budget_analysis_without_destination_still_ready(client):
    res = client.post("/conversation/message", json={
        "message": "recommend a budget for my trip",
    })
    body = res.json()
    assert body["intent"] == "BUDGET_ANALYSIS"
    assert body["missing_information"] == []


def test_conversation_visa_check_intent(client):
    res = client.post("/conversation/message", json={
        "message": "Will my Irish passport work in Japan?",
    })
    body = res.json()
    assert body["intent"] == "VISA_CHECK"
    assert "Visa" in body["response"]


def test_conversation_visa_check_missing_info_asks_for_it(client):
    res = client.post("/conversation/message", json={
        "message": "Do I need a visa?",
    })
    body = res.json()
    assert body["intent"] == "VISA_CHECK"
    assert "What is your passport country or nationality?" in body["missing_information"]


def test_conversation_visa_check_nationality_and_destination_statement(client):
    res = client.post("/conversation/message", json={
        "message": "I am Nigerian travelling to Spain.",
    })
    body = res.json()
    assert body["intent"] == "VISA_CHECK"
    assert body["missing_information"] == []
    assert "Spain" in body["response"]


def test_conversation_weather_analysis_intent(client):
    res = client.post("/conversation/message", json={
        "message": "Is July a good time to visit Japan?",
    })
    body = res.json()
    assert body["intent"] == "WEATHER_ANALYSIS"
    assert "Weather" in body["response"]


def test_conversation_weather_analysis_missing_destination_asks_for_it(client):
    res = client.post("/conversation/message", json={
        "message": "Should I avoid hurricane season?",
    })
    body = res.json()
    assert body["intent"] == "WEATHER_ANALYSIS"
    assert "Which destination would you like a weather and safety assessment for?" in body["missing_information"]


def test_conversation_weather_analysis_without_month_still_ready(client):
    res = client.post("/conversation/message", json={
        "message": "When should I visit Spain?",
    })
    body = res.json()
    assert body["intent"] == "WEATHER_ANALYSIS"
    assert body["missing_information"] == []


def test_conversation_preserves_session(client):
    first = client.post("/conversation/message", json={
        "message": "I want to visit London",
    }).json()
    conversation_id = first["conversation_id"]

    second = client.post("/conversation/message", json={
        "message": "What about the weather?",
        "conversation_id": conversation_id,
    }).json()
    assert second["conversation_id"] == conversation_id

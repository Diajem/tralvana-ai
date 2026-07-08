def test_recommend_flights_returns_201(client):
    res = client.post("/flights/recommend", json={
        "origin": "London",
        "destination": "Tokyo",
        "departure_date": "2026-09-15",
        "return_date": "2026-09-25",
        "cabin_class": "economy",
        "budget_style": "balanced",
    })
    assert res.status_code == 201
    body = res.json()
    assert len(body["flight_options"]) > 0
    assert body["destination"] == "Tokyo"


def test_recommend_flights_options_are_ranked(client):
    res = client.post("/flights/recommend", json={
        "origin": "London",
        "destination": "Dubai",
        "cabin_class": "business",
        "budget_style": "comfort",
    })
    scores = [f["match_score"] for f in res.json()["flight_options"]]
    assert scores == sorted(scores, reverse=True)


def test_recommend_flights_have_match_score_and_reasoning(client):
    res = client.post("/flights/recommend", json={
        "origin": "London",
        "destination": "Lagos",
    })
    for option in res.json()["flight_options"]:
        assert 0.0 <= option["match_score"] <= 1.0
        assert option["reasoning"]
        assert option["recommendation_type"] in {
            "BEST_OVERALL", "LOWEST_PRICE", "SHORTEST_DURATION", "BEST_FOR_FAMILY",
            "BEST_FOR_BUSINESS", "BEST_FOR_COMFORT", "BEST_FOR_BUDGET", "AVOID",
        }


def test_get_flight_option_returns_200(client):
    create_res = client.post("/flights/recommend", json={
        "origin": "London",
        "destination": "Paris",
    })
    flight_id = create_res.json()["flight_options"][0]["flight_option_id"]

    get_res = client.get(f"/flights/{flight_id}")
    assert get_res.status_code == 200
    assert get_res.json()["flight_option_id"] == flight_id


def test_get_unknown_flight_returns_404(client):
    res = client.get("/flights/does-not-exist")
    assert res.status_code == 404


def test_list_trip_flights_returns_saved_options(client):
    create_res = client.post("/flights/recommend", json={
        "trip_id": "trip-flights-test-001",
        "origin": "London",
        "destination": "Barcelona",
    })
    option_count = len(create_res.json()["flight_options"])

    list_res = client.get("/trips/trip-flights-test-001/flights")
    assert list_res.status_code == 200
    assert len(list_res.json()) == option_count


def test_list_trip_flights_empty_for_unknown_trip(client):
    res = client.get("/trips/no-flights-here/flights")
    assert res.status_code == 200
    assert res.json() == []


def test_recommend_flights_with_traveller_profile(client, sample_profile):
    profile = client.post("/traveller/profile", json=sample_profile).json()
    res = client.post("/flights/recommend", json={
        "traveller_id": profile["id"],
        "origin": "London",
        "destination": "Rome",
        "cabin_class": "economy",
    })
    assert res.status_code == 201
    assert res.json()["traveller_id"] == profile["id"]

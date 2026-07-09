def test_recommend_accommodation_returns_201(client):
    res = client.post("/accommodation/recommend", json={
        "destination": "Tokyo",
        "check_in_date": "2026-09-15",
        "nights": 5,
        "budget_style": "balanced",
    })
    assert res.status_code == 201
    body = res.json()
    assert len(body["accommodation_options"]) > 0
    assert body["destination"] == "Tokyo"


def test_recommend_accommodation_options_are_ranked(client):
    res = client.post("/accommodation/recommend", json={
        "destination": "Dubai",
        "budget_style": "comfort",
    })
    scores = [a["match_score"] for a in res.json()["accommodation_options"]]
    assert scores == sorted(scores, reverse=True)


def test_recommend_accommodation_have_match_score_and_reasoning(client):
    res = client.post("/accommodation/recommend", json={
        "destination": "Lagos",
    })
    for option in res.json()["accommodation_options"]:
        assert 0.0 <= option["match_score"] <= 1.0
        assert option["reasoning"]
        assert option["recommendation_type"] in {
            "BEST_OVERALL", "BEST_VALUE", "BEST_LOCATION", "BEST_COMFORT",
            "BEST_FOR_FAMILY", "BEST_FOR_BUSINESS", "BEST_BUDGET", "AVOID",
        }


def test_recommend_accommodation_types_are_unique(client):
    res = client.post("/accommodation/recommend", json={"destination": "Paris"})
    types = [a["recommendation_type"] for a in res.json()["accommodation_options"]]
    assert len(types) == len(set(types))


def test_get_accommodation_option_returns_200(client):
    create_res = client.post("/accommodation/recommend", json={"destination": "Paris"})
    option_id = create_res.json()["accommodation_options"][0]["accommodation_option_id"]

    get_res = client.get(f"/accommodation/{option_id}")
    assert get_res.status_code == 200
    assert get_res.json()["accommodation_option_id"] == option_id


def test_get_unknown_accommodation_returns_404(client):
    res = client.get("/accommodation/does-not-exist")
    assert res.status_code == 404


def test_list_trip_accommodation_returns_saved_options(client):
    create_res = client.post("/accommodation/recommend", json={
        "trip_id": "trip-accommodation-test-001",
        "destination": "Barcelona",
    })
    option_count = len(create_res.json()["accommodation_options"])

    list_res = client.get("/trips/trip-accommodation-test-001/accommodation")
    assert list_res.status_code == 200
    assert len(list_res.json()) == option_count


def test_list_trip_accommodation_empty_for_unknown_trip(client):
    res = client.get("/trips/no-accommodation-here/accommodation")
    assert res.status_code == 200
    assert res.json() == []


def test_recommend_accommodation_with_traveller_profile(client, sample_profile):
    profile = client.post("/traveller/profile", json=sample_profile).json()
    res = client.post("/accommodation/recommend", json={
        "traveller_id": profile["id"],
        "destination": "Rome",
    })
    assert res.status_code == 201
    assert res.json()["traveller_id"] == profile["id"]


def test_recommend_accommodation_with_family_and_business_flags(client):
    res = client.post("/accommodation/recommend", json={
        "destination": "London",
        "children": 2,
        "business_trip": True,
        "accessibility_required": True,
    })
    assert res.status_code == 201

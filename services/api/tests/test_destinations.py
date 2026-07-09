def test_recommend_destinations_returns_201(client):
    res = client.post("/destinations/recommend", json={
        "city": "Tokyo",
        "interests": ["food", "culture"],
        "budget_style": "balanced",
    })
    assert res.status_code == 201
    body = res.json()
    assert len(body["destination_options"]) > 0
    assert body["city"] == "Tokyo"


def test_recommend_destinations_without_city_returns_catalogue(client):
    res = client.post("/destinations/recommend", json={})
    assert res.status_code == 201
    body = res.json()
    assert len(body["destination_options"]) == 10
    assert all(d["destination_type"] == "CITY" for d in body["destination_options"])


def test_recommend_destinations_options_are_ranked(client):
    res = client.post("/destinations/recommend", json={"city": "Barcelona"})
    scores = [d["match_score"] for d in res.json()["destination_options"]]
    assert scores == sorted(scores, reverse=True)


def test_recommend_destinations_have_match_score_and_reasoning(client):
    res = client.post("/destinations/recommend", json={"city": "Lagos"})
    for option in res.json()["destination_options"]:
        assert 0.0 <= option["match_score"] <= 1.0
        assert option["reasoning"]
        assert option["recommendation_type"] in {
            "BEST_OVERALL", "BEST_FOR_FOOD", "BEST_FOR_FOOTBALL", "BEST_FOR_CULTURE",
            "BEST_FOR_FAMILY", "BEST_FOR_BUDGET", "BEST_FOR_PHOTOGRAPHY", "BEST_HIDDEN_GEM", "AVOID",
        }


def test_recommend_destinations_city_mode_types_are_unique(client):
    res = client.post("/destinations/recommend", json={"city": "Paris"})
    types = [d["recommendation_type"] for d in res.json()["destination_options"]]
    assert len(types) == len(set(types))


def test_get_destination_option_returns_200(client):
    create_res = client.post("/destinations/recommend", json={"city": "Osaka"})
    option_id = create_res.json()["destination_options"][0]["destination_option_id"]

    get_res = client.get(f"/destinations/{option_id}")
    assert get_res.status_code == 200
    assert get_res.json()["destination_option_id"] == option_id


def test_get_unknown_destination_returns_404(client):
    res = client.get("/destinations/does-not-exist")
    assert res.status_code == 404


def test_list_trip_destinations_returns_saved_options(client):
    create_res = client.post("/destinations/recommend", json={
        "trip_id": "trip-destinations-test-001",
        "city": "Kingston",
    })
    option_count = len(create_res.json()["destination_options"])

    list_res = client.get("/trips/trip-destinations-test-001/destinations")
    assert list_res.status_code == 200
    assert len(list_res.json()) == option_count


def test_list_trip_destinations_empty_for_unknown_trip(client):
    res = client.get("/trips/no-destinations-here/destinations")
    assert res.status_code == 200
    assert res.json() == []


def test_recommend_destinations_with_traveller_profile(client, sample_profile):
    profile = client.post("/traveller/profile", json=sample_profile).json()
    res = client.post("/destinations/recommend", json={
        "traveller_id": profile["id"],
        "city": "Accra",
    })
    assert res.status_code == 201
    assert res.json()["traveller_id"] == profile["id"]


def test_recommend_destinations_unknown_city_returns_empty_options(client):
    res = client.post("/destinations/recommend", json={"city": "Atlantis"})
    assert res.status_code == 201
    assert res.json()["destination_options"] == []

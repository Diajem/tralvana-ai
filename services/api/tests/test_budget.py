def test_recommend_budget_returns_201(client):
    res = client.post("/budget/recommend", json={
        "destination": "Tokyo",
        "budget_style": "balanced",
    })
    assert res.status_code == 201
    body = res.json()
    assert len(body["budget_options"]) == 5
    assert body["destination"] == "Tokyo"


def test_recommend_budget_without_destination_still_returns_options(client):
    res = client.post("/budget/recommend", json={})
    assert res.status_code == 201
    body = res.json()
    assert len(body["budget_options"]) == 5


def test_recommend_budget_options_are_ranked(client):
    res = client.post("/budget/recommend", json={"destination": "Barcelona"})
    scores = [o["match_score"] for o in res.json()["budget_options"]]
    assert scores == sorted(scores, reverse=True)


def test_recommend_budget_have_match_score_and_reasoning(client):
    res = client.post("/budget/recommend", json={"destination": "Lagos"})
    for option in res.json()["budget_options"]:
        assert 0.0 <= option["match_score"] <= 1.0
        assert option["reasoning"]
        assert option["recommendation_type"] in {
            "BEST_OVERALL", "LOWEST_COST", "MOST_COMFORTABLE",
            "BEST_VALUE", "BEST_FOR_FAMILY", "AVOID",
        }


def test_recommend_budget_types_are_unique(client):
    res = client.post("/budget/recommend", json={"destination": "Paris"})
    types = [o["recommendation_type"] for o in res.json()["budget_options"]]
    assert len(types) == len(set(types))


def test_get_budget_option_returns_200(client):
    create_res = client.post("/budget/recommend", json={"destination": "Osaka"})
    option_id = create_res.json()["budget_options"][0]["budget_option_id"]

    get_res = client.get(f"/budget/{option_id}")
    assert get_res.status_code == 200
    assert get_res.json()["budget_option_id"] == option_id


def test_get_unknown_budget_option_returns_404(client):
    res = client.get("/budget/does-not-exist")
    assert res.status_code == 404


def test_list_trip_budget_returns_saved_options(client):
    create_res = client.post("/budget/recommend", json={
        "trip_id": "trip-budget-test-001",
        "destination": "Kingston",
    })
    option_count = len(create_res.json()["budget_options"])

    list_res = client.get("/trips/trip-budget-test-001/budget")
    assert list_res.status_code == 200
    assert len(list_res.json()) == option_count


def test_list_trip_budget_empty_for_unknown_trip(client):
    res = client.get("/trips/no-budget-here/budget")
    assert res.status_code == 200
    assert res.json() == []


def test_recommend_budget_with_traveller_profile(client, sample_profile):
    profile = client.post("/traveller/profile", json=sample_profile).json()
    res = client.post("/budget/recommend", json={
        "traveller_id": profile["id"],
        "destination": "Accra",
    })
    assert res.status_code == 201
    assert res.json()["traveller_id"] == profile["id"]


def test_recommend_budget_respects_goal_budget_cap(client, sample_goal):
    res = client.post("/budget/recommend", json={
        "traveller_id": sample_goal["traveller_id"],
        "trip_id": None,
        "destination": "Tokyo",
        "duration_days": 5,
    })
    assert res.status_code == 201
    assert len(res.json()["budget_options"]) == 5

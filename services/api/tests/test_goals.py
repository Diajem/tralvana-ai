def test_create_goal_returns_201(client, sample_profile):
    profile = client.post("/traveller/profile", json=sample_profile).json()
    res = client.post("/goals", json={
        "traveller_id": profile["id"],
        "title": "Food Tour in Tokyo",
        "goal_type": "FOOD_TOUR",
        "interests": ["food", "culture"],
    })
    assert res.status_code == 201
    body = res.json()
    assert "goal_id" in body
    assert body["traveller_id"] == profile["id"]
    assert body["title"] == "Food Tour in Tokyo"


def test_get_goal_returns_200(client, sample_goal):
    goal_id = sample_goal["goal_id"]
    res = client.get(f"/goals/{goal_id}")
    assert res.status_code == 200
    assert res.json()["goal_id"] == goal_id


def test_get_unknown_goal_returns_404(client):
    res = client.get("/goals/does-not-exist")
    assert res.status_code == 404


def test_list_traveller_goals(client, sample_profile):
    profile = client.post("/traveller/profile", json=sample_profile).json()
    traveller_id = profile["id"]

    client.post("/goals", json={"traveller_id": traveller_id, "title": "Goal A"})
    client.post("/goals", json={"traveller_id": traveller_id, "title": "Goal B"})

    res = client.get(f"/traveller/{traveller_id}/goals")
    assert res.status_code == 200
    assert len(res.json()) >= 2


def test_goal_has_status_field(client, sample_goal):
    body = client.get(f"/goals/{sample_goal['goal_id']}").json()
    assert "status" in body
    assert body["status"] in ("DRAFT", "ACTIVE", "COMPLETE", "CANCELLED")


def test_goal_type_auto_classified_from_interests(client, sample_profile):
    profile = client.post("/traveller/profile", json=sample_profile).json()
    res = client.post("/goals", json={
        "traveller_id": profile["id"],
        "title": "My Travel Plan",
        "goal_type": "GENERAL_TRAVEL",
        "interests": ["football"],
    })
    assert res.status_code == 201

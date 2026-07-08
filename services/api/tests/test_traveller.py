def test_create_profile_returns_201(client, sample_profile):
    res = client.post("/traveller/profile", json=sample_profile)
    assert res.status_code == 201
    body = res.json()
    assert "id" in body
    assert body["identity"]["name"] == "Test Traveller"


def test_get_profile_returns_200(client, sample_profile):
    create_res = client.post("/traveller/profile", json=sample_profile)
    traveller_id = create_res.json()["id"]

    get_res = client.get(f"/traveller/profile/{traveller_id}")
    assert get_res.status_code == 200
    assert get_res.json()["id"] == traveller_id


def test_get_unknown_profile_returns_404(client):
    res = client.get("/traveller/profile/does-not-exist")
    assert res.status_code == 404


def test_create_profile_stores_preferences(client, sample_profile):
    res = client.post("/traveller/profile", json=sample_profile)
    body = res.json()
    assert body["preferences"]["cabin_class"] == "economy"
    assert body["preferences"]["budget_style"] == "moderate"

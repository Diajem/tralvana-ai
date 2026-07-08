def test_plan_trip_returns_201(client, sample_profile):
    profile = client.post("/traveller/profile", json=sample_profile).json()
    res = client.post("/trips/plan", json={
        "traveller_id": profile["id"],
        "origin": "London",
        "destination": "Tokyo",
        "duration_days": 7,
        "budget_style": "moderate",
        "cabin_class": "economy",
        "adults": 1,
        "children": 0,
        "interests": ["culture", "food"],
    })
    assert res.status_code == 201
    body = res.json()
    assert "trip_id" in body
    assert body["destination"] == "Tokyo"


def test_trip_plan_has_itinerary(client, sample_profile):
    profile = client.post("/traveller/profile", json=sample_profile).json()
    res = client.post("/trips/plan", json={
        "traveller_id": profile["id"],
        "origin": "Manchester",
        "destination": "Paris",
        "duration_days": 5,
        "budget_style": "budget",
        "cabin_class": "economy",
        "adults": 2,
        "children": 0,
        "interests": ["culture"],
    })
    body = res.json()
    assert len(body["draft_itinerary"]) == 5


def test_trip_plan_has_budget_breakdown(client, sample_profile):
    profile = client.post("/traveller/profile", json=sample_profile).json()
    res = client.post("/trips/plan", json={
        "traveller_id": profile["id"],
        "origin": "London",
        "destination": "Dubai",
        "duration_days": 4,
        "budget_style": "luxury",
        "cabin_class": "business",
        "adults": 1,
        "children": 0,
        "interests": ["luxury"],
    })
    body = res.json()
    assert "estimated_budget_breakdown" in body
    assert body["estimated_budget_breakdown"]["total_estimate_usd"] > 0


def test_get_trip_returns_200(client, sample_profile):
    profile = client.post("/traveller/profile", json=sample_profile).json()
    create_res = client.post("/trips/plan", json={
        "traveller_id": profile["id"],
        "origin": "London",
        "destination": "Barcelona",
        "duration_days": 3,
        "budget_style": "moderate",
        "cabin_class": "economy",
        "adults": 1,
        "children": 0,
        "interests": ["culture"],
    })
    trip_id = create_res.json()["trip_id"]

    get_res = client.get(f"/trips/{trip_id}")
    assert get_res.status_code == 200
    assert get_res.json()["trip_id"] == trip_id


def test_get_unknown_trip_returns_404(client):
    res = client.get("/trips/does-not-exist")
    assert res.status_code == 404


def test_trip_confidence_is_float(client, sample_profile):
    profile = client.post("/traveller/profile", json=sample_profile).json()
    res = client.post("/trips/plan", json={
        "traveller_id": profile["id"],
        "origin": "London",
        "destination": "Rome",
        "duration_days": 6,
        "budget_style": "moderate",
        "cabin_class": "economy",
        "adults": 1,
        "children": 0,
        "interests": ["history"],
    })
    confidence = res.json()["confidence"]
    assert isinstance(confidence, float)
    assert 0.0 <= confidence <= 1.0

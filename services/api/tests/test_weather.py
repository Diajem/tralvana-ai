def test_analyse_weather_returns_201(client):
    res = client.post("/weather/analyse", json={
        "destination": "Japan",
        "month_of_travel": 4,
    })
    assert res.status_code == 201
    body = res.json()
    assert body["destination"] == "Japan"
    assert body["month_of_travel"] == 4


def test_analyse_weather_requires_destination(client):
    res = client.post("/weather/analyse", json={})
    assert res.status_code == 422


def test_analyse_weather_without_month_finds_best_month(client):
    res = client.post("/weather/analyse", json={"destination": "Spain"})
    assert res.status_code == 201
    body = res.json()
    assert 1 <= body["month_of_travel"] <= 12
    assert any("best month" in a.lower() for a in body["assumptions"])


def test_analyse_weather_has_explanation_and_recommendation(client):
    res = client.post("/weather/analyse", json={"destination": "Nigeria", "month_of_travel": 8})
    body = res.json()
    assert body["explanation"]
    assert body["recommendation"]
    assert 0.0 <= body["confidence"] <= 1.0
    assert 0.0 <= body["weather_suitability_score"] <= 1.0


def test_analyse_weather_status_is_a_valid_enum_value(client):
    res = client.post("/weather/analyse", json={"destination": "UAE", "month_of_travel": 7})
    assert res.json()["weather_status"] in {
        "EXCELLENT", "GOOD", "ACCEPTABLE", "CHALLENGING", "NOT_RECOMMENDED",
    }


def test_analyse_weather_month_out_of_range_returns_422(client):
    res = client.post("/weather/analyse", json={"destination": "Japan", "month_of_travel": 13})
    assert res.status_code == 422


def test_analyse_weather_returns_packing_recommendations(client):
    res = client.post("/weather/analyse", json={"destination": "UK", "month_of_travel": 12})
    body = res.json()
    assert len(body["packing_recommendations"]) > 0


def test_analyse_weather_unknown_destination_still_returns_201(client):
    res = client.post("/weather/analyse", json={"destination": "Atlantis", "month_of_travel": 5})
    assert res.status_code == 201
    assert res.json()["confidence"] < 0.5


def test_get_weather_assessment_returns_200(client):
    create_res = client.post("/weather/analyse", json={"destination": "France", "month_of_travel": 6})
    assessment_id = create_res.json()["weather_assessment_id"]

    get_res = client.get(f"/weather/{assessment_id}")
    assert get_res.status_code == 200
    assert get_res.json()["weather_assessment_id"] == assessment_id


def test_get_unknown_weather_assessment_returns_404(client):
    res = client.get("/weather/does-not-exist")
    assert res.status_code == 404


def test_list_trip_weather_returns_saved_assessments(client):
    create_res = client.post("/weather/analyse", json={
        "trip_id": "trip-weather-test-001",
        "destination": "Ghana",
        "month_of_travel": 2,
    })
    assert create_res.status_code == 201

    list_res = client.get("/trips/trip-weather-test-001/weather")
    assert list_res.status_code == 200
    assert len(list_res.json()) == 1


def test_list_trip_weather_empty_for_unknown_trip(client):
    res = client.get("/trips/no-weather-here/weather")
    assert res.status_code == 200
    assert res.json() == []


def test_analyse_weather_with_traveller_profile(client, sample_profile):
    profile = client.post("/traveller/profile", json=sample_profile).json()
    res = client.post("/weather/analyse", json={
        "traveller_id": profile["id"],
        "destination": "Jamaica",
        "month_of_travel": 3,
    })
    assert res.status_code == 201
    assert res.json()["traveller_id"] == profile["id"]

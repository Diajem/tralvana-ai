def test_check_visa_returns_201(client):
    res = client.post("/visa/check", json={
        "passport_country": "UK",
        "destination_country": "Japan",
    })
    assert res.status_code == 201
    body = res.json()
    assert body["visa_status"] == "VISA_NOT_REQUIRED"
    assert body["destination_country"] == "Japan"


def test_check_visa_requires_passport_and_destination(client):
    res = client.post("/visa/check", json={})
    assert res.status_code == 422


def test_check_visa_has_explanation_and_recommendation(client):
    res = client.post("/visa/check", json={
        "passport_country": "Nigeria",
        "destination_country": "UK",
    })
    body = res.json()
    assert body["explanation"]
    assert body["recommendation"]
    assert 0.0 <= body["confidence"] <= 1.0


def test_check_visa_status_is_a_valid_enum_value(client):
    res = client.post("/visa/check", json={
        "passport_country": "Ghana",
        "destination_country": "Nigeria",
    })
    assert res.json()["visa_status"] in {
        "VISA_NOT_REQUIRED", "VISA_REQUIRED", "ETA_REQUIRED",
        "EVISA_AVAILABLE", "CHECK_MANUALLY", "ENTRY_RESTRICTED",
    }


def test_check_visa_nationality_defaults_to_passport_country(client):
    res = client.post("/visa/check", json={
        "passport_country": "UK",
        "destination_country": "Ireland",
    })
    body = res.json()
    assert body["nationality"] == body["passport_country"]


def test_check_visa_with_transit_countries(client):
    res = client.post("/visa/check", json={
        "passport_country": "Nigeria",
        "destination_country": "France",
        "transit_countries": ["USA"],
    })
    body = res.json()
    assert body["transit_countries"] == ["USA"]
    assert any("transiting" in r.lower() for r in body["risks"])


def test_get_visa_assessment_returns_200(client):
    create_res = client.post("/visa/check", json={
        "passport_country": "UK",
        "destination_country": "USA",
    })
    assessment_id = create_res.json()["visa_assessment_id"]

    get_res = client.get(f"/visa/{assessment_id}")
    assert get_res.status_code == 200
    assert get_res.json()["visa_assessment_id"] == assessment_id


def test_get_unknown_visa_assessment_returns_404(client):
    res = client.get("/visa/does-not-exist")
    assert res.status_code == 404


def test_list_trip_visa_returns_saved_assessments(client):
    create_res = client.post("/visa/check", json={
        "trip_id": "trip-visa-test-001",
        "passport_country": "UK",
        "destination_country": "Japan",
    })
    assert create_res.status_code == 201

    list_res = client.get("/trips/trip-visa-test-001/visa")
    assert list_res.status_code == 200
    assert len(list_res.json()) == 1


def test_list_trip_visa_empty_for_unknown_trip(client):
    res = client.get("/trips/no-visa-here/visa")
    assert res.status_code == 200
    assert res.json() == []


def test_check_visa_with_traveller_profile(client, sample_profile):
    profile = client.post("/traveller/profile", json=sample_profile).json()
    res = client.post("/visa/check", json={
        "traveller_id": profile["id"],
        "passport_country": "Nigeria",
        "destination_country": "Ghana",
    })
    assert res.status_code == 201
    assert res.json()["traveller_id"] == profile["id"]


def test_check_visa_unknown_pair_still_returns_201(client):
    res = client.post("/visa/check", json={
        "passport_country": "Wakanda",
        "destination_country": "Atlantis",
    })
    assert res.status_code == 201
    assert res.json()["visa_status"] == "CHECK_MANUALLY"

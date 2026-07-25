from __future__ import annotations


def test_recommend_events_returns_provider_neutral_curated_results(client):
    response = client.post(
        "/events/recommend",
        json={
            "destination": "New York",
            "start_date": "2026-08-07",
            "end_date": "2026-08-22",
            "interests": ["fashion", "soccer"],
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["destination"] == "New York"
    assert body["data_source"] == "TRALVANA_CURATED_EVENT_IDEAS"
    assert body["provider_status"] == "AVAILABLE"
    assert body["retrieved_at"]
    assert len(body["event_options"]) == 4
    assert all(
        option["date_status"] == "UNVERIFIED"
        and option["availability_status"] == "UNKNOWN"
        and option["ticket_url"] is None
        for option in body["event_options"]
    )


def test_event_option_can_be_fetched_and_listed_by_trip(client):
    created = client.post(
        "/events/recommend",
        json={
            "trip_id": "trip-events-1",
            "destination": "London",
            "interests": ["football"],
        },
    ).json()
    option_id = created["event_options"][0]["event_option_id"]

    fetched = client.get(f"/events/{option_id}")
    assert fetched.status_code == 200
    assert fetched.json()["event_option_id"] == option_id

    listed = client.get("/trips/trip-events-1/events")
    assert listed.status_code == 200
    assert option_id in {
        option["event_option_id"] for option in listed.json()
    }


def test_event_date_range_must_be_ordered(client):
    response = client.post(
        "/events/recommend",
        json={
            "destination": "Paris",
            "start_date": "2026-09-10",
            "end_date": "2026-09-01",
        },
    )
    assert response.status_code == 422


def test_event_response_never_claims_a_fixture_or_ticket(client):
    response = client.post(
        "/events/recommend",
        json={
            "destination": "New York",
            "interests": ["soccer"],
        },
    )
    raw = response.text.lower()
    assert "no live calendar" in raw
    assert '"starts_at":null' in raw
    assert '"ticket_url":null' in raw

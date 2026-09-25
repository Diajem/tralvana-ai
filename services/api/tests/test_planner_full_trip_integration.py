"""Whole-trip regression for the launch-critical family booking journey.

The test deliberately exercises every supplier-backed discovery module the
planner currently owns, while proving that unsupported commerce capabilities
remain visible and fail closed.  It does not create a booking or payment.
"""

from __future__ import annotations


VIENNA_TO_JAMAICA_FAMILY = (
    "Plan and price a complete family holiday from Vienna, Austria to Ocho Rios, Jamaica, "
    "departing 10 October 2026 for 12 nights. The travellers are 2 adults and "
    "2 children aged 7 and 10. All four travellers are Austrian passport holders. "
    "We need economy return flights, checked baggage allowance, a family-friendly "
    "hotel, airport transfers, car hire, family attractions, a reggae concert with "
    "tickets, and a full daily itinerary. Include departure and arrival airports, "
    "hotel location and distance from the airport, and Jamaica online entry form guidance."
)


def test_vienna_to_jamaica_family_trip_exercises_complete_planner(
    client, monkeypatch
):
    from app.domains.experiences.service import experience_discovery_service

    monkeypatch.setattr(
        experience_discovery_service,
        "search",
        lambda **_: {
            "destination": "Ocho Rios",
            "destination_id": "34",
            "country_code": "JM",
            "provider": "viator_experience_provider",
            "environment": "SANDBOX",
            "booking_enabled": False,
            "retrieved_at": "2026-09-25T00:00:00+00:00",
            "products": [
                {
                    "provider": "VIATOR",
                    "product_reference": "JAM-FAMILY-1",
                    "title": "Family waterfall and river experience",
                    "description": "Sandbox family activity",
                    "rating": 4.8,
                    "review_count": 120,
                    "price_from": 75,
                    "currency": "GBP",
                    "images": [],
                    "booking_enabled": False,
                }
            ],
        },
    )

    response = client.post("/planner/plan", json={"message": VIENNA_TO_JAMAICA_FAMILY})

    assert response.status_code == 200
    body = response.json()
    assert body["intent"] == "PLAN_TRIP"
    itinerary = body["itinerary"]
    assert itinerary is not None

    brief = itinerary["trip_brief"]
    assert brief["origin"] == "Vienna"
    assert brief["destination"] == "Ocho Rios"
    assert brief["destination_region"] == "Jamaica"
    assert brief["local_areas"] == ["Ocho Rios"]
    assert brief["start_date"] == "2026-10-10"
    assert brief["end_date"] == "2026-10-22"
    assert brief["duration_nights"] == 12
    assert brief["duration_days"] == 13
    assert brief["travellers"] == {
        "adults": 2,
        "children": 2,
        "infants": 0,
        "minor_ages": [7, 10],
    }
    assert brief["nationalities"] == ["Austrian"]
    assert brief["cabin_class"] == "economy"
    assert brief["baggage_information_requested"] is True
    assert brief["car_hire_requested"] is True
    assert brief["airport_transfer_requested"] is True
    assert brief["entry_form_guidance_requested"] is True
    assert brief["airport_details_requested"] is True
    assert brief["hotel_airport_distance_requested"] is True
    assert brief["entry_form_guidance"] == {
        "form_name": "Electronic Immigration and Customs Declaration (C5)",
        "required": True,
        "official_url": "https://www.enterjamaica.gov.jm/",
        "cost": "Free",
        "completion_window": "Up to 30 days before travel",
        "per_traveller": True,
        "children_included": True,
        "advice": (
            "Complete one form for every traveller, including each child. "
            "Recheck the official requirement shortly before departure."
        ),
        "source": "Jamaica PICA and Jamaica Customs Agency",
    }

    assert len(itinerary["daily_outline"]) == 13
    assert [day["day"] for day in itinerary["daily_outline"]] == list(range(1, 14))
    assert itinerary["experience_recommendations"][0]["product_reference"] == "JAM-FAMILY-1"
    assert itinerary["experience_recommendations"][0]["booking_enabled"] is False
    assert "viator_experiences" in itinerary["modules_used"]
    assert "events" in itinerary["modules_used"]

    required_follow_ups = " ".join(itinerary["booking_readiness"]["items_needed"])
    assert "baggage" in required_follow_ups.lower()
    assert "departure, connection and arrival airport" in required_follow_ups
    assert "airport-to-hotel distance" in required_follow_ups
    assert "family airport transfer" in required_follow_ups
    assert "car-hire supplier" in required_follow_ups
    assert "official entry-form" in required_follow_ups
    assert itinerary["booking_readiness"]["status"] != "READY_TO_BOOK"

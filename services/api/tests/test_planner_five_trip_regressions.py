"""Acceptance coverage for the five customer-supplied production regressions."""


TOKYO = """Plan a 7 day trip to Tokyo for a couple, 2 adults, both Polish nationals. We'd like to visit Disneyland Tokyo and experience an unforgettable Japanese culture trip. We would like to fly from any of the airports in Warsaw since we live in Warsaw, ideally with LOT Polish Airlines or a reliable connecting carrier. My wife is interested in Japanese street fashion and would like to visit Harajuku and Shibuya shopping districts, plus attend a traditional tea ceremony. We would like to dine out as a couple 3 times during the trip, including one Michelin-starred restaurant, and would love to stay in a boutique hotel near Shinjuku. We would like to know our package allowance in Polish złoty, our visa requirements as Polish citizens, and a proper plan for the holiday. Maybe a day trip to Mount Fuji and a visit to historical temples in Kyoto. Traveling out on the 14th of October and would like to spend 7 full days in Japan."""

DUBAI = """Plan a 12 day trip to Dubai for a family of 7, 2 adults (Polish nationals) and 5 children (ages 3, 6, 9, 12, and 15), all holding Polish passports. The children would like to visit IMG Worlds of Adventure and water parks like Aquaventure; they would like to make the journey an unforgettable trip. We would like to fly from any of the airports in Warsaw since we live in Warsaw, ideally with LOT Polish Airlines. My husband is interested in luxury watches and would like to visit the Dubai Mall watch boutiques and the Gold Souk. We would like to dine out as a family 5 times during the trip, including a desert safari dinner, and would love to stay in a family-friendly resort with a private beach. We would like to know our package allowance in Polish złoty, our visa requirements as Polish citizens, and a proper plan for the holiday. Maybe a desert safari for the kids and a visit to the Museum of the Future as a family. Traveling out on the 3rd of December and would like to spend 12 full days in Dubai."""

NEW_YORK = """Plan a 5 day trip to New York for 2 adults, close friends travelling together — one Polish national, one Nigerian national currently residing in Warsaw on a work visa. We would like to see a Broadway show and make the journey an unforgettable trip. We would like to fly from any of the airports in Warsaw since we live in Warsaw, and we're open to a budget carrier like Wizz Air for the first leg if it connects well. One of us is interested in art galleries and would like to visit MoMA and a private gallery tour in Chelsea. We would like to dine out 4 times during the trip, including one rooftop restaurant, and would love to stay in a boutique hotel in Midtown Manhattan. We would like to know our package allowance in Polish złoty, our respective US visa requirements given our different nationalities, and a proper plan for the holiday. Maybe an ice skating session at Rockefeller Center and a visit to the Statue of Liberty and Ellis Island as a historical stop. Traveling out on the 20th of November and would like to spend 5 full days in New York."""

CAPE_TOWN = """Plan a 9 day trip to Cape Town for a family of 6, 3 adults (Polish nationals) and 3 children (ages 5, 8, and 11, also Polish nationals). The children would like to go on a safari and visit water parks; they would like to make the journey an unforgettable trip. We would like to fly from any of the airports in Warsaw since we live in Warsaw. My mother is interested in local textiles and would like to visit craft markets and attend a fashion showcase featuring African designers. We would like to dine out as a family 4 times during the trip, including one seafood restaurant on the waterfront, and would love to stay in a family-friendly hotel near Camps Bay. We would like to know our package allowance in Polish złoty, our visa requirements as Polish citizens, and a proper plan for the holiday. Maybe a boat trip to Robben Island and a visit to the Cape of Good Hope as a family. Traveling out on the 5th of January and would like to spend 9 full days in Cape Town."""

BARCELONA = """Plan a 6 day trip to Barcelona for a family of 4, 2 adults (one Polish national, one German national) and 2 children (ages 4 and 7, dual Polish-German nationals). The children would like to visit PortAventura theme park and a water park; they would like to make the journey an unforgettable trip. We would like to fly from any of the airports in Warsaw since we live in Warsaw, ideally with Ryanair or Wizz Air since it's a short hop. My husband is interested in football and would like to visit Camp Nou stadium and the FC Barcelona museum. We would like to dine out as a family 3 times during the trip, including one authentic tapas restaurant, and would love to stay in a family-friendly apartment near the beach. We would like to know our package allowance in Polish złoty and a proper plan for the holiday (visa-free travel within the EU should apply, but please confirm). Maybe a beach day for the kids and a visit to the Sagrada Familia and Gothic Quarter as a family. Traveling out on the 8th of April and would like to spend 6 full days in Barcelona."""


def _plan(client, message: str) -> dict:
    response = client.post("/planner/plan", json={"message": message})
    assert response.status_code == 200
    itinerary = response.json()["itinerary"]
    assert itinerary is not None
    return itinerary


def _visa_by_nationality(itinerary: dict) -> dict[str, dict]:
    return {
        item["nationality"]: item
        for item in itinerary["visa_summary"]["individual_assessments"]
    }


def _assert_warsaw_context(brief: dict) -> None:
    assert brief["origin"] == "Warsaw"
    assert brief["country_of_residence"] == "Poland"
    assert brief["airport_preference"] == "Any Warsaw airport"
    assert brief["departure_options"] == [
        "Warsaw Chopin Airport",
        "Warsaw Modlin Airport",
    ]
    assert not any("Airlines" in value or "Wizz" in value for value in brief["departure_options"])
    assert brief["baggage_information_requested"] is True


def _outline_text(itinerary: dict) -> str:
    return " ".join(
        str(value) for day in itinerary["daily_outline"] for value in day.values()
    ).casefold()


def test_tokyo_trip_preserves_couple_context_and_polish_entry_rule(client):
    itinerary = _plan(client, TOKYO)
    brief = itinerary["trip_brief"]
    _assert_warsaw_context(brief)
    assert brief["destination"] == "Tokyo"
    assert brief["start_date"] == "2026-10-14"
    assert brief["end_date"] == "2026-10-21"
    assert brief["travellers"]["adults"] == 2
    assert brief["nationalities"] == ["Polish"]
    assert brief["airline_preferences"] == ["LOT Polish Airlines"]
    assert brief["dining_out_count"] == 3
    assert _visa_by_nationality(itinerary)["Polish"]["visa_status"] == "VISA_NOT_REQUIRED"
    outline = _outline_text(itinerary)
    for activity in (
        "disneyland tokyo", "harajuku and shibuya", "traditional tea ceremony",
        "mount fuji day trip", "historical temples in kyoto",
    ):
        assert activity in outline
    assert "romantic arrival" not in outline
    assert "sushi saito" not in outline


def test_dubai_trip_preserves_all_child_ages_and_polish_entry_rule(client):
    itinerary = _plan(client, DUBAI)
    brief = itinerary["trip_brief"]
    _assert_warsaw_context(brief)
    assert brief["start_date"] == "2026-12-03"
    assert brief["end_date"] == "2026-12-15"
    assert brief["travellers"] == {
        "adults": 2,
        "children": 5,
        "infants": 0,
        "minor_ages": [3, 6, 9, 12, 15],
    }
    assert brief["dining_out_count"] == 5
    outline = _outline_text(itinerary)
    for activity in (
        "img worlds of adventure", "aquaventure water park", "gold souk",
        "desert safari", "museum of the future",
    ):
        assert activity in outline
    polish = _visa_by_nationality(itinerary)["Polish"]
    assert polish["visa_status"] == "VISA_NOT_REQUIRED"
    assert polish["visa_type"] == "None (short visit)"


def test_new_york_trip_checks_each_passport_and_has_no_amsterdam_leak(client):
    itinerary = _plan(client, NEW_YORK)
    brief = itinerary["trip_brief"]
    _assert_warsaw_context(brief)
    assert brief["nationalities"] == ["Polish", "Nigerian"]
    assessments = _visa_by_nationality(itinerary)
    assert assessments["Polish"]["visa_type"] == "ESTA"
    assert assessments["Nigerian"]["visa_type"] == "B1/B2 Visa"
    assert brief["dining_out_count"] == 4
    outline = _outline_text(itinerary)
    for activity in (
        "moma", "private gallery tour in chelsea", "rockefeller center ice skating",
        "statue of liberty and ellis island", "broadway show",
    ):
        assert activity in outline
    assert "ajax" not in outline
    assert "amsterdam" not in outline
    assert "winery" not in outline


def test_cape_town_trip_rolls_past_month_forward_and_has_no_amsterdam_leak(client):
    itinerary = _plan(client, CAPE_TOWN)
    brief = itinerary["trip_brief"]
    _assert_warsaw_context(brief)
    assert brief["start_date"] == "2027-01-05"
    assert brief["end_date"] == "2027-01-14"
    assert _visa_by_nationality(itinerary)["Polish"]["visa_status"] == "VISA_NOT_REQUIRED"
    assert brief["dining_out_count"] == 4
    outline = _outline_text(itinerary)
    for activity in (
        "safari", "water park", "craft markets", "robben island boat trip",
        "cape of good hope", "african designer fashion showcase",
    ):
        assert activity in outline
    assert "ajax" not in outline
    assert "amsterdam" not in outline


def test_barcelona_trip_normalises_dual_nationality_and_eu_free_movement(client):
    itinerary = _plan(client, BARCELONA)
    brief = itinerary["trip_brief"]
    _assert_warsaw_context(brief)
    assert brief["start_date"] == "2027-04-08"
    assert brief["end_date"] == "2027-04-14"
    assert brief["nationalities"] == ["Polish", "German"]
    assert brief["airline_preferences"] == ["Ryanair", "Wizz Air"]
    assessments = _visa_by_nationality(itinerary)
    assert assessments["Polish"]["visa_type"] == "None (EU free movement)"
    assert assessments["German"]["visa_type"] == "None (EU free movement)"
    assert brief["dining_out_count"] == 3
    outline = _outline_text(itinerary)
    for activity in (
        "portaventura theme park", "water park", "camp nou and the fc barcelona museum",
        "beach day", "sagrada familia", "gothic quarter",
    ):
        assert activity in outline
    assert "football city walk" not in outline
    assert "dinner at tickets" not in outline

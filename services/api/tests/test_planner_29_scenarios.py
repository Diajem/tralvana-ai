"""Broad production-style regression matrix for natural-language trip plans.

These scenarios deliberately vary party composition, trip length, phrasing,
origin, destination and requested activity.  The assertions focus on facts the
traveller actually supplied; provider availability is tested separately.
"""

from __future__ import annotations

import pytest


SCENARIOS = [
    ("paris_couple", "My wife and I want to travel to Paris from Manchester on 5 September 2026 for 4 days. We want to visit the Eiffel Tower.", "Manchester", "Paris", 4, 2, 0, 0, "Eiffel Tower"),
    ("berlin_solo", "Plan a solo trip to Berlin from London on 8 September 2026 for 3 days. I want to visit the Brandenburg Gate.", "London", "Berlin", 3, 1, 0, 0, "Brandenburg Gate"),
    ("lisbon_friends", "Me and my 3 friends are going to Lisbon from Birmingham on 12 September 2026 for 6 days. We want to visit Belem Tower.", "Birmingham", "Lisbon", 6, 4, 0, 0, "Belem Tower"),
    ("rome_family", "Plan a 7 day trip to Rome from Bristol on 20 September 2026 for a family of 5 with three children. We want to visit the Colosseum.", "Bristol", "Rome", 7, 2, 3, 0, "Colosseum"),
    ("barcelona_infant", "Plan a 5 day trip to Barcelona from London on 28 September 2026 for 2 adults and one infant. We want to visit Sagrada Familia.", "London", "Barcelona", 5, 2, 0, 1, "Sagrada Familia"),
    ("prague_spouses", "My husband and I are going to Prague from Leeds on 3 October 2026 for 5 days. We want to visit Prague Castle.", "Leeds", "Prague", 5, 2, 0, 0, "Prague Castle"),
    ("vienna_group", "Plan a 4 day trip to Vienna from Liverpool on 10 October 2026 for a group of 6 friends. We want to visit Schonbrunn Palace.", "Liverpool", "Vienna", 4, 6, 0, 0, "Schonbrunn Palace"),
    ("budapest_reverse_friends", "Three friends and me are going to Budapest from London on 15 October 2026 for 5 days. We want to visit Buda Castle.", "London", "Budapest", 5, 4, 0, 0, "Buda Castle"),
    ("copenhagen_couple", "Plan a 4 day city break to Copenhagen from Edinburgh on 20 October 2026 for a couple. We want to visit Tivoli Gardens.", "Edinburgh", "Copenhagen", 4, 2, 0, 0, "Tivoli Gardens"),
    ("stockholm_parent", "Plan a 6 day trip to Stockholm from Newcastle on 25 October 2026 for one adult and two children. We want to visit the Vasa Museum.", "Newcastle", "Stockholm", 6, 1, 2, 0, "Vasa Museum"),
    ("oslo_family", "Plan a 5 day trip to Oslo from Glasgow on 1 November 2026 for 2 adults and 2 children. We want to visit the Fram Museum.", "Glasgow", "Oslo", 5, 2, 2, 0, "Fram Museum"),
    ("reykjavik_solo", "I am travelling alone from London to Reykjavik on 4 November 2026 for 5 days. I want to visit the Blue Lagoon.", "London", "Reykjavik", 5, 1, 0, 0, "Blue Lagoon"),
    ("new_york_friends", "Plan a 8 day trip to New York from Manchester on 8 November 2026 for 3 adults. We want to visit the Statue of Liberty.", "Manchester", "New York", 8, 3, 0, 0, "Statue Of Liberty"),
    ("tokyo_family", "Plan a 10 day trip to Tokyo from London on 12 November 2026 for a family of 4 with two children. We want to visit Senso-ji Temple.", "London", "Tokyo", 10, 2, 2, 0, "Senso-Ji Temple"),
    ("singapore_family", "Plan a 7 day trip to Singapore from London on 18 November 2026 for 2 adults and 2 children. We want to visit Gardens by the Bay.", "London", "Singapore", 7, 2, 2, 0, "Gardens By The Bay"),
    ("dubai_couple", "I and my partner want to travel to Dubai from Birmingham on 22 November 2026 for 6 days. We want to visit Burj Khalifa.", "Birmingham", "Dubai", 6, 2, 0, 0, "Burj Khalifa"),
    ("istanbul_friends", "Plan a 5 day trip to Istanbul from London on 1 December 2026 for 4 adults. We want to visit the Grand Bazaar.", "London", "Istanbul", 5, 4, 0, 0, "Grand Bazaar"),
    ("marrakech_couple", "Plan a 6 day trip to Marrakech from Manchester on 3 December 2026 for 2 adults. We want to visit Jardin Majorelle.", "Manchester", "Marrakech", 6, 2, 0, 0, "Jardin Majorelle"),
    ("cape_town_family", "Plan a 9 day trip to Cape Town from Birmingham on 5 December 2026 for 2 adults and 2 children. We want to visit Table Mountain.", "Birmingham", "Cape Town", 9, 2, 2, 0, "Table Mountain"),
    ("nairobi_family", "Plan a 7 day trip to Nairobi from London on 8 December 2026 for a family of 4 with two kids. We want to visit Nairobi National Park.", "London", "Nairobi", 7, 2, 2, 0, "Nairobi National Park"),
    ("rio_friends", "Plan a 8 day trip to Rio de Janeiro from Manchester on 10 December 2026 for 3 adults. We want to visit Christ the Redeemer.", "Manchester", "Rio De Janeiro", 8, 3, 0, 0, "Christ The Redeemer"),
    ("buenos_aires_couple", "Plan a 7 day trip to Buenos Aires from London on 12 December 2026 for a couple. We want to visit Teatro Colon.", "London", "Buenos Aires", 7, 2, 0, 0, "Teatro Colon"),
    ("mexico_city_friends", "Plan a 6 day trip to Mexico City from London on 14 December 2026 for 4 adults. We want to visit Frida Kahlo Museum.", "London", "Mexico City", 6, 4, 0, 0, "Frida Kahlo Museum"),
    ("toronto_family", "Plan a 7 day trip to Toronto from Manchester on 16 December 2026 for 2 adults and 2 children. We want to visit the CN Tower.", "Manchester", "Toronto", 7, 2, 2, 0, "Cn Tower"),
    ("sydney_couple", "Plan a 9 day trip to Sydney from London on 18 December 2026 for 2 adults. We want to visit Sydney Opera House.", "London", "Sydney", 9, 2, 0, 0, "Sydney Opera House"),
    ("bangkok_solo", "Plan a solo trip to Bangkok from Manchester on 20 December 2026 for 6 days. I want to visit the Grand Palace.", "Manchester", "Bangkok", 6, 1, 0, 0, "Grand Palace"),
    ("athens_older_couple", "My wife and I want to travel to Athens from London on 22 December 2026 for 5 days. We want to visit the Acropolis.", "London", "Athens", 5, 2, 0, 0, "Acropolis"),
    ("orlando_family", "Plan a 8 day trip to Orlando from Manchester on 24 December 2026 for a family of 5 with three kids. We want to visit Walt Disney World.", "Manchester", "Orlando", 8, 2, 3, 0, "Walt Disney World"),
    ("seoul_friends", "Plan a 7 day trip to Seoul from London on 27 December 2026 for 3 adults. We want to visit Gyeongbokgung Palace.", "London", "Seoul", 7, 3, 0, 0, "Gyeongbokgung Palace"),
]


@pytest.mark.parametrize(
    "scenario_name,message,origin,destination,duration,adults,children,infants,activity",
    SCENARIOS,
    ids=[scenario[0] for scenario in SCENARIOS],
)
def test_twenty_nine_natural_language_trip_scenarios(
    client,
    scenario_name,
    message,
    origin,
    destination,
    duration,
    adults,
    children,
    infants,
    activity,
):
    response = client.post("/planner/plan", json={"message": message})

    assert response.status_code == 200, scenario_name
    body = response.json()
    assert body["intent"] == "PLAN_TRIP", scenario_name
    itinerary = body["itinerary"]
    assert itinerary is not None, scenario_name

    brief = itinerary["trip_brief"]
    assert brief["origin"] == origin, scenario_name
    assert brief["destination"] == destination, scenario_name
    assert brief["duration_days"] == duration, scenario_name
    assert brief["travellers"] == {
        "adults": adults,
        "children": children,
        "infants": infants,
    }, scenario_name
    assert brief["date_precision"] == "EXACT", scenario_name
    assert activity in brief["requested_activities"], scenario_name
    assert len(itinerary["daily_outline"]) == duration, scenario_name
    assert [day["day"] for day in itinerary["daily_outline"]] == list(
        range(1, duration + 1)
    ), scenario_name

    # MOCK and sandbox records must never appear as bookable public planner
    # recommendations.  A missing live provider stays visibly missing.
    assert itinerary["flight_recommendation"] is None, scenario_name
    assert itinerary["accommodation_recommendation"] is None, scenario_name

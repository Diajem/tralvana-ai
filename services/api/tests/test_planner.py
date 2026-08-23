"""
POST /planner/plan (T-040) — the AI Travel Planner. Confirms the
natural-language entry point reuses the existing conversation/Trip
Brain pipeline unchanged and only adds the Trip Assembly step on top.
"""

from __future__ import annotations

from datetime import datetime


def test_full_plan_trip_message_returns_an_assembled_itinerary(client):
    res = client.post("/planner/plan", json={
        "message": "I want to plan a trip to Tokyo in September for 2 adults, balanced budget, I am from Nigeria",
    })
    assert res.status_code == 200
    body = res.json()
    assert body["intent"] == "PLAN_TRIP"
    assert body["itinerary"] is not None

    itinerary = body["itinerary"]
    for key in (
        "executive_summary", "destination_recommendation", "flight_recommendation",
        "accommodation_recommendation", "budget_summary", "visa_summary",
        "weather_expectations", "event_recommendations", "risks", "assumptions", "daily_outline",
        "why_this_itinerary", "confidence", "confidence_explanation",
        "alternative_options", "grounding_notices", "trip_brief",
        "booking_readiness",
    ):
        assert key in itinerary

    assert len(itinerary["daily_outline"]) > 0
    assert itinerary["executive_summary"]
    assert 0.0 <= itinerary["confidence"] <= 1.0


def test_full_plan_with_weather_information_returns_itinerary_not_weather_only(client):
    res = client.post("/planner/plan", json={
        "message": (
            "Plan a 7-day trip to New York for 2 adults, travelling from Manchester "
            "from 15 September 2026 to 22 September 2026. Both travellers are Irish "
            "citizens. We want a balanced budget, a central hotel, major attractions, "
            "restaurants, shopping, a sporting event, ESTA guidance, weather information "
            "and eSIM options."
        ),
    })

    assert res.status_code == 200
    body = res.json()
    assert body["intent"] == "PLAN_TRIP"
    assert body["itinerary"] is not None


def test_vague_message_returns_no_itinerary_but_a_helpful_reply(client):
    res = client.post("/planner/plan", json={"message": "hi there"})
    assert res.status_code == 200
    body = res.json()
    assert body["response"]
    # Too little information for Trip Brain to have run at all.
    assert body["itinerary"] is None


def test_destination_only_message_may_still_lack_a_full_itinerary(client):
    res = client.post("/planner/plan", json={"message": "I want to go to Paris"})
    assert res.status_code == 200
    body = res.json()
    # Either a partial recommendation or a follow-up — never a 500,
    # never a raw exception leaking into the response.
    assert "itinerary" in body


def test_itinerary_never_exposes_raw_provider_or_internal_fields(client):
    res = client.post("/planner/plan", json={
        "message": "Plan a trip to Tokyo in September for 2 adults, balanced budget, from Nigeria",
    })
    body = res.json()
    raw = res.text
    # Underscore-prefixed internal fields (provider ids, persona scores,
    # price anchors) must never leak into the public planner response.
    assert "_provider_offer_id" not in raw
    assert "_persona_scores" not in raw
    assert "_price_anchor" not in raw
    assert body["itinerary"] is not None


def test_conversation_id_is_reused_across_turns(client):
    first = client.post("/planner/plan", json={"message": "I want to go to Rome"})
    conversation_id = first.json()["conversation_id"]

    second = client.post("/planner/plan", json={
        "message": "September, 2 adults, balanced budget",
        "conversation_id": conversation_id,
    })
    assert second.json()["conversation_id"] == conversation_id


def test_plan_trip_accumulates_details_and_completes_across_turns(client):
    first = client.post("/planner/plan", json={
        "message": (
            "I want to go to Montego Bay with my partner. We are travelling from Leeds, "
            "we are British and Nigerian, and we like beaches, culture, food and music."
        ),
    })
    assert first.status_code == 200
    first_body = first.json()
    assert first_body["intent"] == "PLAN_TRIP"
    assert first_body["itinerary"] is None
    assert "When are you planning to travel?" in first_body["missing_information"]

    second = client.post("/planner/plan", json={
        "message": "We want to travel from 10 August to 17 August 2026 and there will be 2 adults.",
        "conversation_id": first_body["conversation_id"],
    })
    assert second.status_code == 200
    second_body = second.json()
    assert second_body["conversation_id"] == first_body["conversation_id"]
    assert second_body["intent"] == "PLAN_TRIP"
    assert second_body["itinerary"] is not None
    assert "When are you planning to travel?" not in second_body["missing_information"]
    assert "Montego Bay" in second_body["itinerary"]["executive_summary"]
    itinerary = second_body["itinerary"]
    assert itinerary["trip_brief"]["origin"] == "Leeds"
    assert itinerary["trip_brief"]["start_date"] == "2026-08-10"
    assert itinerary["trip_brief"]["end_date"] == "2026-08-17"
    assert itinerary["trip_brief"]["travellers"]["adults"] == 2
    assert itinerary["trip_brief"]["duration_days"] == 7
    assert itinerary["flight_recommendation"] is None
    assert itinerary["accommodation_recommendation"] is None
    assert itinerary["visa_summary"]["nationality"] == "British"


def test_exact_family_new_york_request_keeps_every_input_and_builds_seven_specific_days(client):
    res = client.post("/planner/plan", json={
        "message": (
            "Plan a 7-day trip from London to New York for 2 adults and 2 children "
            "aged 6 and 9, departing 10 October 2026 and returning 17 October 2026. "
            "We want economy flights, a family-friendly hotel, attractions and live events."
        ),
    })

    assert res.status_code == 200
    itinerary = res.json()["itinerary"]
    assert itinerary is not None
    brief = itinerary["trip_brief"]
    assert brief["origin"] == "London"
    assert brief["destination"] == "New York"
    assert brief["start_date"] == "2026-10-10"
    assert brief["end_date"] == "2026-10-17"
    assert brief["duration_days"] == 7
    assert brief["travellers"] == {
        "adults": 2,
        "children": 2,
        "infants": 0,
        "minor_ages": [6, 9],
    }
    assert set(brief["interests"]) == {"major attractions", "live events"}
    assert brief["accommodation_preferences"] == ["Child-friendly hotel"]
    assert "events" in itinerary["modules_used"]
    assert itinerary["accommodation_recommendation"] is None
    assert "New York Guesthouse" not in itinerary["executive_summary"]
    assert len(itinerary["event_recommendations"]) > 0
    assert len(itinerary["daily_outline"]) == 7
    assert [day["title"] for day in itinerary["daily_outline"]] == [
        "Day 1: Arrival & easy Manhattan orientation",
        "Day 2: Central Park & natural history",
        "Day 3: Statue of Liberty & Lower Manhattan",
        "Day 4: Intrepid Museum & Hudson River",
        "Day 5: Rockefeller Center & Midtown",
        "Day 6: Brooklyn Bridge & family Brooklyn",
        "Day 7: Final New York stop & departure",
    ]


def test_family_trip_follow_up_adds_interests_without_forgetting_existing_ones(client):
    first = client.post("/planner/plan", json={
        "message": (
            "Plan a 7-day trip from London to New York for 2 adults and 2 children "
            "aged 6 and 9, departing 10 October 2026 and returning 17 October 2026. "
            "We want economy flights, a family-friendly hotel and attractions."
        ),
    })
    conversation_id = first.json()["conversation_id"]

    second = client.post("/planner/plan", json={
        "conversation_id": conversation_id,
        "message": (
            "All four travellers are British passport holders. "
            "Please show family-friendly live events during our dates."
        ),
    })

    assert second.status_code == 200
    itinerary = second.json()["itinerary"]
    assert itinerary is not None
    assert set(itinerary["trip_brief"]["interests"]) == {
        "major attractions",
        "live events",
    }
    assert itinerary["trip_brief"]["nationality"] == "British"
    assert itinerary["visa_summary"]["visa_type"] == "ESTA"


def test_city_clarification_reply_completes_country_level_plan(client):
    first = client.post("/planner/plan", json={
        "message": (
            "Plan a 5 day trip to Jamaica from London on 18 August 2026 "
            "for 2 adults."
        ),
    })
    first_body = first.json()
    assert first_body["itinerary"] is None
    assert any(
        "Which city, town, or resort area in Jamaica" in question
        for question in first_body["missing_information"]
    )

    second = client.post("/planner/plan", json={
        "message": "Ocho Rios",
        "conversation_id": first_body["conversation_id"],
    })
    second_body = second.json()
    assert second_body["intent"] == "PLAN_TRIP"
    assert second_body["itinerary"] is not None
    assert second_body["itinerary"]["trip_brief"]["local_areas"] == ["Ocho Rios"]


def test_additional_details_rebuild_an_existing_itinerary(client):
    first = client.post("/planner/plan", json={
        "message": (
            "Plan a 5 day family trip to Dublin from London on 18 August 2026 "
            "for 2 adults and 2 children."
        ),
    })
    first_body = first.json()
    assert first_body["itinerary"] is not None
    assert first_body["itinerary"]["budget_summary"] is None

    second = client.post("/planner/plan", json={
        "message": (
            "We are British passport holders. Our total budget is £2,500 and "
            "we want a child-friendly hotel near the city centre with a quiet room."
        ),
        "conversation_id": first_body["conversation_id"],
    })
    second_body = second.json()
    itinerary = second_body["itinerary"]
    assert second_body["intent"] == "PLAN_TRIP"
    assert itinerary is not None
    assert itinerary["trip_brief"]["nationality"] == "British"
    assert itinerary["budget_summary"]["declared_budget"] == 2500
    assert itinerary["trip_brief"]["accommodation_preferences"] == [
        "Child-friendly hotel",
        "Near Dublin city centre",
        "Quiet room",
    ]


def test_standalone_year_reply_corrects_an_inferred_year(client):
    first = client.post("/planner/plan", json={
        "message": (
            "Plan a 5 day family trip to Dublin from London on 18 August "
            "for 2 adults and 2 children."
        ),
    })
    first_body = first.json()
    assert first_body["itinerary"]["trip_brief"]["date_inference_note"] is not None

    second = client.post("/planner/plan", json={
        "message": "2027",
        "conversation_id": first_body["conversation_id"],
    })
    brief = second.json()["itinerary"]["trip_brief"]
    assert second.json()["intent"] == "PLAN_TRIP"
    assert brief["start_date"] == "2027-08-18"
    assert brief["end_date"] == "2027-08-23"
    assert brief["date_inference_note"] is None


def test_daily_outline_length_matches_trip_duration(client):
    res = client.post("/planner/plan", json={
        "message": "Plan a 4 day trip to Tokyo in September for 2 adults, balanced budget, from Nigeria",
    })
    body = res.json()
    assert body["itinerary"] is not None
    assert len(body["itinerary"]["daily_outline"]) == 4
    assert body["itinerary"]["trip_brief"]["duration_days"] == 4
    assert body["itinerary"]["budget_summary"] is None


def test_country_only_jamaica_request_asks_for_an_area(client):
    body = client.post(
        "/planner/plan",
        json={
            "message": (
                "Plan a 7 day trip to Jamaica from Leeds in September 2026 "
                "for 2 adults with a £2500 budget."
            )
        },
    ).json()

    assert body["itinerary"] is None
    assert body["missing_information"] == [
        "Which city, town, or resort area in Jamaica would you like to stay in?"
    ]


def test_two_week_dublin_plan_preserves_dates_party_weather_and_country(client):
    res = client.post("/planner/plan", json={
        "message": (
            "I am Desmond. Plan a relaxing holiday to Dublin from Bradford "
            "on 17 August 2026 for two weeks with 2 adults and 2 children."
        ),
    })
    assert res.status_code == 200
    itinerary = res.json()["itinerary"]
    assert itinerary is not None
    assert len(itinerary["daily_outline"]) == 14
    assert itinerary["trip_brief"]["origin"] == "Bradford"
    assert itinerary["trip_brief"]["start_date"] == "2026-08-17"
    assert itinerary["trip_brief"]["end_date"] == "2026-08-31"
    assert itinerary["trip_brief"]["duration_days"] == 14
    assert itinerary["trip_brief"]["travellers"]["adults"] == 2
    assert itinerary["trip_brief"]["travellers"]["children"] == 2
    assert itinerary["flight_recommendation"] is None
    assert itinerary["accommodation_recommendation"] is None
    assert itinerary["weather_expectations"]["destination"] == "Ireland"
    assert itinerary["weather_expectations"]["month_of_travel"] == 8
    assert itinerary["weather_expectations"]["season"] == "SUMMER"
    assert itinerary["visa_summary"]["destination_country"] == "Ireland"
    assert itinerary["visa_summary"]["nationality"] != "Desmond"


def test_complete_new_york_holiday_honours_every_supplied_detail(client):
    res = client.post("/planner/plan", json={
        "message": (
            "Plan a 15-day holiday to New York with my partner from 7 August "
            "to 22 August 2026. We are travelling from Leeds but do not mind "
            "flying from Manchester or London. We are both British nationals. "
            "We love to dine out and stay in an average hotel. She loves fashion "
            "and I like soccer and places of significant interest."
        ),
    })
    assert res.status_code == 200
    body = res.json()
    assert body["intent"] == "PLAN_TRIP"
    itinerary = body["itinerary"]
    assert itinerary is not None
    assert len(itinerary["daily_outline"]) == 15

    assert itinerary["trip_brief"]["origin"] == "Manchester"
    assert itinerary["trip_brief"]["start_date"] == "2026-08-07"
    assert itinerary["trip_brief"]["end_date"] == "2026-08-22"
    assert itinerary["trip_brief"]["travellers"]["adults"] == 2
    assert itinerary["trip_brief"]["duration_days"] == 15
    assert itinerary["flight_recommendation"] is None
    assert itinerary["accommodation_recommendation"] is None
    assert itinerary["budget_summary"] is None

    visa = itinerary["visa_summary"]
    assert visa["destination_country"] == "United States"
    assert visa["intended_length_of_stay"] == 15
    assert visa["visa_type"] == "ESTA"
    assert visa["travel_authorisation_required"] is True
    assert "ESTA travel authorisation is required" in itinerary["executive_summary"]
    assert "No visa is required" not in itinerary["executive_summary"]
    assert any("two years" in item for item in visa["entry_requirements"])

    weather = itinerary["weather_expectations"]
    assert weather["destination"] == "New York City"
    assert weather["month_of_travel"] == 8
    assert "Hurricane season" not in str(weather)

    outline_text = str(itinerary["daily_outline"]).lower()
    for interest in ("dine out", "fashion", "soccer", "significance"):
        assert interest in outline_text

    notices = {notice["domain"]: notice for notice in itinerary["grounding_notices"]}
    assert notices["flight"]["level"] == "GUIDANCE"
    assert notices["flight"]["is_current"] is False
    assert notices["accommodation"]["level"] == "GUIDANCE"
    assert notices["budget"]["level"] == "GUIDANCE"
    assert notices["visa"]["level"] == "GUIDANCE"
    assert notices["weather"]["level"] == "CLIMATE_PROFILE"
    assert notices["events"]["level"] == "CURATED"
    assert notices["events"]["is_current"] is False
    assert len(itinerary["event_recommendations"]) >= 2
    categories = {
        option["category"] for option in itinerary["event_recommendations"]
    }
    assert {"FASHION", "SPORT"}.issubset(categories)
    assert all(
        option["starts_at"] is None
        and option["availability_status"] == "UNKNOWN"
        and option["ticket_url"] is None
        for option in itinerary["event_recommendations"]
    )
    assert all(notice["requires_confirmation"] for notice in notices.values())
    assert "booking confirmation" in itinerary["executive_summary"]
    assert "Guesthouse" not in itinerary["executive_summary"]
    assert "You'll fly" not in itinerary["executive_summary"]
    assert "AeroLondon" not in body["response"]
    assert "Guesthouse" not in body["response"]
    assert "ESTA Required" in body["response"]
    assert "ETA Required" not in body["response"]
    assert "Match Day Experience" not in str(itinerary["daily_outline"])


def test_tokyo_month_only_plan_is_coherent_and_preserves_gbp_budget(client):
    res = client.post("/planner/plan", json={
        "message": (
            "Plan a 10-day holiday to Tokyo from Manchester in October 2026 "
            "for 2 adults. Our total budget is £3,000 and we are interested "
            "in football and culture."
        ),
    })
    assert res.status_code == 200
    itinerary = res.json()["itinerary"]
    assert itinerary is not None
    brief = itinerary["trip_brief"]
    assert brief["origin"] == "Manchester"
    assert brief["destination"] == "Tokyo"
    assert brief["duration_days"] == 10
    assert brief["travel_period"] == "October 2026"
    assert brief["date_precision"] == "MONTH"
    assert brief["travellers"]["adults"] == 2

    budget = itinerary["budget_summary"]
    assert budget["declared_budget"] == 3000
    assert budget["currency"] == "GBP"
    assert budget["assessment_status"] == "NOT_YET_ASSESSED"
    assert "price estimates" in budget["allocation_basis"]

    assert itinerary["flight_recommendation"] is None
    assert itinerary["accommodation_recommendation"] is None
    assert itinerary["booking_readiness"]["score"] == 55
    assert len(itinerary["booking_readiness"]["items_needed"]) == 4
    assert itinerary["weather_expectations"]["month_of_travel"] == 10
    assert itinerary["weather_expectations"]["weather_status"] == "CHALLENGING"
    assert itinerary["weather_expectations"]["natural_hazard_risk"] == "SEVERE"

    assert len(itinerary["daily_outline"]) == 10
    assert all(
        "estimated_daily_cost_usd" not in day
        for day in itinerary["daily_outline"]
    )
    outline = str(itinerary["daily_outline"])
    assert outline.count("Senso-ji") == 1
    assert "Osaka" not in outline
    assert outline.lower().count("fixture calendar") == 1
    assert {event["category"] for event in itinerary["event_recommendations"]} == {
        "CULTURE",
        "SPORT",
    }
    assert "Japan Guesthouse" not in res.text
    assert "AeroLondon" not in res.text
    assert "$150" not in res.text


def test_holiday_goal_persists_dates_party_and_interests(client):
    res = client.post("/planner/plan", json={
        "message": (
            "Plan a 15-day holiday to New York with my partner from 7 August "
            "to 22 August 2026. We are both British nationals and enjoy fashion "
            "and soccer."
        ),
    })
    assert res.status_code == 200
    goal = client.get(f"/goals/{res.json()['goal_id']}").json()

    assert goal["title"] == "Trip to New York"
    assert goal["timeframe"]["earliest"] == "2026-08-07"
    assert goal["timeframe"]["latest"] == "2026-08-22"
    assert goal["timeframe"]["duration_days"] == 15
    assert goal["travellers"]["adults"] == 2
    assert {"fashion", "soccer"}.issubset(set(goal["interests"]))


def test_jamaica_multi_stay_prompt_generates_and_preserves_each_stage(client):
    res = client.post("/planner/plan", json={
        "message": (
            "I would like to travel to Jamaica from either London or Manchester "
            "on the 10th of October 2026. I would like to stay in St Mary Parish "
            "near the family. I would like to party with friends on my birthday, "
            "which is the 12th of October, so I would like to stay at the RIU Hotels "
            "in Oshi Rius until the 13th of October. On the 13th I will check out of "
            "the RIU Hotel and would like you to book a budget-friendly hotel for me "
            "for the rest of the trip. My return date to the UK would be the 22nd of "
            "October. I will be meeting my girlfriend, who is travelling from the US "
            "to meet me in Jamaica, and we would also like to visit a few places of "
            "interest within St Mary Parish."
        ),
    })

    assert res.status_code == 200
    body = res.json()
    itinerary = body["itinerary"]
    assert itinerary is not None
    brief = itinerary["trip_brief"]
    assert brief["origin"] == "London"
    assert brief["departure_options"] == ["London", "Manchester"]
    assert brief["destination"] == "Jamaica"
    assert brief["local_areas"] == ["St Mary Parish", "Ocho Rios"]
    assert brief["start_date"] == "2026-10-10"
    assert brief["end_date"] == "2026-10-22"
    assert brief["duration_days"] == 12
    assert len(itinerary["daily_outline"]) == 12
    assert brief["stay_plan"] == [
        {
            "start_date": "2026-10-10",
            "end_date": "2026-10-13",
            "area": "Ocho Rios",
            "property_name": "RIU Hotel",
            "style": None,
            "status": "REQUESTED_NOT_BOOKED",
        },
        {
            "start_date": "2026-10-13",
            "end_date": "2026-10-22",
            "area": "St Mary Parish",
            "property_name": None,
            "style": "Budget-friendly hotel",
            "status": "REQUESTED_NOT_BOOKED",
        },
    ]
    assert brief["special_occasion"]["date"] == "2026-10-12"
    assert brief["companion_plan"]["origin"] == "United States"
    assert brief["companion_plan"]["relationship"] == "Girlfriend"
    assert "companion's Jamaica arrival" in " ".join(
        itinerary["booking_readiness"]["items_needed"]
    )
    assert itinerary["daily_outline"][2]["title"] == "Day 3: Birthday celebration"
    assert "RIU Hotel in Ocho Rios" in itinerary["daily_outline"][2]["accommodation"]
    assert "Budget-friendly hotel in St Mary Parish" in itinerary["daily_outline"][3]["accommodation"]
    assert "child" not in str(itinerary["daily_outline"]).lower()
    assert "Office Day" not in str(itinerary["daily_outline"])
    assert "conference" not in str(itinerary["daily_outline"]).lower()
    assert "Spa & Wellness" not in str(itinerary["daily_outline"])


def test_amsterdam_friends_request_preserves_party_hotel_match_and_15_days(client):
    res = client.post("/planner/plan", json={
        "message": (
            "Me and my 2 friends are going to Amsterdam for a week from New York; "
            "we would like to stay in the same hotel and would love to see many "
            "tourist attractions in Amsterdam. We would like to visit Ajax stadium "
            "and also would like a ticket to Ajax vs feynold game. We would like to "
            "travel on the 10th of August from New York to Amsterdam for 15 days."
        ),
    })

    assert res.status_code == 200
    itinerary = res.json()["itinerary"]
    assert itinerary is not None
    brief = itinerary["trip_brief"]
    assert brief["origin"] == "New York"
    assert brief["destination"] == "Amsterdam"
    assert brief["travellers"]["adults"] == 3
    assert brief["duration_days"] == 15
    assert brief["departure_day"] == 10
    inferred_year = datetime.now().year
    assert brief["travel_period"] == (
        f"{inferred_year}-08-10 to {inferred_year}-08-25"
    )
    assert brief["date_precision"] == "EXACT"
    assert brief["date_inference_note"] == (
        f"Year not supplied; using {inferred_year}."
    )
    assert brief["accommodation_preferences"] == [
        "Same hotel for all travellers"
    ]
    assert brief["requested_events"] == [{
        "name": "Ajax vs Feyenoord",
        "type": "Football match",
        "ticket_requested": True,
        "status": "REQUESTED_NOT_CONFIRMED",
    }]
    assert brief["duration_note"] == (
        "Both 7 days and 15 days were supplied; using the later 15-day request."
    )
    assert len(itinerary["daily_outline"]) == 15
    assert itinerary["daily_outline"][1]["title"] == "Day 2: Ajax stadium visit"
    assert itinerary["daily_outline"][2]["title"] == (
        "Day 3: Ajax vs Feyenoord fixture check"
    )
    assert "requested, not confirmed" in itinerary["daily_outline"][2]["notes"]
    assert itinerary["daily_outline"][3]["title"] == (
        "Day 4: Canal belt & Rijksmuseum"
    )
    assert itinerary["daily_outline"][4]["title"] == (
        "Day 5: Van Gogh & Museumplein"
    )
    assert itinerary["daily_outline"][5]["title"] == (
        "Day 6: Anne Frank House & Jordaan"
    )
    assert itinerary["daily_outline"][9]["title"] == (
        "Day 10: Zaanse Schans day trip"
    )
    assert itinerary["daily_outline"][10]["title"] == (
        "Day 11: Haarlem day trip"
    )
    assert itinerary["daily_outline"][13]["title"] == (
        "Day 14: Final priorities & shopping"
    )
    assert len({day["theme"] for day in itinerary["daily_outline"]}) == 15
    assert all(
        "One hotel for all 3 travellers" in day["accommodation"]
        for day in itinerary["daily_outline"]
    )
    needed = " ".join(itinerary["booking_readiness"]["items_needed"])
    assert "Add the travel year" not in needed
    assert "Ajax vs Feyenoord" in needed
    assert "ticket availability" in needed
    assert "New York To Amsterdam" not in str(itinerary)


def test_dublin_family_request_preserves_five_days_and_every_requested_activity(client):
    res = client.post("/planner/plan", json={
        "message": (
            "Plan a 5 days trip to Dublin for a family of 4. A man, a woman and "
            "two kids, a boy and a girl, from the UK. We would be traveling from "
            "London so, any airport with the best or reasonable price. Departure "
            "date would be the 18th of August for 5 days. We would like to stay in "
            "a children friendly hotel in Dublin area not far from the city center. "
            "We would like to visit Gunness factory, visit various tourist "
            "attractions, visit the Wicklow Mountains for a day, go for meals in "
            "nice restaurants around Temple Bar, list other attractions in Dublin "
            "and arrange local hop-on hop-off sightseeing in Dublin."
        ),
    })

    assert res.status_code == 200
    itinerary = res.json()["itinerary"]
    assert itinerary is not None
    brief = itinerary["trip_brief"]
    assert brief["origin"] == "London"
    assert brief["destination"] == "Dublin"
    assert brief["duration_days"] == 5
    assert brief["duration_note"] is None
    assert brief["travellers"] == {"adults": 2, "children": 2, "infants": 0}
    assert brief["departure_day"] == 18
    inferred_year = datetime.now().year
    assert brief["start_date"] == f"{inferred_year}-08-18"
    assert brief["end_date"] == f"{inferred_year}-08-23"
    assert brief["travel_period"] == (
        f"{inferred_year}-08-18 to {inferred_year}-08-23"
    )
    assert brief["date_precision"] == "EXACT"
    assert brief["date_inference_note"] == (
        f"Year not supplied; using {inferred_year}."
    )
    assert brief["airport_preference"] == (
        "Any London airport; prioritise a reasonable price"
    )
    assert brief["accommodation_preferences"] == [
        "Child-friendly hotel",
        "Near Dublin city centre",
    ]
    assert set(brief["requested_activities"]) == {
        "Guinness Storehouse",
        "Wicklow Mountains day trip",
        "Family meal near Temple Bar",
        "Dublin hop-on hop-off sightseeing tour",
        "Additional family-friendly Dublin attractions",
    }
    assert len(itinerary["daily_outline"]) == 5
    assert [day["title"] for day in itinerary["daily_outline"]] == [
        "Day 1: Arrival & easy city-centre orientation",
        "Day 2: Hop-on hop-off Dublin & Guinness Storehouse",
        "Day 3: Dublin family highlights",
        "Day 4: Wicklow Mountains day trip",
        "Day 5: Final Dublin stop & departure",
    ]
    assert all(
        "Child-friendly hotel, Near Dublin city centre — requested, not booked"
        in day["accommodation"]
        for day in itinerary["daily_outline"]
    )
    needed = " ".join(itinerary["booking_readiness"]["items_needed"])
    assert "Add the travel year" not in needed
    assert "Confirm the trip length" not in needed
    assert itinerary["flight_recommendation"] is None
    assert itinerary["accommodation_recommendation"] is None
    accommodation_notice = next(
        notice
        for notice in itinerary["grounding_notices"]
        if notice["domain"] == "accommodation"
    )
    assert accommodation_notice["level"] == "GUIDANCE"
    assert accommodation_notice["is_current"] is False
    assert accommodation_notice["title"] == "Current accommodation search pending"

"""Conversational readiness, memory defaults and semantic safety guards."""


def test_vague_trip_stops_and_asks_one_focused_next_question(client):
    body = client.post(
        "/planner/plan",
        json={"message": "Plan me a trip to Paris"},
    ).json()

    assert body["intent"] == "PLAN_TRIP"
    assert body["itinerary"] is None
    readiness = body["planning_readiness"]
    assert readiness["stage"] == "CLARIFYING"
    assert readiness["can_build_itinerary"] is False
    assert readiness["next_question"] == (
        "When would you like to travel, and how many full days would you like to stay?"
    )
    assert readiness["question_fields"] == ["dates", "duration_days"]


def test_family_plan_is_visible_but_child_ages_are_requested_before_live_search(client):
    body = client.post(
        "/planner/plan",
        json={
            "message": (
                "Plan a 7-day trip from London to New York from 10 October 2026 "
                "to 17 October 2026 for 2 adults and 2 children."
            )
        },
    ).json()

    assert body["itinerary"] is not None
    readiness = body["planning_readiness"]
    assert readiness["stage"] == "INSPIRATION_READY"
    assert readiness["can_build_itinerary"] is True
    assert readiness["can_live_search"] is False
    assert readiness["next_question"] == (
        "What age will each child or infant be on the departure date?"
    )


def test_clarification_turns_keep_the_trip_and_reach_search_readiness(client):
    first = client.post(
        "/planner/plan",
        json={
            "message": (
                "Plan a 7-day trip from London to New York from 10 October 2026 "
                "to 17 October 2026 for 2 adults and 2 children."
            )
        },
    ).json()
    second = client.post(
        "/planner/plan",
        json={
            "conversation_id": first["conversation_id"],
            "message": "The children will be aged 6 and 9.",
        },
    ).json()
    assert second["planning_readiness"]["next_question"] == (
        "What passport nationality does each traveller hold? Please mention any mixed nationalities."
    )

    third = client.post(
        "/planner/plan",
        json={
            "conversation_id": first["conversation_id"],
            "message": "All four travellers are British passport holders.",
        },
    ).json()
    readiness = third["planning_readiness"]
    assert readiness["stage"] == "SEARCH_READY"
    assert readiness["can_live_search"] is True
    assert third["itinerary"]["trip_brief"]["travellers"]["minor_ages"] == [6, 9]
    assert third["itinerary"]["trip_brief"]["nationalities"] == ["British"]


def test_signed_in_profile_defaults_are_used_without_overwriting_trip_facts(client):
    profile = client.post(
        "/traveller/profile",
        json={
            "identity": {
                "name": "Amina",
                "email": "amina@example.com",
                "nationality": "Nigerian",
                "country_of_residence": "United Kingdom",
            },
            "preferences": {
                "home_airport": "Manchester",
                "preferred_currency": "GBP",
                "cabin_class": "economy",
            },
        },
    ).json()

    body = client.post(
        "/planner/plan",
        json={
            "traveller_id": profile["id"],
            "message": (
                "Plan a 5-day trip to Madrid from Leeds from 4 November 2026 "
                "to 9 November 2026 for one adult."
            ),
        },
    ).json()

    brief = body["itinerary"]["trip_brief"]
    assert brief["origin"] == "Leeds"
    assert brief["nationalities"] == ["Nigerian"]
    assert brief["country_of_residence"] == "United Kingdom"
    used = body["planning_readiness"]["profile_fields_used"]
    assert "nationality" in used
    assert "origin" not in used


def test_business_meetings_do_not_change_the_flight_cabin(client):
    body = client.post(
        "/planner/plan",
        json={
            "message": (
                "Plan a 7-day trip from London to Dubai from 2 November 2026 "
                "to 9 November 2026 for one adult with two business meetings."
            )
        },
    ).json()

    assert body["itinerary"]["trip_brief"]["cabin_class"] is None


def test_excursion_day_counts_do_not_replace_the_whole_trip_duration(client):
    body = client.post(
        "/planner/plan",
        json={
            "message": (
                "Plan a 7-day trip from London to Rome from 2 November 2026 "
                "to 9 November 2026 for two adults, including two day trips."
            )
        },
    ).json()

    assert body["itinerary"]["trip_brief"]["duration_days"] == 7


def test_negative_constraints_are_first_class_trip_facts(client):
    body = client.post(
        "/planner/plan",
        json={
            "message": (
                "Plan a 5-day alcohol-free trip from London to Lisbon from "
                "2 November 2026 to 7 November 2026 for two adults. No alcohol."
            )
        },
    ).json()

    assert body["itinerary"]["trip_brief"]["negative_constraints"] == [
        "No alcohol"
    ]


def test_mixed_nationalities_remain_part_of_a_full_trip_plan(client):
    body = client.post(
        "/planner/plan",
        json={
            "message": (
                "Plan a 5-day trip from London to Istanbul from 2 November 2026 "
                "to 7 November 2026 for two adults. We are British and Nigerian."
            )
        },
    ).json()

    assert body["intent"] == "PLAN_TRIP"
    assert body["itinerary"] is not None
    assert body["itinerary"]["trip_brief"]["nationalities"] == [
        "British",
        "Nigerian",
    ]
    visa = body["itinerary"]["visa_summary"]
    assert visa["assessment_scope"] == "PARTIAL"
    assert visa["nationalities_considered"] == ["British", "Nigerian"]
    assert visa["nationalities_pending"] == ["British", "Nigerian"]
    assert len(visa["individual_assessments"]) == 2
    assert "each passport nationality" in " ".join(
        body["itinerary"]["booking_readiness"]["items_needed"]
    )

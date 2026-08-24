"""Progressive trip-readiness assessment for conversational planning.

The planner deliberately separates three different thresholds:

* an inspiration itinerary can be built from destination, timing and party;
* live search also needs a real origin, exact dates and age/nationality facts;
* booking details are collected only after a traveller selects an offer.

This keeps the first interaction conversational without quietly inventing the
facts that materially change fares, entry rules or child suitability.
"""

from __future__ import annotations

from typing import Any


_PROFILE_FIELDS = {
    "origin": ("preferences", "home_airport"),
    "nationality": ("identity", "nationality"),
    "country_of_residence": ("identity", "country_of_residence"),
    "cabin_class": ("preferences", "cabin_class"),
    "accessibility_needs": ("preferences", "accessibility_needs"),
    "interests": ("preferences", "travel_interests"),
    "accommodation_preference": ("preferences", "accommodation_type"),
}

_COUNTRY_ONLY_DESTINATIONS = {
    "france", "ghana", "ireland", "jamaica", "japan", "nigeria", "spain",
    "uae", "united arab emirates", "uk", "united kingdom", "usa",
    "united states", "united states of america",
}


def apply_profile_defaults(
    entities: dict[str, str],
    profile: dict[str, Any] | None,
) -> tuple[dict[str, str], list[str]]:
    """Fill only absent planning facts from the signed-in traveller profile.

    Explicit trip facts always win.  The returned field list makes remembered
    defaults visible to the API and UI instead of applying invisible memory.
    """

    merged = dict(entities)
    used: list[str] = []
    if not profile:
        return merged, used

    for entity_key, path in _PROFILE_FIELDS.items():
        if merged.get(entity_key):
            continue
        value: Any = profile
        for part in path:
            value = value.get(part) if isinstance(value, dict) else None
        if value in (None, "", []):
            continue
        if isinstance(value, list):
            merged[entity_key] = ",".join(str(item).strip() for item in value if str(item).strip())
        else:
            merged[entity_key] = str(value).strip()
        if merged.get(entity_key):
            used.append(entity_key)

    if merged.get("nationality") and not merged.get("nationalities"):
        merged["nationalities"] = merged["nationality"]
    return merged, used


def assess_trip_readiness(
    entities: dict[str, str],
    *,
    profile_fields_used: list[str] | None = None,
) -> dict[str, Any]:
    """Return a stable, customer-facing readiness ledger."""

    profile_fields_used = profile_fields_used or []
    travellers = _party(entities)
    children = travellers["children"]
    infants = travellers["infants"]
    minor_ages = _csv(entities.get("minor_ages"))
    nationalities = _csv(entities.get("nationalities") or entities.get("nationality"))

    exact_dates = bool(entities.get("start_date") and entities.get("end_date"))
    has_timing = bool(entities.get("date_hint") or entities.get("month") or exact_dates)
    has_party = any(entities.get(key) is not None for key in ("adults", "children", "infants"))
    has_destination = bool(entities.get("destination"))
    country_area_needed = bool(
        str(entities.get("destination", "")).casefold() in _COUNTRY_ONLY_DESTINATIONS
        and not entities.get("local_areas")
    )

    essential_checks = [
        ("destination", "Destination", has_destination and not country_area_needed),
        ("dates", "Travel dates or month and trip length", has_timing),
        ("party", "Number of adults, children and infants", has_party),
        ("origin", "Departure city or airport", bool(entities.get("origin"))),
        ("nationalities", "Passport nationality for every traveller", bool(nationalities)),
    ]
    if children or infants:
        expected_ages = children + infants
        essential_checks.append(
            (
                "minor_ages",
                "Age of every child and infant at the time of travel",
                len(minor_ages) >= expected_ages,
            )
        )

    recommended_checks = [
        ("budget", "Total budget and currency", bool(entities.get("budget_amount"))),
        ("interests", "Interests and must-do activities", bool(entities.get("interests") or entities.get("requested_activities"))),
        ("accommodation", "Hotel, room or location preferences", bool(entities.get("accommodation_preference"))),
        ("dietary", "Dietary requirements and allergies", bool(entities.get("dietary_requirements"))),
        ("accessibility", "Accessibility or mobility needs", bool(entities.get("accessibility_needs"))),
    ]

    missing_essential = [label for _, label, present in essential_checks if not present]
    missing_recommended = [label for _, label, present in recommended_checks if not present]
    confirmed = [label for _, label, present in [*essential_checks, *recommended_checks] if present]

    can_build_itinerary = has_destination and has_timing and has_party and not country_area_needed
    can_live_search = can_build_itinerary and exact_dates and not missing_essential

    essential_score = sum(present for _, _, present in essential_checks) / len(essential_checks)
    recommended_score = sum(present for _, _, present in recommended_checks) / len(recommended_checks)
    score = round((essential_score * 75) + (recommended_score * 25))

    next_question, question_fields = _next_question(
        entities,
        has_destination=has_destination,
        country_area_needed=country_area_needed,
        has_timing=has_timing,
        has_party=has_party,
        has_origin=bool(entities.get("origin")),
        nationalities=nationalities,
        expected_minor_ages=children + infants,
        supplied_minor_ages=len(minor_ages),
    )

    if not can_build_itinerary:
        stage = "CLARIFYING"
    elif can_live_search:
        stage = "SEARCH_READY"
    else:
        stage = "INSPIRATION_READY"

    return {
        "stage": stage,
        "score": score,
        "can_build_itinerary": can_build_itinerary,
        "can_live_search": can_live_search,
        # Legal names and dates of birth are intentionally collected only
        # after a real offer is selected; passport numbers are never requested.
        "can_book": False,
        "confirmed_fields": confirmed,
        "missing_essential": missing_essential,
        "missing_recommended": missing_recommended,
        "conflicts": _csv(entities.get("trip_conflicts")),
        "next_question": next_question,
        "question_fields": question_fields,
        "profile_fields_used": profile_fields_used,
        "traveller_summary": {
            **travellers,
            "minor_ages": [int(age) for age in minor_ages if age.isdigit()],
            "nationalities": nationalities,
        },
    }


def _next_question(
    entities: dict[str, str],
    *,
    has_destination: bool,
    country_area_needed: bool,
    has_timing: bool,
    has_party: bool,
    has_origin: bool,
    nationalities: list[str],
    expected_minor_ages: int,
    supplied_minor_ages: int,
) -> tuple[str | None, list[str]]:
    if not has_destination:
        return (
            "Where would you like to go? If you are undecided, tell me the month, budget and kind of experience you want.",
            ["destination"],
        )
    if country_area_needed:
        return (
            f"Which city, town or resort area in {entities['destination']} would you like to use as your base?",
            ["local_areas"],
        )
    if not has_timing:
        return (
            "When would you like to travel, and how many full days would you like to stay?",
            ["dates", "duration_days"],
        )
    if not has_party:
        return (
            "How many adults, children and infants are travelling?",
            ["adults", "children", "infants"],
        )
    if not has_origin:
        return (
            "Which city or airport would you like to depart from? You can name several if you are flexible.",
            ["origin", "departure_options"],
        )
    if expected_minor_ages and supplied_minor_ages < expected_minor_ages:
        return (
            "What age will each child or infant be on the departure date?",
            ["minor_ages"],
        )
    if not nationalities:
        return (
            "What passport nationality does each traveller hold? Please mention any mixed nationalities.",
            ["nationalities"],
        )
    if not entities.get("budget_amount"):
        return (
            "What approximate total budget and currency should I plan around?",
            ["budget_amount", "budget_currency"],
        )
    return None, []


def _party(entities: dict[str, str]) -> dict[str, int]:
    return {
        "adults": _integer(entities.get("adults"), 0),
        "children": _integer(entities.get("children"), 0),
        "infants": _integer(entities.get("infants"), 0),
    }


def _integer(value: Any, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _csv(value: Any) -> list[str]:
    if isinstance(value, list):
        values = value
    else:
        values = str(value or "").split(",")
    return list(dict.fromkeys(str(item).strip() for item in values if str(item).strip()))

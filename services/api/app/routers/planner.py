"""
POST /planner/plan — the AI Travel Planner (T-040): the traveller
describes a trip in natural language and gets back one coherent,
consultant-style itinerary, not six independent module responses.

Reuses `travel_concierge.handle()` entirely — intent classification,
goal/trip creation, and Trip Brain invocation are all unchanged (Trip
Brain remains the sole orchestrator of the six Discovery modules). This
router adds only the Trip Assembly step on top, the same relationship
`POST /explain` (services/api/app/routers/explain.py) already has to
Trip Brain's own output — no Discovery module logic is duplicated here.
"""

from __future__ import annotations

import calendar
from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.auth import AuthenticatedTraveller, require_authenticated_traveller
from app.auth.dependencies import (
    authenticated_traveller_id,
    require_conversation_owner,
)
router = APIRouter(prefix="/planner", tags=["planner"])


class PlanTripRequest(BaseModel):
    message: str
    traveller_id: str | None = None
    conversation_id: str | None = None


class PlanTripResponse(BaseModel):
    conversation_id: str
    intent: str
    response: str
    confidence: float
    assumptions: list[str]
    missing_information: list[str]
    next_actions: list[str]
    goal_id: str | None = None
    trip_id: str | None = None
    # None whenever the conversation turn didn't produce a full Trip
    # Brain recommendation yet (e.g. still gathering destination/dates)
    # — `response`/`missing_information` above carry the follow-up in
    # that case, exactly as POST /conversation/message already does.
    itinerary: dict[str, Any] | None = None


@router.post("/plan", response_model=PlanTripResponse)
async def plan_trip(
    request: PlanTripRequest,
    principal: AuthenticatedTraveller | None = Depends(require_authenticated_traveller),
) -> dict:
    from ai.concierge.conversation_engine import conversation_engine
    from ai.concierge.travel_concierge import travel_concierge

    request.traveller_id = authenticated_traveller_id(
        principal, request.traveller_id
    )
    require_conversation_owner(principal, request.conversation_id)
    reply = await travel_concierge.handle(
        request.message,
        traveller_id=request.traveller_id,
        conversation_id=request.conversation_id,
    )

    itinerary: dict[str, Any] | None = None
    session = conversation_engine.get_session(reply["conversation_id"])
    if session is not None and session.last_recommendation is not None:
        itinerary = _assemble_itinerary(session).to_dict()

    return {**reply, "itinerary": itinerary}


def _assemble_itinerary(session: Any):
    from ai.trip_brain.trip_assembly import trip_assembly_engine

    goal: dict[str, Any] | None = None
    if session.goal_id:
        try:
            from app.domains.goals.service import goal_service
            goal = goal_service.get(session.goal_id)
        except Exception:
            goal = None

    trip: dict[str, Any] | None = None
    if session.trip_id:
        try:
            from app.domains.trips.service import trip_planning_service
            trip = trip_planning_service.get(session.trip_id)
        except Exception:
            trip = None

    entities = dict(getattr(session, "planning_entities", {}) or {})
    unified = session.last_recommendation
    destination = unified.destination
    duration_days = (
        entities.get("duration_days")
        or (trip or {}).get("duration_days")
        or (goal or {}).get("timeframe", {}).get("duration_days")
        or 7
    )
    goal_type = (goal or {}).get("goal_type", "GENERAL_TRAVEL")
    budget_style = (trip or {}).get("travel_style") or "balanced"
    interests = (
        [value for value in entities.get("interests", "").split(",") if value]
        or (goal or {}).get("interests", [])
    )

    return trip_assembly_engine.assemble(
        unified,
        destination=destination,
        duration_days=duration_days,
        goal_type=goal_type,
        budget_style=budget_style,
        interests=interests,
        trip_brief=_build_trip_brief(
            entities=entities,
            goal=goal,
            trip=trip,
            destination=destination,
            duration_days=duration_days,
            interests=interests,
        ),
    )


def _build_trip_brief(
    *,
    entities: dict[str, str],
    goal: dict[str, Any] | None,
    trip: dict[str, Any] | None,
    destination: str,
    duration_days: int,
    interests: list[str],
) -> dict[str, Any]:
    goal = goal or {}
    trip = trip or {}
    timeframe = goal.get("timeframe", {})
    stored_travellers = trip.get("travellers") or goal.get("travellers") or {}
    travellers = {
        "adults": entities.get("adults") or stored_travellers.get("adults") or 1,
        "children": entities.get("children") or stored_travellers.get("children") or 0,
        "infants": entities.get("infants") or stored_travellers.get("infants") or 0,
        "minor_ages": entities.get("minor_ages") or stored_travellers.get("minor_ages") or [],
    }
    budget = goal.get("budget") or trip.get("budget") or {}
    start_date = entities.get("start_date") or timeframe.get("earliest")
    end_date = entities.get("end_date") or timeframe.get("latest")
    month = entities.get("month") or timeframe.get("month")
    year = entities.get("travel_year") or timeframe.get("year")
    date_precision = (
        "EXACT"
        if start_date and end_date
        else entities.get("date_precision")
        or timeframe.get("precision")
        or ("MONTH" if month else "UNSPECIFIED")
    )
    if start_date and end_date:
        travel_period = f"{start_date} to {end_date}"
    elif entities.get("departure_day") and month:
        month_name = calendar.month_name[int(month)]
        day_month = f"{int(entities['departure_day'])} {month_name}"
        travel_period = (
            f"{day_month} {year}" if year else f"{day_month} · year needed"
        )
    elif month:
        month_name = calendar.month_name[int(month)]
        travel_period = f"{month_name} {year}".strip() if year else month_name
    else:
        travel_period = timeframe.get("hint") or "Dates not supplied"

    budget_amount = entities.get("budget_amount")
    if budget_amount is not None:
        numeric_amount = float(budget_amount)
        budget = {
            "amount": (
                int(numeric_amount)
                if numeric_amount.is_integer()
                else numeric_amount
            ),
            "currency": entities.get("budget_currency", "USD"),
            "source": "TRAVELLER_DECLARED",
        }

    departure_options = [
        value for value in entities.get("departure_options", "").split(",") if value
    ]
    local_areas = [
        value for value in entities.get("local_areas", "").split(",") if value
    ]
    stay_plan: list[dict[str, Any]] = []
    for index in (1, 2):
        property_name = entities.get(f"stay_{index}_property")
        style = entities.get(f"stay_{index}_style")
        if not property_name and not style:
            continue
        stay_plan.append({
            "start_date": entities.get(f"stay_{index}_start_date"),
            "end_date": entities.get(f"stay_{index}_end_date"),
            "area": entities.get(f"stay_{index}_area"),
            "property_name": property_name,
            "style": style,
            "status": "REQUESTED_NOT_BOOKED",
        })

    special_occasion = None
    if entities.get("special_occasion"):
        special_occasion = {
            "type": entities["special_occasion"],
            "date": entities.get("special_occasion_date"),
            "notes": entities.get("special_occasion_notes"),
        }

    companion_plan = None
    if entities.get("companion_relationship") or entities.get("companion_origin"):
        companion_plan = {
            "relationship": entities.get("companion_relationship"),
            "origin": entities.get("companion_origin"),
            "arrival_date": entities.get("companion_arrival_date"),
            "departure_date": entities.get("companion_departure_date"),
            "meeting_destination": destination,
        }

    requested_events: list[dict[str, Any]] = []
    if entities.get("requested_event"):
        requested_events.append({
            "name": entities["requested_event"],
            "type": entities.get("requested_event_type") or "Event",
            "ticket_requested": entities.get("ticket_requested") == "true",
            "status": entities.get("requested_event_status")
            or "REQUESTED_NOT_CONFIRMED",
        })

    accommodation_preferences = [
        value
        for value in (
            entities.get("accommodation_preference"),
            entities.get("accommodation_location_preference"),
        )
        if value
    ]
    accommodation_preferences.extend(
        value
        for value in entities.get(
            "additional_accommodation_preferences", ""
        ).split(",")
        if value and value not in accommodation_preferences
    )
    requested_activities = [
        value
        for value in entities.get("requested_activities", "").split(",")
        if value
    ]

    return {
        "origin": entities.get("origin") or trip.get("origin") or "",
        "departure_options": departure_options,
        "airport_preference": entities.get("airport_preference"),
        "destination": destination or trip.get("destination") or "",
        "local_areas": local_areas,
        "duration_days": int(duration_days),
        "start_date": start_date,
        "end_date": end_date,
        "month": int(month) if month else None,
        "year": int(year) if year else None,
        "departure_day": (
            int(entities["departure_day"])
            if entities.get("departure_day")
            else None
        ),
        "date_precision": date_precision,
        "travel_period": travel_period,
        "duration_note": entities.get("duration_conflict"),
        "date_inference_note": entities.get("date_inference_note"),
        "travellers": {
            "adults": int(travellers.get("adults") or 1),
            "children": int(travellers.get("children") or 0),
            "infants": int(travellers.get("infants") or 0),
        },
        "budget": budget,
        "nationality": entities.get("nationality"),
        "interests": list(interests),
        "accommodation_preferences": accommodation_preferences,
        "requested_events": requested_events,
        "requested_activities": requested_activities,
        "stay_plan": stay_plan,
        "special_occasion": special_occasion,
        "companion_plan": companion_plan,
    }

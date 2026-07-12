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

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

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
async def plan_trip(request: PlanTripRequest) -> dict:
    from ai.concierge.conversation_engine import conversation_engine
    from ai.concierge.travel_concierge import travel_concierge

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

    unified = session.last_recommendation
    destination = unified.destination
    duration_days = (
        (trip or {}).get("duration_days")
        or (goal or {}).get("timeframe", {}).get("duration_days")
        or 7
    )
    goal_type = (goal or {}).get("goal_type", "GENERAL_TRAVEL")
    budget_style = (trip or {}).get("travel_style") or "balanced"
    interests = (goal or {}).get("interests", [])

    return trip_assembly_engine.assemble(
        unified,
        destination=destination,
        duration_days=duration_days,
        goal_type=goal_type,
        budget_style=budget_style,
        interests=interests,
    )

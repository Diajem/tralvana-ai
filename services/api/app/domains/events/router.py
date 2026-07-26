from fastapi import APIRouter, Depends, HTTPException

from app.auth import AuthenticatedTraveller, require_authenticated_traveller
from app.auth.dependencies import (
    authenticated_traveller_id,
    require_resource_owner,
    require_trip_owner,
)
from app.domains.events.schemas import (
    EventOptionResponse,
    EventRecommendationResponse,
    RecommendEventsRequest,
)
from app.domains.events.service import event_intelligence_service
from travelos.intelligence_gateway.discovery_adapters import (
    LiveEventSearchUnavailableError,
)

router = APIRouter(tags=["events"])


@router.post(
    "/events/recommend",
    response_model=EventRecommendationResponse,
    status_code=201,
)
async def recommend_events(
    request: RecommendEventsRequest,
    principal: AuthenticatedTraveller | None = Depends(require_authenticated_traveller),
) -> dict:
    request.traveller_id = authenticated_traveller_id(
        principal, request.traveller_id
    )
    require_trip_owner(principal, request.trip_id)
    trip = None
    goal = None
    if request.trip_id:
        try:
            from app.domains.trips.service import trip_planning_service
            trip = trip_planning_service.get(request.trip_id)
            if trip and trip.get("goal_id"):
                from app.domains.goals.service import goal_service
                goal = goal_service.get(trip["goal_id"])
        except Exception:
            pass
    try:
        return event_intelligence_service.recommend(request, trip=trip, goal=goal)
    except LiveEventSearchUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.get("/events/{event_option_id}", response_model=EventOptionResponse)
async def get_event_option(
    event_option_id: str,
    principal: AuthenticatedTraveller | None = Depends(require_authenticated_traveller),
) -> dict:
    option = event_intelligence_service.get(event_option_id)
    if not option:
        raise HTTPException(status_code=404, detail="Event option not found")
    require_resource_owner(principal, option)
    return option


@router.get(
    "/trips/{trip_id}/events",
    response_model=list[EventOptionResponse],
)
async def list_trip_events(
    trip_id: str,
    principal: AuthenticatedTraveller | None = Depends(require_authenticated_traveller),
) -> list[dict]:
    require_trip_owner(principal, trip_id)
    return event_intelligence_service.list_by_trip(trip_id)

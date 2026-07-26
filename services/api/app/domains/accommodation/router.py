from fastapi import APIRouter, Depends, HTTPException

from app.auth import AuthenticatedTraveller, require_authenticated_traveller
from app.auth.dependencies import (
    authenticated_traveller_id,
    require_resource_owner,
    require_trip_owner,
)
from ai.discovery.accommodation.live_search_validator import LiveAccommodationSearchValidationError
from app.domains.accommodation.schemas import (
    AccommodationOptionResponse,
    AccommodationRecommendationResponse,
    RecommendAccommodationRequest,
)
from app.domains.accommodation.service import accommodation_intelligence_service
from travelos.intelligence_gateway.discovery_adapters import LiveAccommodationSearchUnavailableError

router = APIRouter(tags=["accommodation"])


@router.post("/accommodation/recommend", response_model=AccommodationRecommendationResponse, status_code=201)
async def recommend_accommodation(
    request: RecommendAccommodationRequest,
    principal: AuthenticatedTraveller | None = Depends(require_authenticated_traveller),
) -> dict:
    request.traveller_id = authenticated_traveller_id(
        principal, request.traveller_id
    )
    require_trip_owner(principal, request.trip_id)
    trip = None
    if request.trip_id:
        try:
            from app.domains.trips.service import trip_planning_service
            trip = trip_planning_service.get(request.trip_id)
        except Exception:
            pass

    goal = None
    if trip and trip.get("goal_id"):
        try:
            from app.domains.goals.service import goal_service
            goal = goal_service.get(trip["goal_id"])
        except Exception:
            pass

    profile = None
    if request.traveller_id:
        try:
            from ai.memory.traveller_intelligence_service import traveller_intelligence_service
            profile = traveller_intelligence_service.build_context_data(request.traveller_id)
        except Exception:
            pass

    try:
        return accommodation_intelligence_service.recommend(request, trip=trip, goal=goal, profile=profile)
    except LiveAccommodationSearchValidationError as exc:
        raise HTTPException(status_code=422, detail={"errors": exc.errors}) from exc
    except LiveAccommodationSearchUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.get("/accommodation/{accommodation_option_id}", response_model=AccommodationOptionResponse)
async def get_accommodation_option(
    accommodation_option_id: str,
    principal: AuthenticatedTraveller | None = Depends(require_authenticated_traveller),
) -> dict:
    option = accommodation_intelligence_service.get(accommodation_option_id)
    if not option:
        raise HTTPException(status_code=404, detail="Accommodation option not found")
    require_resource_owner(principal, option)
    return option


@router.get("/trips/{trip_id}/accommodation", response_model=list[AccommodationOptionResponse])
async def list_trip_accommodation(
    trip_id: str,
    principal: AuthenticatedTraveller | None = Depends(require_authenticated_traveller),
) -> list[dict]:
    require_trip_owner(principal, trip_id)
    return accommodation_intelligence_service.list_by_trip(trip_id)

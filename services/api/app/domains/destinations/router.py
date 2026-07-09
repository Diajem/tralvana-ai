from fastapi import APIRouter, HTTPException

from app.domains.destinations.schemas import (
    DestinationOptionResponse,
    DestinationRecommendationResponse,
    RecommendDestinationsRequest,
)
from app.domains.destinations.service import destination_intelligence_service

router = APIRouter(tags=["destinations"])


@router.post("/destinations/recommend", response_model=DestinationRecommendationResponse, status_code=201)
async def recommend_destinations(request: RecommendDestinationsRequest) -> dict:
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

    return destination_intelligence_service.recommend(request, trip=trip, goal=goal, profile=profile)


@router.get("/destinations/{destination_option_id}", response_model=DestinationOptionResponse)
async def get_destination_option(destination_option_id: str) -> dict:
    option = destination_intelligence_service.get(destination_option_id)
    if not option:
        raise HTTPException(status_code=404, detail="Destination option not found")
    return option


@router.get("/trips/{trip_id}/destinations", response_model=list[DestinationOptionResponse])
async def list_trip_destinations(trip_id: str) -> list[dict]:
    return destination_intelligence_service.list_by_trip(trip_id)

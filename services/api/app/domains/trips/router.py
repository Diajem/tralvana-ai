from fastapi import APIRouter, HTTPException

from app.domains.trips.schemas import CreateTripPlanRequest, TripPlanResponse, UpdateTripPlanRequest
from app.domains.trips.service import trip_planning_service

router = APIRouter(tags=["trips"])


@router.post("/trips/plan", response_model=TripPlanResponse, status_code=201)
async def plan_trip(request: CreateTripPlanRequest) -> dict:
    goal = None
    if request.goal_id:
        try:
            from app.domains.goals.service import goal_service
            goal = goal_service.get(request.goal_id)
        except Exception:
            pass

    profile = None
    if request.traveller_id:
        try:
            from ai.memory.traveller_intelligence_service import traveller_intelligence_service
            profile = traveller_intelligence_service.build_context_data(request.traveller_id)
        except Exception:
            pass

    return trip_planning_service.plan(request, goal=goal, profile=profile)


@router.get("/trips/{trip_id}", response_model=TripPlanResponse)
async def get_trip(trip_id: str) -> dict:
    trip = trip_planning_service.get(trip_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    return trip


@router.get("/traveller/{traveller_id}/trips", response_model=list[TripPlanResponse])
async def list_traveller_trips(traveller_id: str) -> list[dict]:
    return trip_planning_service.list_by_traveller(traveller_id)


@router.patch("/trips/{trip_id}", response_model=TripPlanResponse)
async def update_trip(trip_id: str, request: UpdateTripPlanRequest) -> dict:
    trip = trip_planning_service.update(trip_id, request)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    return trip

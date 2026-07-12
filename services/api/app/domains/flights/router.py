from fastapi import APIRouter, HTTPException

from ai.discovery.flights.live_search_validator import LiveFlightSearchValidationError
from app.domains.flights.schemas import FlightOptionResponse, FlightRecommendationResponse, RecommendFlightsRequest
from app.domains.flights.service import flight_intelligence_service
from travelos.intelligence_gateway.discovery_adapters import LiveFlightSearchUnavailableError

router = APIRouter(tags=["flights"])


@router.post("/flights/recommend", response_model=FlightRecommendationResponse, status_code=201)
async def recommend_flights(request: RecommendFlightsRequest) -> dict:
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
        return flight_intelligence_service.recommend(request, trip=trip, goal=goal, profile=profile)
    except LiveFlightSearchValidationError as exc:
        raise HTTPException(status_code=422, detail={"errors": exc.errors}) from exc
    except LiveFlightSearchUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.get("/flights/{flight_option_id}", response_model=FlightOptionResponse)
async def get_flight_option(flight_option_id: str) -> dict:
    flight = flight_intelligence_service.get(flight_option_id)
    if not flight:
        raise HTTPException(status_code=404, detail="Flight option not found")
    return flight


@router.get("/trips/{trip_id}/flights", response_model=list[FlightOptionResponse])
async def list_trip_flights(trip_id: str) -> list[dict]:
    return flight_intelligence_service.list_by_trip(trip_id)

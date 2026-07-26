from fastapi import APIRouter, Depends, HTTPException

from app.auth import AuthenticatedTraveller, require_authenticated_traveller
from app.auth.dependencies import (
    authenticated_traveller_id,
    require_resource_owner,
    require_trip_owner,
)
from app.domains.weather.schemas import AnalyseWeatherRequest, WeatherAssessmentResponse
from app.domains.weather.service import weather_intelligence_service

router = APIRouter(tags=["weather"])


@router.post("/weather/analyse", response_model=WeatherAssessmentResponse, status_code=201)
async def analyse_weather(
    request: AnalyseWeatherRequest,
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

    return weather_intelligence_service.analyse(request, trip=trip, goal=goal, profile=profile)


@router.get("/weather/{weather_assessment_id}", response_model=WeatherAssessmentResponse)
async def get_weather_assessment(
    weather_assessment_id: str,
    principal: AuthenticatedTraveller | None = Depends(require_authenticated_traveller),
) -> dict:
    assessment = weather_intelligence_service.get(weather_assessment_id)
    if not assessment:
        raise HTTPException(status_code=404, detail="Weather assessment not found")
    require_resource_owner(principal, assessment)
    return assessment


@router.get("/trips/{trip_id}/weather", response_model=list[WeatherAssessmentResponse])
async def list_trip_weather(
    trip_id: str,
    principal: AuthenticatedTraveller | None = Depends(require_authenticated_traveller),
) -> list[dict]:
    require_trip_owner(principal, trip_id)
    return weather_intelligence_service.list_by_trip(trip_id)

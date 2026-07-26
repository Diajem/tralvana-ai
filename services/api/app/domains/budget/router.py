from fastapi import APIRouter, Depends, HTTPException

from app.auth import AuthenticatedTraveller, require_authenticated_traveller
from app.auth.dependencies import (
    authenticated_traveller_id,
    require_resource_owner,
    require_trip_owner,
)
from app.domains.budget.schemas import (
    BudgetOptionResponse,
    BudgetOptimisationResponse,
    BudgetRecommendationResponse,
    OptimiseBudgetRequest,
    RecommendBudgetRequest,
)
from app.domains.budget.service import budget_intelligence_service

router = APIRouter(tags=["budget"])


@router.post(
    "/budget/optimise",
    response_model=BudgetOptimisationResponse,
)
async def optimise_budget(request: OptimiseBudgetRequest) -> dict:
    return budget_intelligence_service.optimise(request)


@router.post("/budget/recommend", response_model=BudgetRecommendationResponse, status_code=201)
async def recommend_budget(
    request: RecommendBudgetRequest,
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

    return budget_intelligence_service.recommend(request, trip=trip, goal=goal, profile=profile)


@router.get("/budget/{budget_option_id}", response_model=BudgetOptionResponse)
async def get_budget_option(
    budget_option_id: str,
    principal: AuthenticatedTraveller | None = Depends(require_authenticated_traveller),
) -> dict:
    option = budget_intelligence_service.get(budget_option_id)
    if not option:
        raise HTTPException(status_code=404, detail="Budget option not found")
    require_resource_owner(principal, option)
    return option


@router.get("/trips/{trip_id}/budget", response_model=list[BudgetOptionResponse])
async def list_trip_budget(
    trip_id: str,
    principal: AuthenticatedTraveller | None = Depends(require_authenticated_traveller),
) -> list[dict]:
    require_trip_owner(principal, trip_id)
    return budget_intelligence_service.list_by_trip(trip_id)

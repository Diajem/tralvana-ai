from fastapi import APIRouter, Depends, HTTPException, Query

from app.auth import AuthenticatedTraveller, require_authenticated_traveller
from app.auth.dependencies import authenticated_traveller_id, require_owner
from app.domains.goals.schemas import CreateGoalRequest, GoalResponse, UpdateGoalRequest
from app.domains.goals.service import goal_service

router = APIRouter(tags=["goals"])


@router.post("/goals", response_model=GoalResponse, status_code=201)
async def create_goal(
    request: CreateGoalRequest,
    principal: AuthenticatedTraveller | None = Depends(require_authenticated_traveller),
) -> dict:
    request.traveller_id = authenticated_traveller_id(
        principal, request.traveller_id
    )
    return goal_service.create(request)


@router.get("/goals/{goal_id}", response_model=GoalResponse)
async def get_goal(
    goal_id: str,
    principal: AuthenticatedTraveller | None = Depends(require_authenticated_traveller),
) -> dict:
    goal = goal_service.get(goal_id)
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    require_owner(principal, goal["traveller_id"])
    return goal


@router.get("/traveller/{traveller_id}/goals", response_model=list[GoalResponse])
async def list_traveller_goals(
    traveller_id: str,
    limit: int = Query(default=100, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    principal: AuthenticatedTraveller | None = Depends(require_authenticated_traveller),
) -> list[dict]:
    require_owner(principal, traveller_id)
    return goal_service.list_by_traveller(
        traveller_id,
        limit=limit,
        offset=offset,
    )


@router.patch("/goals/{goal_id}", response_model=GoalResponse)
async def update_goal(
    goal_id: str,
    request: UpdateGoalRequest,
    principal: AuthenticatedTraveller | None = Depends(require_authenticated_traveller),
) -> dict:
    existing = goal_service.get(goal_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Goal not found")
    require_owner(principal, existing["traveller_id"])
    goal = goal_service.update(goal_id, request)
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    return goal

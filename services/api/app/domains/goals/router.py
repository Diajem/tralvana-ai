from fastapi import APIRouter, HTTPException

from app.domains.goals.schemas import CreateGoalRequest, GoalResponse, UpdateGoalRequest
from app.domains.goals.service import goal_service

router = APIRouter(tags=["goals"])


@router.post("/goals", response_model=GoalResponse, status_code=201)
async def create_goal(request: CreateGoalRequest) -> dict:
    return goal_service.create(request)


@router.get("/goals/{goal_id}", response_model=GoalResponse)
async def get_goal(goal_id: str) -> dict:
    goal = goal_service.get(goal_id)
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    return goal


@router.get("/traveller/{traveller_id}/goals", response_model=list[GoalResponse])
async def list_traveller_goals(traveller_id: str) -> list[dict]:
    return goal_service.list_by_traveller(traveller_id)


@router.patch("/goals/{goal_id}", response_model=GoalResponse)
async def update_goal(goal_id: str, request: UpdateGoalRequest) -> dict:
    goal = goal_service.update(goal_id, request)
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    return goal

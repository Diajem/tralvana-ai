from __future__ import annotations

from pydantic import BaseModel, Field


class BudgetSchema(BaseModel):
    min_usd: int | None = None
    max_usd: int | None = None
    currency: str = "USD"


class TimeframeSchema(BaseModel):
    earliest: str | None = None     # ISO-8601 date e.g. "2026-09-01"
    latest: str | None = None
    duration_days: int | None = None
    flexible: bool = True


class TravellersSchema(BaseModel):
    adults: int = Field(default=1, ge=1)
    children: int = Field(default=0, ge=0)
    infants: int = Field(default=0, ge=0)


class FlexibilitySchema(BaseModel):
    dates: bool = True
    duration: bool = True
    budget: bool = False


class CreateGoalRequest(BaseModel):
    traveller_id: str
    title: str = Field(min_length=3, max_length=200)
    goal_type: str = "GENERAL_TRAVEL"
    priority: int = Field(default=3, ge=1, le=5)
    budget: BudgetSchema = BudgetSchema()
    timeframe: TimeframeSchema = TimeframeSchema()
    travellers: TravellersSchema = TravellersSchema()
    interests: list[str] = []
    constraints: list[str] = []
    success_criteria: list[str] = []
    flexibility: FlexibilitySchema = FlexibilitySchema()


class UpdateGoalRequest(BaseModel):
    title: str | None = None
    goal_type: str | None = None
    priority: int | None = Field(default=None, ge=1, le=5)
    budget: BudgetSchema | None = None
    timeframe: TimeframeSchema | None = None
    travellers: TravellersSchema | None = None
    interests: list[str] | None = None
    constraints: list[str] | None = None
    success_criteria: list[str] | None = None
    flexibility: FlexibilitySchema | None = None
    status: str | None = None


class GoalResponse(BaseModel):
    goal_id: str
    traveller_id: str
    title: str
    goal_type: str
    priority: int
    budget: dict
    timeframe: dict
    travellers: dict
    interests: list[str]
    constraints: list[str]
    success_criteria: list[str]
    flexibility: dict
    status: str
    created_at: str
    updated_at: str

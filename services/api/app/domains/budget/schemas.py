from __future__ import annotations

from pydantic import BaseModel, Field


class RecommendBudgetRequest(BaseModel):
    traveller_id: str | None = None
    trip_id: str | None = None
    destination: str | None = None        # omit to compare tiers at global-average rates
    goal_type: str | None = None
    budget_style: str = "balanced"         # backpacker | budget | balanced | comfort | luxury
    duration_days: int = Field(default=7, ge=1, le=90)
    adults: int = Field(default=1, ge=1)
    children: int = Field(default=0, ge=0)


class BudgetOptionResponse(BaseModel):
    budget_option_id: str
    traveller_id: str | None
    trip_id: str | None
    destination: str
    region: str
    budget_style: str
    duration_days: int
    adults: int
    children: int
    cabin_class: str
    daily_cost_usd: int
    flight_cost_usd: int
    accommodation_usd: int
    food_usd: int
    activities_usd: int
    misc_usd: int
    total_cost_usd: int
    cost_per_day_usd: int
    cost_per_person_usd: int
    currency: str
    affordability_score: float
    comfort_score: float
    cost_certainty_score: float
    family_suitability_score: float
    match_score: float
    reasoning: str
    risks: list[str]
    assumptions: list[str]
    recommendation_type: str
    created_at: str


class BudgetRecommendationResponse(BaseModel):
    traveller_id: str | None
    trip_id: str | None
    destination: str | None
    budget_options: list[BudgetOptionResponse]
    assumptions: list[str]
    next_actions: list[str]
    recommended_agents: list[str]
    summary: str

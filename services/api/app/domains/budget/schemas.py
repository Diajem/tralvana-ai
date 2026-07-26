from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator

BudgetStyle = Literal[
    "backpacker",
    "budget",
    "balanced",
    "comfort",
    "luxury",
]


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


class BudgetOptimisationTripRequest(BaseModel):
    trip_reference: str = Field(min_length=1, max_length=100)
    destination: str | None = None
    duration_days: int = Field(default=7, ge=1, le=90)
    adults: int = Field(default=1, ge=1, le=20)
    children: int = Field(default=0, ge=0, le=20)
    priority: int = Field(default=3, ge=1, le=5)
    preferred_style: BudgetStyle = "balanced"
    minimum_style: BudgetStyle = "backpacker"

    @model_validator(mode="after")
    def minimum_cannot_exceed_preferred(self):
        order = ["backpacker", "budget", "balanced", "comfort", "luxury"]
        if order.index(self.minimum_style) > order.index(self.preferred_style):
            raise ValueError("minimum_style cannot exceed preferred_style")
        return self


class OptimiseBudgetRequest(BaseModel):
    portfolio_budget_usd: int = Field(gt=0, le=10_000_000)
    trips: list[BudgetOptimisationTripRequest] = Field(
        min_length=1,
        max_length=10,
    )

    @model_validator(mode="after")
    def trip_references_must_be_unique(self):
        references = [trip.trip_reference for trip in self.trips]
        if len(references) != len(set(references)):
            raise ValueError("trip_reference values must be unique")
        return self


class BudgetAllocationResponse(BaseModel):
    trip_reference: str
    destination: str | None
    priority: int
    preferred_style: BudgetStyle
    minimum_style: BudgetStyle
    selected_style: BudgetStyle
    preferred_cost_usd: int
    selected_cost_usd: int
    savings_usd: int
    changed: bool
    tradeoff: str
    cost_breakdown: dict[str, int]
    cost_certainty_score: float
    data_source: str


class BudgetOptimisationResponse(BaseModel):
    feasible: bool
    portfolio_budget_usd: int
    preferred_total_usd: int
    minimum_total_usd: int
    optimised_total_usd: int
    savings_usd: int
    remaining_budget_usd: int
    shortfall_usd: int
    data_source: str
    estimate_confidence: float
    allocations: list[BudgetAllocationResponse]
    assumptions: list[str]
    risks: list[str]
    next_actions: list[str]
    summary: str

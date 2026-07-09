from __future__ import annotations

from pydantic import BaseModel, Field


class RecommendDestinationsRequest(BaseModel):
    traveller_id: str | None = None
    trip_id: str | None = None
    city: str | None = None                  # omit to get city-level recommendations across the catalogue
    interests: list[str] = []
    goal_type: str | None = None
    budget_style: str = "balanced"            # backpacker | budget | balanced | comfort | luxury
    travel_month: int | None = Field(default=None, ge=1, le=12)
    trip_duration_days: int = Field(default=7, ge=1, le=90)
    children: int = Field(default=0, ge=0)


class DestinationOptionResponse(BaseModel):
    destination_option_id: str
    traveller_id: str | None
    trip_id: str | None
    city: str
    country: str
    region: str
    neighbourhood: str
    destination_type: str
    name: str
    description: str
    best_for: list[str]
    interests_matched: list[str]
    distance_from_centre: float
    transport_access_score: float
    food_score: float
    culture_score: float
    football_score: float
    nightlife_score: float
    family_score: float
    safety_score: float
    budget_score: float
    season_score: float
    match_score: float
    reasoning: str
    risks: list[str]
    assumptions: list[str]
    recommendation_type: str
    created_at: str


class DestinationRecommendationResponse(BaseModel):
    traveller_id: str | None
    trip_id: str | None
    city: str | None
    destination_options: list[DestinationOptionResponse]
    assumptions: list[str]
    next_actions: list[str]
    recommended_agents: list[str]
    summary: str

from __future__ import annotations

from pydantic import BaseModel, Field


class TravellersSchema(BaseModel):
    adults: int = Field(default=1, ge=1)
    children: int = Field(default=0, ge=0)
    infants: int = Field(default=0, ge=0)


class CreateTripPlanRequest(BaseModel):
    traveller_id: str | None = None
    goal_id: str | None = None
    origin: str = "London"
    destination: str = ""
    duration_days: int = Field(default=7, ge=1, le=90)
    budget_style: str = "balanced"       # backpacker | budget | balanced | comfort | luxury
    cabin_class: str = "economy"          # economy | business | first
    interests: list[str] = []
    travellers: TravellersSchema = TravellersSchema()


class UpdateTripPlanRequest(BaseModel):
    title: str | None = None
    origin: str | None = None
    destination: str | None = None
    duration_days: int | None = Field(default=None, ge=1, le=90)
    status: str | None = None
    interests: list[str] | None = None


class TripPlanResponse(BaseModel):
    trip_id: str
    traveller_id: str | None
    goal_id: str | None
    title: str
    origin: str
    destination: str
    duration_days: int
    budget: dict
    travellers: dict
    interests: list[str]
    travel_style: str
    assumptions: list[str]
    missing_information: list[str]
    recommended_destinations: list[dict]
    draft_itinerary: list[dict]
    estimated_budget_breakdown: dict
    risks: list[dict]
    confidence: float
    status: str
    created_at: str
    updated_at: str
    recommended_agents: list[str]
    next_actions: list[str]
    trip_summary: str

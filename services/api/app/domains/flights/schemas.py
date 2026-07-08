from __future__ import annotations

from pydantic import BaseModel, Field


class RecommendFlightsRequest(BaseModel):
    traveller_id: str | None = None
    trip_id: str | None = None
    origin: str = "London"
    destination: str = ""
    departure_date: str | None = None       # YYYY-MM-DD; defaulted by the engine if omitted
    return_date: str | None = None
    cabin_class: str = "economy"             # economy | business | first
    budget_style: str = "balanced"           # backpacker | budget | balanced | comfort | luxury
    airline_preference: str | None = None
    adults: int = Field(default=1, ge=1)
    trip_duration_days: int = Field(default=7, ge=1, le=90)


class FlightOptionResponse(BaseModel):
    flight_option_id: str
    traveller_id: str | None
    trip_id: str | None
    origin: str
    destination: str
    departure_date: str
    return_date: str | None
    airline: str
    flight_number: str
    cabin_class: str
    stops: int
    layover_duration: str
    departure_time: str
    arrival_time: str
    total_duration: str
    estimated_price: float
    currency: str
    baggage_included: bool
    refundability: str
    flexibility: str
    match_score: float
    reasoning: str
    risks: list[str]
    assumptions: list[str]
    recommendation_type: str
    created_at: str


class FlightRecommendationResponse(BaseModel):
    traveller_id: str | None
    trip_id: str | None
    origin: str
    destination: str
    flight_options: list[FlightOptionResponse]
    assumptions: list[str]
    next_actions: list[str]
    recommended_agents: list[str]
    summary: str

from __future__ import annotations

from pydantic import BaseModel, Field


class RecommendAccommodationRequest(BaseModel):
    traveller_id: str | None = None
    trip_id: str | None = None
    destination: str = ""
    check_in_date: str | None = None        # YYYY-MM-DD; defaulted by the engine if omitted
    nights: int = Field(default=7, ge=1, le=90)
    accommodation_type: str | None = None    # one of AccommodationType, or None for no preference
    budget_style: str = "balanced"           # backpacker | budget | balanced | comfort | luxury
    adults: int = Field(default=1, ge=1)
    children: int = Field(default=0, ge=0)
    rooms: int = Field(default=1, ge=1)      # T-039 — forwarded to Duffel Stays; ignored by MockAccommodationProvider
    business_trip: bool = False
    accessibility_required: bool = False


class AccommodationOptionResponse(BaseModel):
    accommodation_option_id: str
    traveller_id: str | None
    trip_id: str | None
    destination: str
    property_name: str
    accommodation_type: str
    star_rating: int
    neighbourhood: str
    distance_to_centre: float
    distance_to_transport: float
    nightly_price: float
    total_price: float
    currency: str
    breakfast_included: bool
    cancellation_policy: str
    accessibility_features: list[str]
    family_friendly: bool
    business_friendly: bool
    review_score: float
    safety_score: float
    comfort_score: float
    location_score: float
    match_score: float
    reasoning: str
    risks: list[str]
    assumptions: list[str]
    recommendation_type: str
    created_at: str
    data_source: str = "MOCK"


class AccommodationRecommendationResponse(BaseModel):
    traveller_id: str | None
    trip_id: str | None
    destination: str
    accommodation_options: list[AccommodationOptionResponse]
    assumptions: list[str]
    next_actions: list[str]
    recommended_agents: list[str]
    summary: str
    # Safe provenance metadata only (T-039, docs/LIVE_ACCOMMODATION_SEARCH.md)
    # — never a header, token, or raw provider payload. Additive fields
    # with defaults, so this is not a breaking change to the response shape.
    data_source: str = "MOCK"              # MOCK | DUFFEL_STAYS_SANDBOX | MOCK_FALLBACK
    provider_status: str = "AVAILABLE"
    retrieved_at: str = ""
    request_id: str = ""
    raw_results_count: int = 0
    normalised_results_count: int = 0
    ranked_results_count: int = 0

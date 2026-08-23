from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field, model_validator


class RecommendEventsRequest(BaseModel):
    traveller_id: str | None = None
    trip_id: str | None = None
    destination: str = Field(min_length=1, max_length=120)
    start_date: date | None = None
    end_date: date | None = None
    interests: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def dates_are_ordered(self) -> "RecommendEventsRequest":
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValueError("end_date must be on or after start_date")
        return self


class EventOptionResponse(BaseModel):
    event_option_id: str
    traveller_id: str | None
    trip_id: str | None
    destination: str
    name: str
    category: str
    venue_area: str
    description: str
    starts_at: str | None
    ends_at: str | None
    local_date: str | None
    local_time: str | None
    date_status: str
    availability_status: str
    ticket_url: str | None
    requires_ticket: bool
    team_level: str
    interests_matched: list[str]
    match_score: float
    reasoning: str
    risks: list[str]
    assumptions: list[str]
    recommendation_type: str
    data_source: str
    provider_status: str
    retrieved_at: str | None
    created_at: str


class EventRecommendationResponse(BaseModel):
    traveller_id: str | None
    trip_id: str | None
    destination: str
    start_date: str | None
    end_date: str | None
    event_options: list[EventOptionResponse]
    data_source: str
    provider_status: str
    retrieved_at: str | None
    assumptions: list[str]
    next_actions: list[str]
    recommended_agents: list[str]
    summary: str
    filter_summary: dict[str, int]

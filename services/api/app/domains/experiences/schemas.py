from __future__ import annotations

from datetime import date
from typing import Any

from pydantic import BaseModel, Field, model_validator


class ExperienceSearchRequest(BaseModel):
    destination: str = Field(min_length=2, max_length=120)
    start_date: date | None = None
    end_date: date | None = None
    currency: str = Field(default="GBP", min_length=3, max_length=3)
    count: int = Field(default=20, ge=1, le=50)

    @model_validator(mode="after")
    def dates_are_ordered(self) -> "ExperienceSearchRequest":
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValueError("end_date must be on or after start_date")
        self.currency = self.currency.upper()
        return self


class ExperienceSearchResponse(BaseModel):
    destination: str
    destination_id: str
    products: list[dict[str, Any]]
    provider: str
    environment: str
    booking_enabled: bool
    retrieved_at: str


class ExperienceDetailsResponse(BaseModel):
    product: dict[str, Any]
    availability_schedule: dict[str, Any] | None = None
    provider: str
    environment: str
    booking_enabled: bool
    retrieved_at: str

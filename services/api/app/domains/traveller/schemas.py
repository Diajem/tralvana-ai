"""Traveller API request and response schemas."""

from pydantic import BaseModel, Field


class IdentitySchema(BaseModel):
    name: str
    email: str
    locale: str = "en"
    timezone: str = "UTC"


class PreferencesSchema(BaseModel):
    home_airport: str = ""
    preferred_currency: str = "USD"
    preferred_language: str = "en"
    budget_style: str = "balanced"
    travel_interests: list[str] = Field(default_factory=list)
    seat: str = "no_preference"
    cabin_class: str = "economy"
    meal: str = "standard"
    accommodation_type: str = "hotel"
    hotel_preferences: list[str] = Field(default_factory=list)
    accessibility_needs: list[str] = Field(default_factory=list)


class AirlineLoyaltySchema(BaseModel):
    carrier: str
    number: str


class HotelLoyaltySchema(BaseModel):
    brand: str
    number: str


class LoyaltySchema(BaseModel):
    airline_programs: list[AirlineLoyaltySchema] = Field(default_factory=list)
    hotel_programs: list[HotelLoyaltySchema] = Field(default_factory=list)


class CreateProfileRequest(BaseModel):
    identity: IdentitySchema
    preferences: PreferencesSchema = Field(default_factory=PreferencesSchema)
    loyalty: LoyaltySchema = Field(default_factory=LoyaltySchema)


class TravellerProfileResponse(BaseModel):
    id: str
    created_at: str
    updated_at: str
    identity: IdentitySchema
    preferences: PreferencesSchema
    loyalty: LoyaltySchema
    travel_history: list[dict] = Field(default_factory=list)

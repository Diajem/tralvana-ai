from pydantic import BaseModel


class IdentitySchema(BaseModel):
    name: str
    email: str
    locale: str = "en"
    timezone: str = "UTC"


class PreferencesSchema(BaseModel):
    seat: str = "no_preference"
    cabin_class: str = "economy"
    meal: str = "standard"
    accommodation_type: str = "hotel"
    budget_tier: str = "mid"


class AirlineLoyaltySchema(BaseModel):
    carrier: str
    number: str


class HotelLoyaltySchema(BaseModel):
    brand: str
    number: str


class LoyaltySchema(BaseModel):
    airline_programs: list[AirlineLoyaltySchema] = []
    hotel_programs: list[HotelLoyaltySchema] = []


class CreateProfileRequest(BaseModel):
    identity: IdentitySchema
    preferences: PreferencesSchema = PreferencesSchema()
    loyalty: LoyaltySchema = LoyaltySchema()


class TravellerProfileResponse(BaseModel):
    id: str
    created_at: str
    updated_at: str
    identity: IdentitySchema
    preferences: PreferencesSchema
    loyalty: LoyaltySchema
    travel_history: list = []

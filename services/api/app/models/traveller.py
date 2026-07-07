from pydantic import BaseModel


class IdentitySchema(BaseModel):
    name: str
    email: str
    locale: str = "en"
    timezone: str = "UTC"


class PreferencesSchema(BaseModel):
    # Travel basics
    home_airport: str = ""
    preferred_currency: str = "USD"
    preferred_language: str = "en"
    budget_style: str = "balanced"  # backpacker | budget | balanced | comfort | luxury
    travel_interests: list[str] = []  # beach, city, adventure, culture, food_drink, wellness, sport, nature, luxury, business

    # Flight
    seat: str = "no_preference"  # window | aisle | no_preference
    cabin_class: str = "economy"  # economy | business | first
    meal: str = "standard"  # standard | vegetarian | vegan | halal | kosher

    # Accommodation
    accommodation_type: str = "hotel"  # hotel | apartment | hostel | resort
    hotel_preferences: list[str] = []  # pool, gym, wifi, breakfast, spa, parking, pet_friendly

    # Accessibility
    accessibility_needs: list[str] = []  # wheelchair_access, visual_assistance, hearing_assistance, extra_legroom, dietary_options


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

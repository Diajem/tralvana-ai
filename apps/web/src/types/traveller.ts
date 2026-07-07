export interface TravellerIdentity {
  name: string;
  email: string;
  locale: string;
  timezone: string;
}

export interface TravellerPreferences {
  seat: "window" | "aisle" | "no_preference";
  cabin_class: "economy" | "business" | "first";
  meal: string;
  accommodation_type: string;
  budget_tier: "budget" | "mid" | "luxury";
}

export interface AirlineLoyalty {
  carrier: string;
  number: string;
}

export interface HotelLoyalty {
  brand: string;
  number: string;
}

export interface TravellerLoyalty {
  airline_programs: AirlineLoyalty[];
  hotel_programs: HotelLoyalty[];
}

export interface TravellerProfile {
  id: string;
  created_at: string;
  updated_at: string;
  identity: TravellerIdentity;
  preferences: TravellerPreferences;
  loyalty: TravellerLoyalty;
  travel_history: unknown[];
}

export interface CreateProfileRequest {
  identity: TravellerIdentity;
  preferences: TravellerPreferences;
  loyalty: TravellerLoyalty;
}

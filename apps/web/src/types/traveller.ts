export interface TravellerIdentity {
  name: string;
  email: string;
  locale: string;
  timezone: string;
}

export interface TravellerPreferences {
  // Travel basics
  home_airport: string;
  preferred_currency: string;
  preferred_language: string;
  budget_style: "backpacker" | "budget" | "balanced" | "comfort" | "luxury";
  travel_interests: string[];

  // Flight
  seat: "window" | "aisle" | "no_preference";
  cabin_class: "economy" | "business" | "first";
  meal: string;

  // Accommodation
  accommodation_type: string;
  hotel_preferences: string[];

  // Accessibility
  accessibility_needs: string[];
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

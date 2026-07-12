export type AccommodationType =
  | "HOTEL"
  | "APARTMENT"
  | "HOSTEL"
  | "VILLA"
  | "RESORT"
  | "SERVICED_APARTMENT"
  | "BOUTIQUE_HOTEL"
  | "GUESTHOUSE";

export type RecommendationType =
  | "BEST_OVERALL"
  | "BEST_VALUE"
  | "BEST_LOCATION"
  | "BEST_COMFORT"
  | "BEST_FOR_FAMILY"
  | "BEST_FOR_BUSINESS"
  | "BEST_BUDGET"
  | "AVOID";

export type AccommodationDataSource = "MOCK" | "DUFFEL_STAYS_SANDBOX" | "MOCK_FALLBACK";

export interface AccommodationOption {
  accommodation_option_id: string;
  traveller_id: string | null;
  trip_id: string | null;
  destination: string;
  property_name: string;
  accommodation_type: AccommodationType;
  star_rating: number;
  neighbourhood: string;
  distance_to_centre: number;
  distance_to_transport: number;
  nightly_price: number;
  total_price: number;
  currency: string;
  breakfast_included: boolean;
  cancellation_policy: string;
  accessibility_features: string[];
  family_friendly: boolean;
  business_friendly: boolean;
  review_score: number;
  safety_score: number;
  comfort_score: number;
  location_score: number;
  match_score: number;
  reasoning: string;
  risks: string[];
  assumptions: string[];
  recommendation_type: RecommendationType;
  created_at: string;
  data_source: AccommodationDataSource;
}

export interface AccommodationRecommendationResponse {
  traveller_id: string | null;
  trip_id: string | null;
  destination: string;
  accommodation_options: AccommodationOption[];
  assumptions: string[];
  next_actions: string[];
  recommended_agents: string[];
  summary: string;
  // Safe provenance metadata (T-039) — never a header, token, or raw
  // provider payload, see docs/LIVE_ACCOMMODATION_SEARCH.md.
  data_source: AccommodationDataSource;
  provider_status: string;
  retrieved_at: string;
  request_id: string;
  raw_results_count: number;
  normalised_results_count: number;
  ranked_results_count: number;
}

export interface RecommendAccommodationRequest {
  traveller_id?: string;
  trip_id?: string;
  destination?: string;
  check_in_date?: string;
  nights?: number;
  accommodation_type?: string;
  budget_style?: string;
  adults?: number;
  children?: number;
  rooms?: number;
  business_trip?: boolean;
  accessibility_required?: boolean;
}

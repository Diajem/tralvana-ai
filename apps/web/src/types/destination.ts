export type DestinationType =
  | "CITY"
  | "NEIGHBOURHOOD"
  | "ATTRACTION"
  | "MUSEUM"
  | "FOOD_DISTRICT"
  | "FOOTBALL_VENUE"
  | "SHOPPING_DISTRICT"
  | "BEACH"
  | "NATURE_AREA"
  | "HISTORIC_SITE"
  | "TRANSPORT_HUB"
  | "NIGHTLIFE_AREA";

export type RecommendationType =
  | "BEST_OVERALL"
  | "BEST_FOR_FOOD"
  | "BEST_FOR_FOOTBALL"
  | "BEST_FOR_CULTURE"
  | "BEST_FOR_FAMILY"
  | "BEST_FOR_BUDGET"
  | "BEST_FOR_PHOTOGRAPHY"
  | "BEST_HIDDEN_GEM"
  | "AVOID";

export interface DestinationOption {
  destination_option_id: string;
  traveller_id: string | null;
  trip_id: string | null;
  city: string;
  country: string;
  region: string;
  neighbourhood: string;
  destination_type: DestinationType;
  name: string;
  description: string;
  best_for: string[];
  interests_matched: string[];
  distance_from_centre: number;
  transport_access_score: number;
  food_score: number;
  culture_score: number;
  football_score: number;
  nightlife_score: number;
  family_score: number;
  safety_score: number;
  budget_score: number;
  season_score: number;
  match_score: number;
  reasoning: string;
  risks: string[];
  assumptions: string[];
  recommendation_type: RecommendationType;
  created_at: string;
}

export interface DestinationRecommendationResponse {
  traveller_id: string | null;
  trip_id: string | null;
  city: string | null;
  destination_options: DestinationOption[];
  assumptions: string[];
  next_actions: string[];
  recommended_agents: string[];
  summary: string;
}

export interface RecommendDestinationsRequest {
  traveller_id?: string;
  trip_id?: string;
  city?: string;
  interests?: string[];
  goal_type?: string;
  budget_style?: string;
  travel_month?: number;
  trip_duration_days?: number;
  children?: number;
}

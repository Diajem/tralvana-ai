export type RecommendationType =
  | "BEST_OVERALL"
  | "LOWEST_PRICE"
  | "SHORTEST_DURATION"
  | "BEST_FOR_FAMILY"
  | "BEST_FOR_BUSINESS"
  | "BEST_FOR_COMFORT"
  | "BEST_FOR_BUDGET"
  | "AVOID";

export interface FlightOption {
  flight_option_id: string;
  traveller_id: string | null;
  trip_id: string | null;
  origin: string;
  destination: string;
  departure_date: string;
  return_date: string | null;
  airline: string;
  flight_number: string;
  cabin_class: string;
  stops: number;
  layover_duration: string;
  departure_time: string;
  arrival_time: string;
  total_duration: string;
  estimated_price: number;
  currency: string;
  baggage_included: boolean;
  refundability: string;
  flexibility: string;
  match_score: number;
  reasoning: string;
  risks: string[];
  assumptions: string[];
  recommendation_type: RecommendationType;
  created_at: string;
}

export interface FlightRecommendationResponse {
  traveller_id: string | null;
  trip_id: string | null;
  origin: string;
  destination: string;
  flight_options: FlightOption[];
  assumptions: string[];
  next_actions: string[];
  recommended_agents: string[];
  summary: string;
}

export interface RecommendFlightsRequest {
  traveller_id?: string;
  trip_id?: string;
  origin?: string;
  destination?: string;
  departure_date?: string;
  return_date?: string;
  cabin_class?: string;
  budget_style?: string;
  airline_preference?: string;
  adults?: number;
  trip_duration_days?: number;
}

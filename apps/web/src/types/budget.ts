export type RecommendationType =
  | "BEST_OVERALL"
  | "LOWEST_COST"
  | "MOST_COMFORTABLE"
  | "BEST_VALUE"
  | "BEST_FOR_FAMILY"
  | "AVOID";

export interface BudgetOption {
  budget_option_id: string;
  traveller_id: string | null;
  trip_id: string | null;
  destination: string;
  region: string;
  budget_style: string;
  duration_days: number;
  adults: number;
  children: number;
  cabin_class: string;
  daily_cost_usd: number;
  flight_cost_usd: number;
  accommodation_usd: number;
  food_usd: number;
  activities_usd: number;
  misc_usd: number;
  total_cost_usd: number;
  cost_per_day_usd: number;
  cost_per_person_usd: number;
  currency: string;
  affordability_score: number;
  comfort_score: number;
  cost_certainty_score: number;
  family_suitability_score: number;
  match_score: number;
  reasoning: string;
  risks: string[];
  assumptions: string[];
  recommendation_type: RecommendationType;
  created_at: string;
}

export interface BudgetRecommendationResponse {
  traveller_id: string | null;
  trip_id: string | null;
  destination: string | null;
  budget_options: BudgetOption[];
  assumptions: string[];
  next_actions: string[];
  recommended_agents: string[];
  summary: string;
}

export interface RecommendBudgetRequest {
  traveller_id?: string;
  trip_id?: string;
  destination?: string;
  goal_type?: string;
  budget_style?: string;
  duration_days?: number;
  adults?: number;
  children?: number;
}

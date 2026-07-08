export type TripStatus = "DRAFT" | "NEEDS_INFORMATION" | "READY" | "ARCHIVED";

export interface TripBudget {
  min_usd: number | null;
  max_usd: number | null;
  currency: string;
}

export interface TripTravellers {
  adults: number;
  children: number;
  infants: number;
}

export interface DayPlan {
  day: number;
  title: string;
  theme: string;
  morning: string;
  afternoon: string;
  evening: string;
  accommodation: string;
  estimated_daily_cost_usd: number;
  notes: string;
}

export interface BudgetBreakdown {
  flights_usd: number;
  accommodation_usd: number;
  food_usd: number;
  activities_usd: number;
  miscellaneous_usd: number;
  total_estimate_usd: number;
  per_person_usd: number;
  total_range_usd: { low: number; high: number };
  basis: string;
  source: string;
  notes: string[];
}

export interface TripRisk {
  type: string;
  severity: "low" | "medium" | "high";
  description: string;
  mitigation: string;
}

export interface RecommendedDestination {
  city: string;
  country: string;
  reason: string;
}

export interface TripPlan {
  trip_id: string;
  traveller_id: string | null;
  goal_id: string | null;
  title: string;
  origin: string;
  destination: string;
  duration_days: number;
  budget: TripBudget;
  travellers: TripTravellers;
  interests: string[];
  travel_style: string;
  assumptions: string[];
  missing_information: string[];
  recommended_destinations: RecommendedDestination[];
  draft_itinerary: DayPlan[];
  estimated_budget_breakdown: BudgetBreakdown;
  risks: TripRisk[];
  confidence: float;
  status: TripStatus;
  created_at: string;
  updated_at: string;
  recommended_agents: string[];
  next_actions: string[];
  trip_summary: string;
}

export interface CreateTripPlanRequest {
  traveller_id?: string;
  goal_id?: string;
  origin?: string;
  destination?: string;
  duration_days?: number;
  budget_style?: string;
  cabin_class?: string;
  interests?: string[];
  travellers?: TripTravellers;
}

type float = number;

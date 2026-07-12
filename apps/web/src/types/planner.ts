// AI Travel Planner (T-040) — the assembled itinerary shape returned by
// POST /planner/plan. Every field here is read from an existing
// Discovery module or the Explainability Engine's own output — nothing
// is scored or invented on the frontend either.

export interface TripItinerary {
  executive_summary: string;
  destination_recommendation: Record<string, unknown> | null;
  flight_recommendation: Record<string, unknown> | null;
  accommodation_recommendation: Record<string, unknown> | null;
  budget_summary: Record<string, unknown> | null;
  visa_summary: Record<string, unknown> | null;
  weather_expectations: Record<string, unknown> | null;
  risks: string[];
  assumptions: string[];
  daily_outline: DailyOutlineEntry[];
  why_this_itinerary: { module: string; driver: string }[];
  confidence: number;
  confidence_explanation: string;
  alternative_options: { module: string; alternative: string; why_not_chosen: string }[];
  modules_used: string[];
  modules_unavailable: string[];
}

export interface DailyOutlineEntry {
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

export interface PlanTripRequest {
  message: string;
  traveller_id?: string;
  conversation_id?: string;
}

export interface PlanTripResponse {
  conversation_id: string;
  intent: string;
  response: string;
  confidence: number;
  assumptions: string[];
  missing_information: string[];
  next_actions: string[];
  goal_id: string | null;
  trip_id: string | null;
  itinerary: TripItinerary | null;
}

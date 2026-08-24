// AI Travel Planner (T-040) — the assembled itinerary shape returned by
// POST /planner/plan. Every field here is read from an existing
// Discovery module or the Explainability Engine's own output — nothing
// is scored or invented on the frontend either.

export interface TripItinerary {
  executive_summary: string;
  trip_brief: TripBrief;
  booking_readiness: BookingReadiness;
  destination_recommendation: Record<string, unknown> | null;
  flight_recommendation: Record<string, unknown> | null;
  accommodation_recommendation: Record<string, unknown> | null;
  budget_summary: Record<string, unknown> | null;
  visa_summary: Record<string, unknown> | null;
  weather_expectations: Record<string, unknown> | null;
  event_recommendations: EventRecommendation[];
  risks: string[];
  assumptions: string[];
  daily_outline: DailyOutlineEntry[];
  why_this_itinerary: { module: string; driver: string }[];
  confidence: number;
  confidence_explanation: string;
  alternative_options: { module: string; alternative: string; why_not_chosen: string }[];
  grounding_notices: GroundingNotice[];
  modules_used: string[];
  modules_unavailable: string[];
}

export interface TripBrief {
  origin: string;
  departure_options: string[];
  airport_preference: string | null;
  destination: string;
  destination_region: string | null;
  local_areas: string[];
  duration_days: number;
  start_date: string | null;
  end_date: string | null;
  month: number | null;
  year: number | null;
  departure_day: number | null;
  date_precision: string;
  travel_period: string;
  duration_note: string | null;
  date_inference_note: string | null;
  travellers: {
    adults: number;
    children: number;
    infants: number;
    minor_ages?: number[];
  };
  budget: {
    amount?: number | null;
    currency?: string;
    source?: string;
  };
  nationality: string | null;
  nationalities: string[];
  country_of_residence: string | null;
  cabin_class: string | null;
  dining_out_count: number | null;
  baggage_information_requested: boolean;
  accessibility_needs: string[];
  dietary_requirements: string[];
  negative_constraints: string[];
  interests: string[];
  accommodation_preferences: string[];
  requested_events: RequestedEvent[];
  requested_activities: string[];
  stay_plan: StayPlanSegment[];
  special_occasion: {
    type: string;
    date: string | null;
    notes: string | null;
  } | null;
  companion_plan: {
    relationship: string | null;
    origin: string | null;
    arrival_date: string | null;
    departure_date: string | null;
    meeting_destination: string | null;
  } | null;
}

export interface RequestedEvent {
  name: string;
  type: string;
  ticket_requested: boolean;
  status: "REQUESTED_NOT_CONFIRMED";
}

export interface StayPlanSegment {
  start_date: string | null;
  end_date: string | null;
  area: string | null;
  property_name: string | null;
  style: string | null;
  status: "REQUESTED_NOT_BOOKED";
}

export interface BookingReadiness {
  score: number;
  status: string;
  items_needed: string[];
  budget_status: string;
  explanation: string;
}

export interface EventRecommendation extends Record<string, unknown> {
  event_option_id: string;
  name: string;
  category: string;
  venue_area: string;
  description: string;
  starts_at: string | null;
  ends_at: string | null;
  local_date: string | null;
  local_time: string | null;
  date_status: string;
  availability_status: string;
  ticket_url: string | null;
  team_level: string;
  interests_matched: string[];
  data_source: string;
  image_url: string | null;
  image_alt: string | null;
  image_source: string | null;
}

export interface GroundingNotice {
  domain: string;
  level: "LIVE" | "SANDBOX" | "ESTIMATE" | "CURATED" | "GUIDANCE" | "CLIMATE_PROFILE" | "IDEA";
  title: string;
  message: string;
  data_source: string;
  is_current: boolean;
  requires_confirmation: boolean;
  retrieved_at: string | null;
}

export interface DailyOutlineEntry {
  day: number;
  title: string;
  theme: string;
  morning: string;
  afternoon: string;
  evening: string;
  accommodation: string;
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
  planning_readiness: PlanningReadiness | null;
}

export interface PlanningReadiness {
  stage: "CLARIFYING" | "INSPIRATION_READY" | "SEARCH_READY";
  score: number;
  can_build_itinerary: boolean;
  can_live_search: boolean;
  can_book: boolean;
  confirmed_fields: string[];
  missing_essential: string[];
  missing_recommended: string[];
  conflicts: string[];
  next_question: string | null;
  question_fields: string[];
  profile_fields_used: string[];
  traveller_summary: {
    adults: number;
    children: number;
    infants: number;
    minor_ages: number[];
    nationalities: string[];
  };
}

export interface SavedPlanSummary {
  conversation_id: string;
  trip_id: string | null;
  title: string;
  origin: string;
  destination: string;
  travel_period: string;
  status: string;
  created_at: string;
  updated_at: string;
}

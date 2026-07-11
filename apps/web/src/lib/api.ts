import type { CreateProfileRequest, TravellerProfile } from "@/types/traveller";
export type DemoResponse = Record<string, any>;
import type { CreateGoalRequest, Goal } from "@/types/goal";
import type { CreateTripPlanRequest, TripPlan } from "@/types/trip";
import type { FlightOption, FlightRecommendationResponse, RecommendFlightsRequest } from "@/types/flight";
import type {
  AccommodationOption,
  AccommodationRecommendationResponse,
  RecommendAccommodationRequest,
} from "@/types/accommodation";
import type {
  DestinationOption,
  DestinationRecommendationResponse,
  RecommendDestinationsRequest,
} from "@/types/destination";
import type {
  BudgetOption,
  BudgetRecommendationResponse,
  RecommendBudgetRequest,
} from "@/types/budget";
import type { CheckVisaRequest, VisaAssessment } from "@/types/visa";
import type { AnalyseWeatherRequest, WeatherAssessment } from "@/types/weather";
import type { Explanation, ExplainRequest } from "@/types/explain";

const BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export async function createProfile(
  data: CreateProfileRequest
): Promise<TravellerProfile> {
  const res = await fetch(`${BASE_URL}/traveller/profile`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    throw new Error(`Failed to create profile: ${res.status}`);
  }
  return res.json();
}

export async function getProfile(id: string): Promise<TravellerProfile> {
  const res = await fetch(`${BASE_URL}/traveller/profile/${id}`, {
    cache: "no-store",
  });
  if (!res.ok) {
    throw new Error(`Profile not found: ${res.status}`);
  }
  return res.json();
}

// ------------------------------------------------------------------
// Goal API
// ------------------------------------------------------------------

export async function createGoal(data: CreateGoalRequest): Promise<Goal> {
  const res = await fetch(`${BASE_URL}/goals`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    throw new Error(`Failed to create goal: ${res.status}`);
  }
  return res.json();
}

export async function getGoal(goalId: string): Promise<Goal> {
  const res = await fetch(`${BASE_URL}/goals/${goalId}`, { cache: "no-store" });
  if (!res.ok) {
    throw new Error(`Goal not found: ${res.status}`);
  }
  return res.json();
}

export async function getTravellerGoals(travellerId: string): Promise<Goal[]> {
  const res = await fetch(`${BASE_URL}/traveller/${travellerId}/goals`, {
    cache: "no-store",
  });
  if (!res.ok) {
    throw new Error(`Failed to load goals: ${res.status}`);
  }
  return res.json();
}

// ------------------------------------------------------------------
// Trip API
// ------------------------------------------------------------------

export async function createTripPlan(
  data: CreateTripPlanRequest
): Promise<TripPlan> {
  const res = await fetch(`${BASE_URL}/trips/plan`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    throw new Error(`Failed to create trip plan: ${res.status}`);
  }
  return res.json();
}

export async function getTripPlan(tripId: string): Promise<TripPlan> {
  const res = await fetch(`${BASE_URL}/trips/${tripId}`, { cache: "no-store" });
  if (!res.ok) {
    throw new Error(`Trip not found: ${res.status}`);
  }
  return res.json();
}

export async function getTravellerTrips(
  travellerId: string
): Promise<TripPlan[]> {
  const res = await fetch(`${BASE_URL}/traveller/${travellerId}/trips`, {
    cache: "no-store",
  });
  if (!res.ok) {
    throw new Error(`Failed to load trips: ${res.status}`);
  }
  return res.json();
}

// ------------------------------------------------------------------
// Flight API
// ------------------------------------------------------------------

export async function recommendFlights(
  data: RecommendFlightsRequest
): Promise<FlightRecommendationResponse> {
  const res = await fetch(`${BASE_URL}/flights/recommend`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    throw new Error(`Failed to get flight recommendations: ${res.status}`);
  }
  return res.json();
}

export async function getFlightOption(flightOptionId: string): Promise<FlightOption> {
  const res = await fetch(`${BASE_URL}/flights/${flightOptionId}`, {
    cache: "no-store",
  });
  if (!res.ok) {
    throw new Error(`Flight option not found: ${res.status}`);
  }
  return res.json();
}

export async function getTripFlights(tripId: string): Promise<FlightOption[]> {
  const res = await fetch(`${BASE_URL}/trips/${tripId}/flights`, {
    cache: "no-store",
  });
  if (!res.ok) {
    throw new Error(`Failed to load trip flights: ${res.status}`);
  }
  return res.json();
}

// ------------------------------------------------------------------
// Accommodation API
// ------------------------------------------------------------------

export async function recommendAccommodation(
  data: RecommendAccommodationRequest
): Promise<AccommodationRecommendationResponse> {
  const res = await fetch(`${BASE_URL}/accommodation/recommend`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    throw new Error(`Failed to get accommodation recommendations: ${res.status}`);
  }
  return res.json();
}

export async function getAccommodationOption(
  accommodationOptionId: string
): Promise<AccommodationOption> {
  const res = await fetch(`${BASE_URL}/accommodation/${accommodationOptionId}`, {
    cache: "no-store",
  });
  if (!res.ok) {
    throw new Error(`Accommodation option not found: ${res.status}`);
  }
  return res.json();
}

export async function getTripAccommodation(tripId: string): Promise<AccommodationOption[]> {
  const res = await fetch(`${BASE_URL}/trips/${tripId}/accommodation`, {
    cache: "no-store",
  });
  if (!res.ok) {
    throw new Error(`Failed to load trip accommodation: ${res.status}`);
  }
  return res.json();
}

// ------------------------------------------------------------------
// Destination API
// ------------------------------------------------------------------

export async function recommendDestinations(
  data: RecommendDestinationsRequest
): Promise<DestinationRecommendationResponse> {
  const res = await fetch(`${BASE_URL}/destinations/recommend`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    throw new Error(`Failed to get destination recommendations: ${res.status}`);
  }
  return res.json();
}

export async function getDestinationOption(
  destinationOptionId: string
): Promise<DestinationOption> {
  const res = await fetch(`${BASE_URL}/destinations/${destinationOptionId}`, {
    cache: "no-store",
  });
  if (!res.ok) {
    throw new Error(`Destination option not found: ${res.status}`);
  }
  return res.json();
}

export async function getTripDestinations(tripId: string): Promise<DestinationOption[]> {
  const res = await fetch(`${BASE_URL}/trips/${tripId}/destinations`, {
    cache: "no-store",
  });
  if (!res.ok) {
    throw new Error(`Failed to load trip destinations: ${res.status}`);
  }
  return res.json();
}

// ------------------------------------------------------------------
// Budget API
// ------------------------------------------------------------------

export async function recommendBudget(
  data: RecommendBudgetRequest
): Promise<BudgetRecommendationResponse> {
  const res = await fetch(`${BASE_URL}/budget/recommend`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    throw new Error(`Failed to get budget recommendations: ${res.status}`);
  }
  return res.json();
}

export async function getBudgetOption(budgetOptionId: string): Promise<BudgetOption> {
  const res = await fetch(`${BASE_URL}/budget/${budgetOptionId}`, {
    cache: "no-store",
  });
  if (!res.ok) {
    throw new Error(`Budget option not found: ${res.status}`);
  }
  return res.json();
}

export async function getTripBudget(tripId: string): Promise<BudgetOption[]> {
  const res = await fetch(`${BASE_URL}/trips/${tripId}/budget`, {
    cache: "no-store",
  });
  if (!res.ok) {
    throw new Error(`Failed to load trip budget: ${res.status}`);
  }
  return res.json();
}

// ------------------------------------------------------------------
// Visa API
// ------------------------------------------------------------------

export async function checkVisa(data: CheckVisaRequest): Promise<VisaAssessment> {
  const res = await fetch(`${BASE_URL}/visa/check`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    throw new Error(`Failed to check visa requirements: ${res.status}`);
  }
  return res.json();
}

export async function getVisaAssessment(visaAssessmentId: string): Promise<VisaAssessment> {
  const res = await fetch(`${BASE_URL}/visa/${visaAssessmentId}`, {
    cache: "no-store",
  });
  if (!res.ok) {
    throw new Error(`Visa assessment not found: ${res.status}`);
  }
  return res.json();
}

export async function getTripVisa(tripId: string): Promise<VisaAssessment[]> {
  const res = await fetch(`${BASE_URL}/trips/${tripId}/visa`, {
    cache: "no-store",
  });
  if (!res.ok) {
    throw new Error(`Failed to load trip visa assessments: ${res.status}`);
  }
  return res.json();
}

// ------------------------------------------------------------------
// Weather API
// ------------------------------------------------------------------

export async function analyseWeather(data: AnalyseWeatherRequest): Promise<WeatherAssessment> {
  const res = await fetch(`${BASE_URL}/weather/analyse`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    throw new Error(`Failed to analyse weather: ${res.status}`);
  }
  return res.json();
}

export async function getWeatherAssessment(weatherAssessmentId: string): Promise<WeatherAssessment> {
  const res = await fetch(`${BASE_URL}/weather/${weatherAssessmentId}`, {
    cache: "no-store",
  });
  if (!res.ok) {
    throw new Error(`Weather assessment not found: ${res.status}`);
  }
  return res.json();
}

export async function getTripWeather(tripId: string): Promise<WeatherAssessment[]> {
  const res = await fetch(`${BASE_URL}/trips/${tripId}/weather`, {
    cache: "no-store",
  });
  if (!res.ok) {
    throw new Error(`Failed to load trip weather assessments: ${res.status}`);
  }
  return res.json();
}

// ------------------------------------------------------------------
// Explainability API
// ------------------------------------------------------------------

export async function explainRecommendation(data: ExplainRequest): Promise<Explanation> {
  const res = await fetch(`${BASE_URL}/explain`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    throw new Error(`Failed to get explanation: ${res.status}`);
  }
  return res.json();
}

// ------------------------------------------------------------------
// Demo API
// ------------------------------------------------------------------

export async function runJapanDemo(): Promise<DemoResponse> {
  const res = await fetch(`${BASE_URL}/demo/japan-football-food`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
  });
  if (!res.ok) {
    throw new Error(`Demo failed: ${res.status}`);
  }
  return res.json();
}

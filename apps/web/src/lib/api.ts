import type { CreateProfileRequest, TravellerProfile } from "@/types/traveller";
export type DemoResponse = Record<string, any>;
import type { CreateGoalRequest, Goal } from "@/types/goal";
import type { CreateTripPlanRequest, TripPlan } from "@/types/trip";
import type { FlightOption, FlightRecommendationResponse, RecommendFlightsRequest } from "@/types/flight";

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

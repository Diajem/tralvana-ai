import type { CreateProfileRequest, TravellerProfile } from "@/types/traveller";

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

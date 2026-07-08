"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { createTripPlan } from "@/lib/api";
import type { CreateTripPlanRequest } from "@/types/trip";

const GOAL_TYPES = [
  "GENERAL_TRAVEL",
  "FOOTBALL_TRAVEL",
  "FOOD_TOUR",
  "RELAXATION",
  "ADVENTURE",
  "FAMILY_TRIP",
  "BUSINESS_TRAVEL",
  "PHOTOGRAPHY",
  "PILGRIMAGE",
  "DIASPORA_TRAVEL",
  "ROMANTIC_TRIP",
] as const;

const BUDGET_STYLES = [
  { value: "backpacker", label: "Backpacker" },
  { value: "budget", label: "Budget" },
  { value: "balanced", label: "Balanced" },
  { value: "comfort", label: "Comfort" },
  { value: "luxury", label: "Luxury" },
];

const CABIN_CLASSES = [
  { value: "economy", label: "Economy" },
  { value: "business", label: "Business" },
  { value: "first", label: "First" },
];

const INTERESTS = [
  "football", "food", "culture", "history", "art", "music",
  "nature", "adventure", "relaxation", "photography", "family", "romance",
  "shopping", "nightlife",
];

export default function NewTripPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [form, setForm] = useState<{
    traveller_id: string;
    goal_id: string;
    origin: string;
    destination: string;
    duration_days: number;
    budget_style: string;
    cabin_class: string;
    interests: string[];
    adults: number;
    children: number;
  }>({
    traveller_id: "",
    goal_id: "",
    origin: "London",
    destination: "",
    duration_days: 7,
    budget_style: "balanced",
    cabin_class: "economy",
    interests: [],
    adults: 1,
    children: 0,
  });

  const toggleInterest = (interest: string) => {
    setForm((f) => ({
      ...f,
      interests: f.interests.includes(interest)
        ? f.interests.filter((i) => i !== interest)
        : [...f.interests, interest],
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    const payload: CreateTripPlanRequest = {
      ...(form.traveller_id ? { traveller_id: form.traveller_id } : {}),
      ...(form.goal_id ? { goal_id: form.goal_id } : {}),
      origin: form.origin,
      destination: form.destination,
      duration_days: form.duration_days,
      budget_style: form.budget_style,
      cabin_class: form.cabin_class,
      interests: form.interests,
      travellers: { adults: form.adults, children: form.children, infants: 0 },
    };

    try {
      const trip = await createTripPlan(payload);
      router.push(`/trips/${trip.trip_id}`);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to create trip plan");
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen bg-gray-50 py-10 px-4">
      <div className="max-w-2xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Plan a Trip</h1>
        <p className="text-gray-500 mb-8">
          Generate a draft trip plan with itinerary, budget, and risk assessment.
        </p>

        {error && (
          <div className="mb-6 rounded-lg bg-red-50 border border-red-200 p-4 text-red-700">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6 bg-white rounded-2xl shadow p-8">
          {/* IDs */}
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Traveller ID <span className="text-gray-400">(optional)</span>
              </label>
              <input
                type="text"
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="e.g. traveller_001"
                value={form.traveller_id}
                onChange={(e) => setForm({ ...form, traveller_id: e.target.value })}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Goal ID <span className="text-gray-400">(optional)</span>
              </label>
              <input
                type="text"
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Link an existing goal"
                value={form.goal_id}
                onChange={(e) => setForm({ ...form, goal_id: e.target.value })}
              />
            </div>
          </div>

          {/* Route */}
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Origin <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Departing from..."
                value={form.origin}
                onChange={(e) => setForm({ ...form, origin: e.target.value })}
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Destination
              </label>
              <input
                type="text"
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="e.g. London, Tokyo, Lagos"
                value={form.destination}
                onChange={(e) => setForm({ ...form, destination: e.target.value })}
              />
            </div>
          </div>

          {/* Duration */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Duration (days)
            </label>
            <input
              type="number"
              min={1}
              max={90}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              value={form.duration_days}
              onChange={(e) =>
                setForm({ ...form, duration_days: parseInt(e.target.value) || 7 })
              }
            />
          </div>

          {/* Budget style */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Budget Style</label>
            <div className="flex flex-wrap gap-2">
              {BUDGET_STYLES.map((s) => (
                <button
                  key={s.value}
                  type="button"
                  onClick={() => setForm({ ...form, budget_style: s.value })}
                  className={`px-4 py-2 rounded-full text-sm font-medium border transition-colors ${
                    form.budget_style === s.value
                      ? "bg-blue-600 text-white border-blue-600"
                      : "bg-white text-gray-700 border-gray-300 hover:border-blue-400"
                  }`}
                >
                  {s.label}
                </button>
              ))}
            </div>
          </div>

          {/* Cabin class */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Cabin Class</label>
            <div className="flex gap-2">
              {CABIN_CLASSES.map((c) => (
                <button
                  key={c.value}
                  type="button"
                  onClick={() => setForm({ ...form, cabin_class: c.value })}
                  className={`px-4 py-2 rounded-full text-sm font-medium border transition-colors ${
                    form.cabin_class === c.value
                      ? "bg-indigo-600 text-white border-indigo-600"
                      : "bg-white text-gray-700 border-gray-300 hover:border-indigo-400"
                  }`}
                >
                  {c.label}
                </button>
              ))}
            </div>
          </div>

          {/* Travellers */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Adults</label>
              <input
                type="number"
                min={1}
                max={20}
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                value={form.adults}
                onChange={(e) =>
                  setForm({ ...form, adults: parseInt(e.target.value) || 1 })
                }
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Children</label>
              <input
                type="number"
                min={0}
                max={20}
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                value={form.children}
                onChange={(e) =>
                  setForm({ ...form, children: parseInt(e.target.value) || 0 })
                }
              />
            </div>
          </div>

          {/* Interests */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Interests</label>
            <div className="flex flex-wrap gap-2">
              {INTERESTS.map((interest) => (
                <button
                  key={interest}
                  type="button"
                  onClick={() => toggleInterest(interest)}
                  className={`px-3 py-1.5 rounded-full text-sm font-medium border transition-colors ${
                    form.interests.includes(interest)
                      ? "bg-emerald-600 text-white border-emerald-600"
                      : "bg-white text-gray-600 border-gray-300 hover:border-emerald-400"
                  }`}
                >
                  {interest}
                </button>
              ))}
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-3 rounded-xl bg-blue-600 text-white font-semibold text-sm hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {loading ? "Generating trip plan..." : "Generate Trip Plan"}
          </button>
        </form>
      </div>
    </main>
  );
}

"use client";

import { useState } from "react";
import Link from "next/link";
import { recommendDestinations } from "@/lib/api";
import type {
  DestinationOption,
  DestinationRecommendationResponse,
  RecommendDestinationsRequest,
} from "@/types/destination";

const KNOWN_CITIES = [
  "Tokyo", "Osaka", "Barcelona", "Paris", "London",
  "New York", "Lagos", "Accra", "Kingston", "Dubai",
];

const INTERESTS = [
  "football", "food", "culture", "history", "art", "music",
  "nature", "adventure", "relaxation", "photography", "family", "romance",
  "shopping", "nightlife",
];

const BUDGET_STYLES = [
  { value: "backpacker", label: "Backpacker" },
  { value: "budget", label: "Budget" },
  { value: "balanced", label: "Balanced" },
  { value: "comfort", label: "Comfort" },
  { value: "luxury", label: "Luxury" },
];

const RECOMMENDATION_LABELS: Record<string, { label: string; className: string }> = {
  BEST_OVERALL: { label: "Best Overall", className: "bg-blue-600 text-white" },
  BEST_FOR_FOOD: { label: "Best for Food", className: "bg-emerald-600 text-white" },
  BEST_FOR_FOOTBALL: { label: "Best for Football", className: "bg-green-700 text-white" },
  BEST_FOR_CULTURE: { label: "Best for Culture", className: "bg-indigo-600 text-white" },
  BEST_FOR_FAMILY: { label: "Best for Family", className: "bg-amber-500 text-white" },
  BEST_FOR_BUDGET: { label: "Best for Budget", className: "bg-teal-600 text-white" },
  BEST_FOR_PHOTOGRAPHY: { label: "Best for Photography", className: "bg-purple-600 text-white" },
  BEST_HIDDEN_GEM: { label: "Hidden Gem", className: "bg-fuchsia-600 text-white" },
  AVOID: { label: "Avoid", className: "bg-red-600 text-white" },
};

function MatchScoreBar({ score }: { score: number }) {
  const pct = Math.round(score * 100);
  const colour = pct >= 70 ? "bg-green-500" : pct >= 45 ? "bg-amber-400" : "bg-red-400";
  return (
    <div>
      <div className="flex justify-between text-xs text-gray-500 mb-1">
        <span>Match Score</span>
        <span>{pct}%</span>
      </div>
      <div className="h-2 w-full rounded-full bg-gray-200 overflow-hidden">
        <div className={`h-full ${colour} rounded-full`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}

function DestinationCard({ destination }: { destination: DestinationOption }) {
  const badge = RECOMMENDATION_LABELS[destination.recommendation_type] ?? {
    label: destination.recommendation_type,
    className: "bg-gray-500 text-white",
  };

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-6 space-y-4">
      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div>
          <p className="font-semibold text-gray-900">{destination.name}</p>
          <p className="text-xs text-gray-500 mt-0.5">
            {destination.destination_type.replace(/_/g, " ")} ·{" "}
            {destination.destination_type === "CITY"
              ? destination.country
              : `${destination.city}, ${destination.country}`}
          </p>
        </div>
        <span className={`px-2.5 py-1 rounded-full text-xs font-medium ${badge.className}`}>
          {badge.label}
        </span>
      </div>

      <p className="text-sm text-gray-600">{destination.description}</p>

      {destination.interests_matched.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {destination.interests_matched.map((interest) => (
            <span
              key={interest}
              className="px-2 py-0.5 rounded-full bg-blue-50 text-blue-700 text-xs font-medium"
            >
              {interest}
            </span>
          ))}
        </div>
      )}

      <MatchScoreBar score={destination.match_score} />

      <p className="text-sm text-gray-700">{destination.reasoning}</p>

      {destination.risks.length > 0 && (
        <div className="rounded-lg bg-amber-50 border border-amber-200 p-3">
          <p className="text-xs font-semibold text-amber-800 mb-1">Risks</p>
          <ul className="space-y-0.5">
            {destination.risks.map((r, i) => (
              <li key={i} className="text-xs text-amber-700">• {r}</li>
            ))}
          </ul>
        </div>
      )}

      {destination.assumptions.length > 0 && (
        <ul className="space-y-0.5">
          {destination.assumptions.map((a, i) => (
            <li key={i} className="text-xs text-gray-400">• {a}</li>
          ))}
        </ul>
      )}

      <Link
        href={`/destinations/${destination.destination_option_id}`}
        className="inline-block text-xs font-medium text-blue-600 hover:text-blue-700"
      >
        View full details →
      </Link>
    </div>
  );
}

export default function RecommendDestinationsPage() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<DestinationRecommendationResponse | null>(null);

  const [form, setForm] = useState<{
    traveller_id: string;
    trip_id: string;
    city: string;
    interests: string[];
    budget_style: string;
    travel_month: string;
    children: number;
  }>({
    traveller_id: "",
    trip_id: "",
    city: "",
    interests: [],
    budget_style: "balanced",
    travel_month: "",
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

    const payload: RecommendDestinationsRequest = {
      ...(form.traveller_id ? { traveller_id: form.traveller_id } : {}),
      ...(form.trip_id ? { trip_id: form.trip_id } : {}),
      ...(form.city ? { city: form.city } : {}),
      interests: form.interests,
      budget_style: form.budget_style,
      ...(form.travel_month ? { travel_month: parseInt(form.travel_month) } : {}),
      children: form.children,
    };

    try {
      const recommendation = await recommendDestinations(payload);
      setResult(recommendation);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to get destination recommendations");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen bg-gray-50 py-10 px-4">
      <div className="max-w-3xl mx-auto space-y-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Destination Recommendations</h1>
          <p className="text-gray-500">
            Leave the city blank to compare cities, or pick one to explore neighbourhoods,
            food areas, and attractions within it.
          </p>
        </div>

        {error && (
          <div className="rounded-lg bg-red-50 border border-red-200 p-4 text-red-700">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6 bg-white rounded-2xl shadow p-8">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Traveller ID <span className="text-gray-400">(optional)</span>
              </label>
              <input
                type="text"
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                value={form.traveller_id}
                onChange={(e) => setForm({ ...form, traveller_id: e.target.value })}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Trip ID <span className="text-gray-400">(optional)</span>
              </label>
              <input
                type="text"
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Link an existing trip"
                value={form.trip_id}
                onChange={(e) => setForm({ ...form, trip_id: e.target.value })}
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              City <span className="text-gray-400">(optional — leave blank to compare cities)</span>
            </label>
            <div className="flex flex-wrap gap-2">
              <button
                type="button"
                onClick={() => setForm({ ...form, city: "" })}
                className={`px-3 py-1.5 rounded-full text-sm font-medium border transition-colors ${
                  form.city === ""
                    ? "bg-indigo-600 text-white border-indigo-600"
                    : "bg-white text-gray-700 border-gray-300 hover:border-indigo-400"
                }`}
              >
                Any / Compare Cities
              </button>
              {KNOWN_CITIES.map((city) => (
                <button
                  key={city}
                  type="button"
                  onClick={() => setForm({ ...form, city })}
                  className={`px-3 py-1.5 rounded-full text-sm font-medium border transition-colors ${
                    form.city === city
                      ? "bg-indigo-600 text-white border-indigo-600"
                      : "bg-white text-gray-700 border-gray-300 hover:border-indigo-400"
                  }`}
                >
                  {city}
                </button>
              ))}
            </div>
          </div>

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

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Travel Month <span className="text-gray-400">(optional)</span>
              </label>
              <select
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                value={form.travel_month}
                onChange={(e) => setForm({ ...form, travel_month: e.target.value })}
              >
                <option value="">Not sure yet</option>
                {[
                  "January", "February", "March", "April", "May", "June",
                  "July", "August", "September", "October", "November", "December",
                ].map((label, i) => (
                  <option key={label} value={i + 1}>{label}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Children</label>
              <input
                type="number"
                min={0}
                max={20}
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                value={form.children}
                onChange={(e) => setForm({ ...form, children: parseInt(e.target.value) || 0 })}
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-3 rounded-xl bg-blue-600 text-white font-semibold text-sm hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {loading ? "Ranking destination options..." : "Get Destination Recommendations"}
          </button>
        </form>

        {result && (
          <div className="space-y-6">
            <div className="bg-white rounded-xl border border-gray-200 p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-2">Summary</h2>
              <p className="text-sm text-gray-700">{result.summary}</p>
            </div>

            <div className="space-y-4">
              {result.destination_options.map((destination) => (
                <DestinationCard
                  key={destination.destination_option_id}
                  destination={destination}
                />
              ))}
            </div>

            <div className="bg-white rounded-xl border border-gray-200 p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-3">Assumptions</h2>
              <ul className="space-y-1">
                {result.assumptions.map((a, i) => (
                  <li key={i} className="text-sm text-gray-600">• {a}</li>
                ))}
              </ul>
            </div>

            {result.next_actions.length > 0 && (
              <div className="bg-white rounded-xl border border-gray-200 p-6">
                <h2 className="text-lg font-semibold text-gray-900 mb-3">Recommended Next Steps</h2>
                <ol className="space-y-1">
                  {result.next_actions.map((a, i) => (
                    <li key={i} className="text-sm text-gray-700">
                      <span className="font-medium text-blue-600 mr-1">{i + 1}.</span>
                      {a}
                    </li>
                  ))}
                </ol>
              </div>
            )}
          </div>
        )}
      </div>
    </main>
  );
}

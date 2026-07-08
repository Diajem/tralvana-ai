"use client";

import { useState } from "react";
import Link from "next/link";
import { recommendFlights } from "@/lib/api";
import type { FlightOption, FlightRecommendationResponse, RecommendFlightsRequest } from "@/types/flight";

const CABIN_CLASSES = [
  { value: "economy", label: "Economy" },
  { value: "business", label: "Business" },
  { value: "first", label: "First" },
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
  LOWEST_PRICE: { label: "Lowest Price", className: "bg-emerald-600 text-white" },
  SHORTEST_DURATION: { label: "Shortest Duration", className: "bg-indigo-600 text-white" },
  BEST_FOR_FAMILY: { label: "Best for Family", className: "bg-amber-500 text-white" },
  BEST_FOR_BUSINESS: { label: "Best for Business", className: "bg-slate-700 text-white" },
  BEST_FOR_COMFORT: { label: "Best for Comfort", className: "bg-purple-600 text-white" },
  BEST_FOR_BUDGET: { label: "Best for Budget", className: "bg-teal-600 text-white" },
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

function FlightCard({ flight }: { flight: FlightOption }) {
  const badge = RECOMMENDATION_LABELS[flight.recommendation_type] ?? {
    label: flight.recommendation_type,
    className: "bg-gray-500 text-white",
  };

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-6 space-y-4">
      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div>
          <p className="font-semibold text-gray-900">
            {flight.airline} {flight.flight_number}
          </p>
          <p className="text-xs text-gray-500 mt-0.5">
            {flight.origin} → {flight.destination} · {flight.cabin_class} ·{" "}
            {flight.stops === 0 ? "Direct" : `${flight.stops} stop${flight.stops > 1 ? "s" : ""}`}
          </p>
        </div>
        <span className={`px-2.5 py-1 rounded-full text-xs font-medium ${badge.className}`}>
          {badge.label}
        </span>
      </div>

      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4 text-sm">
        <div>
          <p className="text-gray-400 text-xs mb-0.5">Departs</p>
          <p className="font-medium text-gray-900">{flight.departure_time}</p>
        </div>
        <div>
          <p className="text-gray-400 text-xs mb-0.5">Arrives</p>
          <p className="font-medium text-gray-900">{flight.arrival_time}</p>
        </div>
        <div>
          <p className="text-gray-400 text-xs mb-0.5">Duration</p>
          <p className="font-medium text-gray-900">{flight.total_duration}</p>
        </div>
        <div>
          <p className="text-gray-400 text-xs mb-0.5">Price</p>
          <p className="font-medium text-gray-900">
            {flight.currency} {flight.estimated_price.toLocaleString()}
          </p>
        </div>
      </div>

      <MatchScoreBar score={flight.match_score} />

      <p className="text-sm text-gray-700">{flight.reasoning}</p>

      {flight.risks.length > 0 && (
        <div className="rounded-lg bg-amber-50 border border-amber-200 p-3">
          <p className="text-xs font-semibold text-amber-800 mb-1">Risks</p>
          <ul className="space-y-0.5">
            {flight.risks.map((r, i) => (
              <li key={i} className="text-xs text-amber-700">• {r}</li>
            ))}
          </ul>
        </div>
      )}

      {flight.assumptions.length > 0 && (
        <ul className="space-y-0.5">
          {flight.assumptions.map((a, i) => (
            <li key={i} className="text-xs text-gray-400">• {a}</li>
          ))}
        </ul>
      )}

      <Link
        href={`/flights/${flight.flight_option_id}`}
        className="inline-block text-xs font-medium text-blue-600 hover:text-blue-700"
      >
        View full details →
      </Link>
    </div>
  );
}

export default function RecommendFlightsPage() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<FlightRecommendationResponse | null>(null);

  const [form, setForm] = useState<{
    traveller_id: string;
    trip_id: string;
    origin: string;
    destination: string;
    departure_date: string;
    return_date: string;
    cabin_class: string;
    budget_style: string;
    airline_preference: string;
    adults: number;
    trip_duration_days: number;
  }>({
    traveller_id: "",
    trip_id: "",
    origin: "London",
    destination: "",
    departure_date: "",
    return_date: "",
    cabin_class: "economy",
    budget_style: "balanced",
    airline_preference: "",
    adults: 1,
    trip_duration_days: 7,
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    const payload: RecommendFlightsRequest = {
      ...(form.traveller_id ? { traveller_id: form.traveller_id } : {}),
      ...(form.trip_id ? { trip_id: form.trip_id } : {}),
      origin: form.origin,
      destination: form.destination,
      ...(form.departure_date ? { departure_date: form.departure_date } : {}),
      ...(form.return_date ? { return_date: form.return_date } : {}),
      cabin_class: form.cabin_class,
      budget_style: form.budget_style,
      ...(form.airline_preference ? { airline_preference: form.airline_preference } : {}),
      adults: form.adults,
      trip_duration_days: form.trip_duration_days,
    };

    try {
      const recommendation = await recommendFlights(payload);
      setResult(recommendation);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to get flight recommendations");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen bg-gray-50 py-10 px-4">
      <div className="max-w-3xl mx-auto space-y-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Flight Recommendations</h1>
          <p className="text-gray-500">
            Ranked flight options scored against your budget, cabin preference, and travel style.
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

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Origin <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                value={form.origin}
                onChange={(e) => setForm({ ...form, origin: e.target.value })}
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Destination <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="e.g. Tokyo"
                value={form.destination}
                onChange={(e) => setForm({ ...form, destination: e.target.value })}
                required
              />
            </div>
          </div>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Departure Date <span className="text-gray-400">(optional)</span>
              </label>
              <input
                type="date"
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                value={form.departure_date}
                onChange={(e) => setForm({ ...form, departure_date: e.target.value })}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Return Date <span className="text-gray-400">(optional)</span>
              </label>
              <input
                type="date"
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                value={form.return_date}
                onChange={(e) => setForm({ ...form, return_date: e.target.value })}
              />
            </div>
          </div>

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

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Preferred Airline <span className="text-gray-400">(optional)</span>
              </label>
              <input
                type="text"
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                value={form.airline_preference}
                onChange={(e) => setForm({ ...form, airline_preference: e.target.value })}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Adults</label>
              <input
                type="number"
                min={1}
                max={20}
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                value={form.adults}
                onChange={(e) => setForm({ ...form, adults: parseInt(e.target.value) || 1 })}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Trip Duration (days)</label>
              <input
                type="number"
                min={1}
                max={90}
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                value={form.trip_duration_days}
                onChange={(e) => setForm({ ...form, trip_duration_days: parseInt(e.target.value) || 7 })}
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-3 rounded-xl bg-blue-600 text-white font-semibold text-sm hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {loading ? "Ranking flight options..." : "Get Flight Recommendations"}
          </button>
        </form>

        {result && (
          <div className="space-y-6">
            <div className="bg-white rounded-xl border border-gray-200 p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-2">Summary</h2>
              <p className="text-sm text-gray-700">{result.summary}</p>
            </div>

            <div className="space-y-4">
              {result.flight_options.map((flight) => (
                <FlightCard key={flight.flight_option_id} flight={flight} />
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

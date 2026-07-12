"use client";

import { useState } from "react";
import Link from "next/link";
import { recommendAccommodation } from "@/lib/api";
import type {
  AccommodationOption,
  AccommodationRecommendationResponse,
  RecommendAccommodationRequest,
} from "@/types/accommodation";

const ACCOMMODATION_TYPES = [
  { value: "", label: "Any" },
  { value: "HOTEL", label: "Hotel" },
  { value: "APARTMENT", label: "Apartment" },
  { value: "HOSTEL", label: "Hostel" },
  { value: "VILLA", label: "Villa" },
  { value: "RESORT", label: "Resort" },
  { value: "SERVICED_APARTMENT", label: "Serviced Apartment" },
  { value: "BOUTIQUE_HOTEL", label: "Boutique Hotel" },
  { value: "GUESTHOUSE", label: "Guesthouse" },
];

const BUDGET_STYLES = [
  { value: "backpacker", label: "Backpacker" },
  { value: "budget", label: "Budget" },
  { value: "balanced", label: "Balanced" },
  { value: "comfort", label: "Comfort" },
  { value: "luxury", label: "Luxury" },
];

const DATA_SOURCE_LABELS: Record<string, { label: string; className: string; banner: string | null }> = {
  MOCK: { label: "Test data", className: "bg-gray-100 text-gray-600", banner: null },
  DUFFEL_STAYS_SANDBOX: {
    label: "Duffel Stays sandbox",
    className: "bg-sky-100 text-sky-700",
    banner: "Duffel Stays sandbox data — not available for purchase.",
  },
  MOCK_FALLBACK: {
    label: "Mock fallback",
    className: "bg-amber-100 text-amber-700",
    banner: "Duffel Stays sandbox was unavailable — showing mock fallback data, not real inventory.",
  },
};

const RECOMMENDATION_LABELS: Record<string, { label: string; className: string }> = {
  BEST_OVERALL: { label: "Best Overall", className: "bg-blue-600 text-white" },
  BEST_VALUE: { label: "Best Value", className: "bg-emerald-600 text-white" },
  BEST_LOCATION: { label: "Best Location", className: "bg-indigo-600 text-white" },
  BEST_COMFORT: { label: "Best Comfort", className: "bg-purple-600 text-white" },
  BEST_FOR_FAMILY: { label: "Best for Family", className: "bg-amber-500 text-white" },
  BEST_FOR_BUSINESS: { label: "Best for Business", className: "bg-slate-700 text-white" },
  BEST_BUDGET: { label: "Best Budget", className: "bg-teal-600 text-white" },
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

function AccommodationCard({ accommodation }: { accommodation: AccommodationOption }) {
  const badge = RECOMMENDATION_LABELS[accommodation.recommendation_type] ?? {
    label: accommodation.recommendation_type,
    className: "bg-gray-500 text-white",
  };

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-6 space-y-4">
      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div>
          <p className="font-semibold text-gray-900">{accommodation.property_name}</p>
          <p className="text-xs text-gray-500 mt-0.5">
            {accommodation.accommodation_type.replace(/_/g, " ")} · {accommodation.star_rating}-star ·{" "}
            {accommodation.neighbourhood}
          </p>
        </div>
        <span className={`px-2.5 py-1 rounded-full text-xs font-medium ${badge.className}`}>
          {badge.label}
        </span>
      </div>

      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4 text-sm">
        <div>
          <p className="text-gray-400 text-xs mb-0.5">To Centre</p>
          <p className="font-medium text-gray-900">{accommodation.distance_to_centre} km</p>
        </div>
        <div>
          <p className="text-gray-400 text-xs mb-0.5">To Transport</p>
          <p className="font-medium text-gray-900">{accommodation.distance_to_transport} km</p>
        </div>
        <div>
          <p className="text-gray-400 text-xs mb-0.5">Reviews</p>
          <p className="font-medium text-gray-900">{accommodation.review_score}/10</p>
        </div>
        <div>
          <p className="text-gray-400 text-xs mb-0.5">Nightly Price</p>
          <p className="font-medium text-gray-900">
            {accommodation.currency} {accommodation.nightly_price.toLocaleString()}
          </p>
        </div>
      </div>

      <p className="text-xs text-gray-500">
        {accommodation.breakfast_included ? "✓ Breakfast included" : "✗ Breakfast not included"}
        {" · "}
        {accommodation.cancellation_policy.replace(/_/g, " ")}
        {" · Stay total "}
        {accommodation.currency} {accommodation.total_price.toLocaleString()}
      </p>

      <MatchScoreBar score={accommodation.match_score} />

      <p className="text-sm text-gray-700">{accommodation.reasoning}</p>

      {accommodation.risks.length > 0 && (
        <div className="rounded-lg bg-amber-50 border border-amber-200 p-3">
          <p className="text-xs font-semibold text-amber-800 mb-1">Risks</p>
          <ul className="space-y-0.5">
            {accommodation.risks.map((r, i) => (
              <li key={i} className="text-xs text-amber-700">• {r}</li>
            ))}
          </ul>
        </div>
      )}

      {accommodation.assumptions.length > 0 && (
        <ul className="space-y-0.5">
          {accommodation.assumptions.map((a, i) => (
            <li key={i} className="text-xs text-gray-400">• {a}</li>
          ))}
        </ul>
      )}

      <Link
        href={`/accommodation/${accommodation.accommodation_option_id}`}
        className="inline-block text-xs font-medium text-blue-600 hover:text-blue-700"
      >
        View full details →
      </Link>
    </div>
  );
}

export default function RecommendAccommodationPage() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<AccommodationRecommendationResponse | null>(null);

  const [form, setForm] = useState<{
    traveller_id: string;
    trip_id: string;
    destination: string;
    check_in_date: string;
    nights: number;
    accommodation_type: string;
    budget_style: string;
    adults: number;
    children: number;
    rooms: number;
    business_trip: boolean;
    accessibility_required: boolean;
  }>({
    traveller_id: "",
    trip_id: "",
    destination: "",
    check_in_date: "",
    nights: 7,
    accommodation_type: "",
    budget_style: "balanced",
    adults: 1,
    children: 0,
    rooms: 1,
    business_trip: false,
    accessibility_required: false,
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    const payload: RecommendAccommodationRequest = {
      ...(form.traveller_id ? { traveller_id: form.traveller_id } : {}),
      ...(form.trip_id ? { trip_id: form.trip_id } : {}),
      destination: form.destination,
      ...(form.check_in_date ? { check_in_date: form.check_in_date } : {}),
      nights: form.nights,
      ...(form.accommodation_type ? { accommodation_type: form.accommodation_type } : {}),
      budget_style: form.budget_style,
      adults: form.adults,
      children: form.children,
      rooms: form.rooms,
      business_trip: form.business_trip,
      accessibility_required: form.accessibility_required,
    };

    try {
      const recommendation = await recommendAccommodation(payload);
      setResult(recommendation);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to get accommodation recommendations");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen bg-gray-50 py-10 px-4">
      <div className="max-w-3xl mx-auto space-y-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Accommodation Recommendations</h1>
          <p className="text-gray-500">
            Ranked accommodation options scored against your budget, location needs, and travel style.
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

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Check-in Date <span className="text-gray-400">(optional)</span>
              </label>
              <input
                type="date"
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                value={form.check_in_date}
                onChange={(e) => setForm({ ...form, check_in_date: e.target.value })}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Nights</label>
              <input
                type="number"
                min={1}
                max={90}
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                value={form.nights}
                onChange={(e) => setForm({ ...form, nights: parseInt(e.target.value) || 7 })}
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Accommodation Type</label>
            <div className="flex flex-wrap gap-2">
              {ACCOMMODATION_TYPES.map((t) => (
                <button
                  key={t.value}
                  type="button"
                  onClick={() => setForm({ ...form, accommodation_type: t.value })}
                  className={`px-3 py-1.5 rounded-full text-sm font-medium border transition-colors ${
                    form.accommodation_type === t.value
                      ? "bg-indigo-600 text-white border-indigo-600"
                      : "bg-white text-gray-700 border-gray-300 hover:border-indigo-400"
                  }`}
                >
                  {t.label}
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

          <div className="grid grid-cols-3 gap-4">
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
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Rooms</label>
              <input
                type="number"
                min={1}
                max={8}
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                value={form.rooms}
                onChange={(e) => setForm({ ...form, rooms: parseInt(e.target.value) || 1 })}
              />
            </div>
          </div>

          <div className="flex flex-wrap gap-4">
            <label className="flex items-center gap-2 text-sm text-gray-700">
              <input
                type="checkbox"
                checked={form.business_trip}
                onChange={(e) => setForm({ ...form, business_trip: e.target.checked })}
              />
              Business trip
            </label>
            <label className="flex items-center gap-2 text-sm text-gray-700">
              <input
                type="checkbox"
                checked={form.accessibility_required}
                onChange={(e) => setForm({ ...form, accessibility_required: e.target.checked })}
              />
              Accessibility required
            </label>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-3 rounded-xl bg-blue-600 text-white font-semibold text-sm hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {loading ? "Ranking accommodation options..." : "Get Accommodation Recommendations"}
          </button>
        </form>

        {result && (
          <div className="space-y-6">
            {(() => {
              const source = DATA_SOURCE_LABELS[result.data_source] ?? DATA_SOURCE_LABELS.MOCK;
              return source.banner ? (
                <div className="rounded-lg bg-sky-50 border border-sky-200 p-4 text-sky-800 text-sm font-medium">
                  {source.banner}
                </div>
              ) : null;
            })()}

            <div className="bg-white rounded-xl border border-gray-200 p-6">
              <div className="flex items-start justify-between gap-4 flex-wrap mb-2">
                <h2 className="text-lg font-semibold text-gray-900">Summary</h2>
                <span
                  className={`px-2.5 py-1 rounded-full text-xs font-medium ${
                    (DATA_SOURCE_LABELS[result.data_source] ?? DATA_SOURCE_LABELS.MOCK).className
                  }`}
                >
                  Source: {(DATA_SOURCE_LABELS[result.data_source] ?? DATA_SOURCE_LABELS.MOCK).label}
                </span>
              </div>
              <p className="text-sm text-gray-700">{result.summary}</p>
            </div>

            <div className="space-y-4">
              {result.accommodation_options.map((accommodation) => (
                <AccommodationCard
                  key={accommodation.accommodation_option_id}
                  accommodation={accommodation}
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

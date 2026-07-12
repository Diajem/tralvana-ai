"use client";

import { useState } from "react";
import { planTrip } from "@/lib/api";
import type { DailyOutlineEntry, PlanTripResponse, TripItinerary } from "@/types/planner";

function ConfidenceBadge({ confidence }: { confidence: number }) {
  const pct = Math.round(confidence * 100);
  const colour = pct >= 70 ? "bg-green-100 text-green-800" : pct >= 45 ? "bg-amber-100 text-amber-800" : "bg-red-100 text-red-800";
  return (
    <span className={`px-3 py-1 rounded-full text-sm font-semibold ${colour}`}>
      {pct}% confidence
    </span>
  );
}

function SectionCard({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-6">
      <h2 className="text-lg font-semibold text-gray-900 mb-3">{title}</h2>
      {children}
    </div>
  );
}

function fmtKey(key: string): string {
  return key.replace(/_/g, " ");
}

function RecommendationFacts({ data }: { data: Record<string, unknown> }) {
  // Show a curated, readable subset rather than dumping every raw
  // field — but never invent a value that isn't already in `data`.
  const preferredOrder = [
    "airline", "flight_number", "property_name", "name", "city", "budget_style",
    "estimated_price", "nightly_price", "total_price", "currency",
    "star_rating", "review_score", "match_score", "recommendation_type",
    "cabin_class", "accommodation_type", "stops", "total_duration",
    "cancellation_policy", "breakfast_included", "visa_status", "visa_required",
    "visa_type", "processing_time", "season", "weather_summary", "recommendation",
  ];
  const entries = preferredOrder
    .filter((k) => k in data && data[k] !== null && data[k] !== undefined && data[k] !== "")
    .map((k) => [k, data[k]] as const);

  if (entries.length === 0) return null;

  return (
    <dl className="grid grid-cols-2 gap-x-4 gap-y-2 text-sm sm:grid-cols-3">
      {entries.map(([key, value]) => (
        <div key={key}>
          <dt className="text-gray-400 text-xs capitalize">{fmtKey(key)}</dt>
          <dd className="font-medium text-gray-900">{String(value)}</dd>
        </div>
      ))}
    </dl>
  );
}

function DailyOutlineCard({ entry }: { entry: DailyOutlineEntry }) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5">
      <p className="font-semibold text-gray-900">{entry.title}</p>
      <div className="mt-3 space-y-2 text-sm text-gray-700">
        <p><span className="text-gray-400">Morning:</span> {entry.morning}</p>
        <p><span className="text-gray-400">Afternoon:</span> {entry.afternoon}</p>
        <p><span className="text-gray-400">Evening:</span> {entry.evening}</p>
      </div>
      <div className="mt-3 pt-3 border-t border-gray-100 flex items-center justify-between text-xs text-gray-500">
        <span>{entry.accommodation}</span>
        <span>~${entry.estimated_daily_cost_usd}/day</span>
      </div>
      {entry.notes && <p className="mt-2 text-xs text-amber-700">{entry.notes}</p>}
    </div>
  );
}

function ItineraryView({ itinerary }: { itinerary: TripItinerary }) {
  return (
    <div className="space-y-6">
      <div className="bg-indigo-600 rounded-2xl p-8 text-white">
        <div className="flex items-start justify-between gap-4 flex-wrap mb-3">
          <h2 className="text-xl font-bold">Your Trip, Assembled</h2>
          <ConfidenceBadge confidence={itinerary.confidence} />
        </div>
        <p className="text-indigo-50 leading-relaxed">{itinerary.executive_summary}</p>
      </div>

      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
        {itinerary.destination_recommendation && (
          <SectionCard title="Destination">
            <RecommendationFacts data={itinerary.destination_recommendation} />
          </SectionCard>
        )}
        {itinerary.flight_recommendation && (
          <SectionCard title="Flight">
            <RecommendationFacts data={itinerary.flight_recommendation} />
          </SectionCard>
        )}
        {itinerary.accommodation_recommendation && (
          <SectionCard title="Accommodation">
            <RecommendationFacts data={itinerary.accommodation_recommendation} />
          </SectionCard>
        )}
        {itinerary.budget_summary && (
          <SectionCard title="Budget">
            <RecommendationFacts data={itinerary.budget_summary} />
          </SectionCard>
        )}
        {itinerary.visa_summary && (
          <SectionCard title="Visa">
            <RecommendationFacts data={itinerary.visa_summary} />
          </SectionCard>
        )}
        {itinerary.weather_expectations && (
          <SectionCard title="Weather">
            <RecommendationFacts data={itinerary.weather_expectations} />
          </SectionCard>
        )}
      </div>

      {itinerary.daily_outline.length > 0 && (
        <div>
          <h2 className="text-lg font-semibold text-gray-900 mb-3">Daily Outline</h2>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            {itinerary.daily_outline.map((entry) => (
              <DailyOutlineCard key={entry.day} entry={entry} />
            ))}
          </div>
        </div>
      )}

      {itinerary.why_this_itinerary.length > 0 && (
        <SectionCard title="Why This Itinerary">
          <ul className="space-y-2">
            {itinerary.why_this_itinerary.map((d, i) => (
              <li key={i} className="text-sm text-gray-700">
                <span className="font-medium text-gray-900 capitalize">{fmtKey(d.module)}: </span>
                {d.driver}
              </li>
            ))}
          </ul>
        </SectionCard>
      )}

      {itinerary.confidence_explanation && (
        <SectionCard title="Confidence">
          <p className="text-sm text-gray-700">{itinerary.confidence_explanation}</p>
        </SectionCard>
      )}

      {itinerary.alternative_options.length > 0 && (
        <SectionCard title="Alternative Options">
          <ul className="space-y-2">
            {itinerary.alternative_options.map((a, i) => (
              <li key={i} className="text-sm text-gray-700">
                <span className="font-medium text-gray-900">{a.alternative}</span> ({fmtKey(a.module)}) —{" "}
                <span className="text-gray-500">{a.why_not_chosen}</span>
              </li>
            ))}
          </ul>
        </SectionCard>
      )}

      {itinerary.risks.length > 0 && (
        <div className="rounded-lg bg-amber-50 border border-amber-200 p-5">
          <p className="text-sm font-semibold text-amber-800 mb-2">Risks</p>
          <ul className="space-y-1">
            {itinerary.risks.map((r, i) => (
              <li key={i} className="text-sm text-amber-700">• {r}</li>
            ))}
          </ul>
        </div>
      )}

      {itinerary.assumptions.length > 0 && (
        <SectionCard title="Assumptions">
          <ul className="space-y-1">
            {itinerary.assumptions.map((a, i) => (
              <li key={i} className="text-sm text-gray-600">• {a}</li>
            ))}
          </ul>
        </SectionCard>
      )}

      {itinerary.modules_unavailable.length > 0 && (
        <p className="text-xs text-gray-400">
          Not included this time: {itinerary.modules_unavailable.map(fmtKey).join(", ")}.
        </p>
      )}
    </div>
  );
}

export default function PlannerPage() {
  const [message, setMessage] = useState("");
  const [travellerId, setTravellerId] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<PlanTripResponse | null>(null);
  const [conversationId, setConversationId] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!message.trim()) return;
    setLoading(true);
    setError(null);

    try {
      const response = await planTrip({
        message,
        ...(travellerId ? { traveller_id: travellerId } : {}),
        ...(conversationId ? { conversation_id: conversationId } : {}),
      });
      setResult(response);
      setConversationId(response.conversation_id);
      setMessage("");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to plan your trip");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen bg-gray-50 py-10 px-4">
      <div className="max-w-4xl mx-auto space-y-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">AI Travel Planner</h1>
          <p className="text-gray-500">
            Describe your trip in your own words — Tralvana will pull together destinations,
            flights, accommodation, budget, visa requirements, and weather into one plan.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="bg-white rounded-2xl shadow p-6 space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              {conversationId ? "Add more detail" : "Tell us about your trip"}
            </label>
            <textarea
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 min-h-[100px]"
              placeholder="e.g. I want to plan a football trip to London in September for 2 adults, balanced budget, travelling from Lagos"
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              required
            />
          </div>
          {!conversationId && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Traveller ID <span className="text-gray-400">(optional)</span>
              </label>
              <input
                type="text"
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                value={travellerId}
                onChange={(e) => setTravellerId(e.target.value)}
              />
            </div>
          )}
          <button
            type="submit"
            disabled={loading}
            className="w-full py-3 rounded-xl bg-indigo-600 text-white font-semibold text-sm hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {loading ? "Putting your trip together..." : conversationId ? "Continue Planning" : "Plan My Trip"}
          </button>
        </form>

        {error && (
          <div className="rounded-lg bg-red-50 border border-red-200 p-4 text-red-700 text-sm">
            {error}
          </div>
        )}

        {result && !result.itinerary && (
          <div className="bg-white rounded-xl border border-gray-200 p-6 space-y-3">
            <p className="text-sm text-gray-700">{result.response}</p>
            {result.missing_information.length > 0 && (
              <ul className="space-y-1">
                {result.missing_information.map((m, i) => (
                  <li key={i} className="text-xs text-gray-500">• {m}</li>
                ))}
              </ul>
            )}
          </div>
        )}

        {result?.itinerary && <ItineraryView itinerary={result.itinerary} />}
      </div>
    </main>
  );
}

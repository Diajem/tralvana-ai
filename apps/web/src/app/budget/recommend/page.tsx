"use client";

import { useState } from "react";
import Link from "next/link";
import { recommendBudget } from "@/lib/api";
import type {
  BudgetOption,
  BudgetRecommendationResponse,
  RecommendBudgetRequest,
} from "@/types/budget";

const BUDGET_STYLES = [
  { value: "backpacker", label: "Backpacker" },
  { value: "budget", label: "Budget" },
  { value: "balanced", label: "Balanced" },
  { value: "comfort", label: "Comfort" },
  { value: "luxury", label: "Luxury" },
];

const RECOMMENDATION_LABELS: Record<string, { label: string; className: string }> = {
  BEST_OVERALL: { label: "Best Overall", className: "bg-blue-600 text-white" },
  LOWEST_COST: { label: "Lowest Cost", className: "bg-teal-600 text-white" },
  MOST_COMFORTABLE: { label: "Most Comfortable", className: "bg-purple-600 text-white" },
  BEST_VALUE: { label: "Best Value", className: "bg-emerald-600 text-white" },
  BEST_FOR_FAMILY: { label: "Best for Family", className: "bg-amber-500 text-white" },
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

function BudgetCard({ option }: { option: BudgetOption }) {
  const badge = RECOMMENDATION_LABELS[option.recommendation_type] ?? {
    label: option.recommendation_type,
    className: "bg-gray-500 text-white",
  };

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-6 space-y-4">
      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div>
          <p className="font-semibold text-gray-900">
            {option.budget_style.charAt(0).toUpperCase() + option.budget_style.slice(1)} tier
          </p>
          <p className="text-xs text-gray-500 mt-0.5">
            {option.destination || "Global average"} · {option.duration_days} day(s) ·{" "}
            {option.adults} adult(s){option.children > 0 ? `, ${option.children} child(ren)` : ""}
          </p>
        </div>
        <span className={`px-2.5 py-1 rounded-full text-xs font-medium ${badge.className}`}>
          {badge.label}
        </span>
      </div>

      <p className="text-2xl font-bold text-gray-900">
        {option.currency} {option.total_cost_usd.toLocaleString()}
        <span className="text-sm font-normal text-gray-500">
          {" "}
          ({option.currency} {option.cost_per_day_usd}/day)
        </span>
      </p>

      <MatchScoreBar score={option.match_score} />

      <p className="text-sm text-gray-700">{option.reasoning}</p>

      <div className="grid grid-cols-2 gap-2 text-xs text-gray-600 sm:grid-cols-3">
        <div>Flights: {option.currency} {option.flight_cost_usd}</div>
        <div>Accommodation: {option.currency} {option.accommodation_usd}</div>
        <div>Food: {option.currency} {option.food_usd}</div>
        <div>Activities: {option.currency} {option.activities_usd}</div>
        <div>Misc: {option.currency} {option.misc_usd}</div>
      </div>

      {option.risks.length > 0 && (
        <div className="rounded-lg bg-amber-50 border border-amber-200 p-3">
          <p className="text-xs font-semibold text-amber-800 mb-1">Risks</p>
          <ul className="space-y-0.5">
            {option.risks.map((r, i) => (
              <li key={i} className="text-xs text-amber-700">• {r}</li>
            ))}
          </ul>
        </div>
      )}

      {option.assumptions.length > 0 && (
        <ul className="space-y-0.5">
          {option.assumptions.map((a, i) => (
            <li key={i} className="text-xs text-gray-400">• {a}</li>
          ))}
        </ul>
      )}

      <Link
        href={`/budget/${option.budget_option_id}`}
        className="inline-block text-xs font-medium text-blue-600 hover:text-blue-700"
      >
        View full details →
      </Link>
    </div>
  );
}

export default function RecommendBudgetPage() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<BudgetRecommendationResponse | null>(null);

  const [form, setForm] = useState<{
    traveller_id: string;
    trip_id: string;
    destination: string;
    budget_style: string;
    duration_days: number;
    adults: number;
    children: number;
  }>({
    traveller_id: "",
    trip_id: "",
    destination: "",
    budget_style: "balanced",
    duration_days: 7,
    adults: 1,
    children: 0,
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    const payload: RecommendBudgetRequest = {
      ...(form.traveller_id ? { traveller_id: form.traveller_id } : {}),
      ...(form.trip_id ? { trip_id: form.trip_id } : {}),
      ...(form.destination ? { destination: form.destination } : {}),
      budget_style: form.budget_style,
      duration_days: form.duration_days,
      adults: form.adults,
      children: form.children,
    };

    try {
      const recommendation = await recommendBudget(payload);
      setResult(recommendation);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to get budget recommendations");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen bg-gray-50 py-10 px-4">
      <div className="max-w-3xl mx-auto space-y-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Budget Recommendations</h1>
          <p className="text-gray-500">
            Compare backpacker, budget, balanced, comfort, and luxury tiers for your trip,
            ranked against your goal&apos;s budget cap when one is linked.
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
              Destination <span className="text-gray-400">(optional — leave blank for global average rates)</span>
            </label>
            <input
              type="text"
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="e.g. Tokyo"
              value={form.destination}
              onChange={(e) => setForm({ ...form, destination: e.target.value })}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Your usual budget style <span className="text-gray-400">(used as a preference, not a filter)</span>
            </label>
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
              <label className="block text-sm font-medium text-gray-700 mb-1">Duration (days)</label>
              <input
                type="number"
                min={1}
                max={90}
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                value={form.duration_days}
                onChange={(e) => setForm({ ...form, duration_days: parseInt(e.target.value) || 1 })}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Adults</label>
              <input
                type="number"
                min={1}
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
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-3 rounded-xl bg-blue-600 text-white font-semibold text-sm hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {loading ? "Ranking budget options..." : "Get Budget Recommendations"}
          </button>
        </form>

        {result && (
          <div className="space-y-6">
            <div className="bg-white rounded-xl border border-gray-200 p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-2">Summary</h2>
              <p className="text-sm text-gray-700">{result.summary}</p>
            </div>

            <div className="space-y-4">
              {result.budget_options.map((option) => (
                <BudgetCard key={option.budget_option_id} option={option} />
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

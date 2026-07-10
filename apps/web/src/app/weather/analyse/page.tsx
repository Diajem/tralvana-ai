"use client";

import { useState } from "react";
import Link from "next/link";
import { analyseWeather } from "@/lib/api";
import type { AnalyseWeatherRequest, WeatherAssessment } from "@/types/weather";

const KNOWN_DESTINATIONS = [
  "Japan", "Spain", "France", "United Kingdom", "Ireland",
  "USA", "Nigeria", "Ghana", "Jamaica", "UAE",
];

const MONTHS = [
  "January", "February", "March", "April", "May", "June",
  "July", "August", "September", "October", "November", "December",
];

const STATUS_LABELS: Record<string, { label: string; className: string }> = {
  EXCELLENT: { label: "Excellent", className: "bg-green-600 text-white" },
  GOOD: { label: "Good", className: "bg-emerald-500 text-white" },
  ACCEPTABLE: { label: "Acceptable", className: "bg-amber-500 text-white" },
  CHALLENGING: { label: "Challenging", className: "bg-orange-600 text-white" },
  NOT_RECOMMENDED: { label: "Not Recommended", className: "bg-red-600 text-white" },
};

function ScoreBar({ label, score }: { label: string; score: number }) {
  const pct = Math.round(score * 100);
  const colour = pct >= 70 ? "bg-green-500" : pct >= 45 ? "bg-amber-400" : "bg-red-400";
  return (
    <div>
      <div className="flex justify-between text-xs text-gray-500 mb-1">
        <span>{label}</span>
        <span>{pct}%</span>
      </div>
      <div className="h-2 w-full rounded-full bg-gray-200 overflow-hidden">
        <div className={`h-full ${colour} rounded-full`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}

function AssessmentCard({ assessment }: { assessment: WeatherAssessment }) {
  const badge = STATUS_LABELS[assessment.weather_status] ?? {
    label: assessment.weather_status,
    className: "bg-gray-500 text-white",
  };

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-6 space-y-4">
      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div>
          <p className="font-semibold text-gray-900">
            {assessment.destination} — {MONTHS[assessment.month_of_travel - 1]}
          </p>
          <p className="text-xs text-gray-500 mt-0.5">{assessment.season.replace(/_/g, " ")}</p>
        </div>
        <span className={`px-2.5 py-1 rounded-full text-xs font-medium ${badge.className}`}>
          {badge.label}
        </span>
      </div>

      <p className="text-sm text-gray-700">{assessment.weather_summary}</p>

      <ScoreBar label="Weather Suitability" score={assessment.weather_suitability_score} />
      <ScoreBar label="Confidence" score={assessment.confidence} />

      <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
        <ScoreBar label="Outdoor Activity" score={assessment.outdoor_activity_score} />
        <ScoreBar label="Photography" score={assessment.photography_score} />
        <ScoreBar label="Family Suitability" score={assessment.family_score} />
      </div>

      <p className="text-sm text-gray-700">{assessment.explanation}</p>

      <div className="rounded-lg bg-blue-50 border border-blue-200 p-3">
        <p className="text-xs font-semibold text-blue-800 mb-1">Recommendation</p>
        <p className="text-xs text-blue-700">{assessment.recommendation}</p>
      </div>

      {assessment.alternative_months.length > 0 && (
        <div>
          <p className="text-xs font-semibold text-gray-700 mb-1">Alternative Months</p>
          <div className="flex flex-wrap gap-2">
            {assessment.alternative_months.map((m) => (
              <span
                key={m.month}
                className="px-2.5 py-1 rounded-full bg-emerald-50 text-emerald-700 text-xs font-medium"
              >
                {m.month_name} ({STATUS_LABELS[m.weather_status]?.label ?? m.weather_status})
              </span>
            ))}
          </div>
        </div>
      )}

      <div>
        <p className="text-xs font-semibold text-gray-700 mb-1">Packing Recommendations</p>
        <ul className="space-y-0.5">
          {assessment.packing_recommendations.map((p, i) => (
            <li key={i} className="text-xs text-gray-600">• {p}</li>
          ))}
        </ul>
      </div>

      {assessment.risks.length > 0 && (
        <div className="rounded-lg bg-amber-50 border border-amber-200 p-3">
          <p className="text-xs font-semibold text-amber-800 mb-1">Risks</p>
          <ul className="space-y-0.5">
            {assessment.risks.map((r, i) => (
              <li key={i} className="text-xs text-amber-700">• {r}</li>
            ))}
          </ul>
        </div>
      )}

      {assessment.assumptions.length > 0 && (
        <ul className="space-y-0.5">
          {assessment.assumptions.map((a, i) => (
            <li key={i} className="text-xs text-gray-400">• {a}</li>
          ))}
        </ul>
      )}

      <Link
        href={`/weather/${assessment.weather_assessment_id}`}
        className="inline-block text-xs font-medium text-blue-600 hover:text-blue-700"
      >
        View full details →
      </Link>
    </div>
  );
}

export default function AnalyseWeatherPage() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<WeatherAssessment | null>(null);

  const [form, setForm] = useState<{
    traveller_id: string;
    trip_id: string;
    destination: string;
    month_of_travel: string;
  }>({
    traveller_id: "",
    trip_id: "",
    destination: "",
    month_of_travel: "",
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    const payload: AnalyseWeatherRequest = {
      ...(form.traveller_id ? { traveller_id: form.traveller_id } : {}),
      ...(form.trip_id ? { trip_id: form.trip_id } : {}),
      destination: form.destination,
      ...(form.month_of_travel ? { month_of_travel: parseInt(form.month_of_travel) } : {}),
    };

    try {
      const assessment = await analyseWeather(payload);
      setResult(assessment);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to analyse weather");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen bg-gray-50 py-10 px-4">
      <div className="max-w-3xl mx-auto space-y-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Weather &amp; Safety Assessment</h1>
          <p className="text-gray-500">
            A travel decision aid, not a forecast. Leave the month blank to see the best month to visit.
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
                value={form.trip_id}
                onChange={(e) => setForm({ ...form, trip_id: e.target.value })}
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Destination</label>
            <div className="flex flex-wrap gap-2">
              {KNOWN_DESTINATIONS.map((d) => (
                <button
                  key={d}
                  type="button"
                  onClick={() => setForm({ ...form, destination: d })}
                  className={`px-3 py-1.5 rounded-full text-sm font-medium border transition-colors ${
                    form.destination === d
                      ? "bg-indigo-600 text-white border-indigo-600"
                      : "bg-white text-gray-700 border-gray-300 hover:border-indigo-400"
                  }`}
                >
                  {d}
                </button>
              ))}
            </div>
            <input
              type="text"
              required
              placeholder="Or type a destination"
              className="mt-2 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              value={form.destination}
              onChange={(e) => setForm({ ...form, destination: e.target.value })}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Month of Travel <span className="text-gray-400">(optional — leave blank to find the best month)</span>
            </label>
            <select
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              value={form.month_of_travel}
              onChange={(e) => setForm({ ...form, month_of_travel: e.target.value })}
            >
              <option value="">Find the best month</option>
              {MONTHS.map((label, i) => (
                <option key={label} value={i + 1}>{label}</option>
              ))}
            </select>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-3 rounded-xl bg-blue-600 text-white font-semibold text-sm hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {loading ? "Analysing weather and safety..." : "Get Weather & Safety Assessment"}
          </button>
        </form>

        {result && (
          <div className="space-y-6">
            <AssessmentCard assessment={result} />
          </div>
        )}
      </div>
    </main>
  );
}

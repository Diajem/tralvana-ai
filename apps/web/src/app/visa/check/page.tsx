"use client";

import { useState } from "react";
import Link from "next/link";
import { checkVisa } from "@/lib/api";
import type { CheckVisaRequest, VisaAssessment } from "@/types/visa";

const TRAVEL_PURPOSES = [
  { value: "TOURISM", label: "Tourism" },
  { value: "BUSINESS", label: "Business" },
  { value: "TRANSIT", label: "Transit" },
  { value: "STUDY", label: "Study" },
  { value: "WORK", label: "Work" },
  { value: "FAMILY_VISIT", label: "Family Visit" },
  { value: "OTHER", label: "Other" },
];

const STATUS_LABELS: Record<string, { label: string; className: string }> = {
  VISA_NOT_REQUIRED: { label: "Visa Not Required", className: "bg-green-600 text-white" },
  VISA_REQUIRED: { label: "Visa Required", className: "bg-red-600 text-white" },
  ETA_REQUIRED: { label: "ETA Required", className: "bg-amber-500 text-white" },
  EVISA_AVAILABLE: { label: "e-Visa Available", className: "bg-blue-600 text-white" },
  CHECK_MANUALLY: { label: "Check Manually", className: "bg-gray-500 text-white" },
  ENTRY_RESTRICTED: { label: "Entry Restricted", className: "bg-red-800 text-white" },
};

function ConfidenceBar({ score }: { score: number }) {
  const pct = Math.round(score * 100);
  const colour = pct >= 70 ? "bg-green-500" : pct >= 45 ? "bg-amber-400" : "bg-red-400";
  return (
    <div>
      <div className="flex justify-between text-xs text-gray-500 mb-1">
        <span>Confidence</span>
        <span>{pct}%</span>
      </div>
      <div className="h-2 w-full rounded-full bg-gray-200 overflow-hidden">
        <div className={`h-full ${colour} rounded-full`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}

function AssessmentCard({ assessment }: { assessment: VisaAssessment }) {
  const badge = STATUS_LABELS[assessment.visa_status] ?? {
    label: assessment.visa_status,
    className: "bg-gray-500 text-white",
  };

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-6 space-y-4">
      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div>
          <p className="font-semibold text-gray-900">
            {assessment.nationality} → {assessment.destination_country}
          </p>
          <p className="text-xs text-gray-500 mt-0.5">
            {assessment.travel_purpose.replace(/_/g, " ")} · {assessment.intended_length_of_stay} day(s)
            {assessment.visa_type !== "None" ? ` · ${assessment.visa_type}` : ""}
          </p>
        </div>
        <span className={`px-2.5 py-1 rounded-full text-xs font-medium ${badge.className}`}>
          {badge.label}
        </span>
      </div>

      <ConfidenceBar score={assessment.confidence} />

      <p className="text-sm text-gray-700">{assessment.explanation}</p>

      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        <div>
          <p className="text-xs font-semibold text-gray-700 mb-1">Entry Requirements</p>
          <ul className="space-y-0.5">
            {assessment.entry_requirements.map((r, i) => (
              <li key={i} className="text-xs text-gray-600">• {r}</li>
            ))}
          </ul>
        </div>
        <div>
          <p className="text-xs font-semibold text-gray-700 mb-1">Supporting Documents</p>
          <ul className="space-y-0.5">
            {assessment.supporting_documents.map((r, i) => (
              <li key={i} className="text-xs text-gray-600">• {r}</li>
            ))}
          </ul>
        </div>
      </div>

      {assessment.vaccination_requirements.length > 0 && (
        <div>
          <p className="text-xs font-semibold text-gray-700 mb-1">Vaccination Requirements</p>
          <ul className="space-y-0.5">
            {assessment.vaccination_requirements.map((r, i) => (
              <li key={i} className="text-xs text-gray-600">• {r}</li>
            ))}
          </ul>
        </div>
      )}

      <div className="rounded-lg bg-blue-50 border border-blue-200 p-3">
        <p className="text-xs font-semibold text-blue-800 mb-1">Recommendation</p>
        <p className="text-xs text-blue-700">{assessment.recommendation}</p>
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
        href={`/visa/${assessment.visa_assessment_id}`}
        className="inline-block text-xs font-medium text-blue-600 hover:text-blue-700"
      >
        View full details →
      </Link>
    </div>
  );
}

export default function CheckVisaPage() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<VisaAssessment | null>(null);

  const [form, setForm] = useState<{
    traveller_id: string;
    trip_id: string;
    nationality: string;
    passport_country: string;
    destination_country: string;
    transit_countries: string;
    travel_purpose: string;
    intended_length_of_stay: number;
    passport_expiry_date: string;
  }>({
    traveller_id: "",
    trip_id: "",
    nationality: "",
    passport_country: "",
    destination_country: "",
    transit_countries: "",
    travel_purpose: "TOURISM",
    intended_length_of_stay: 14,
    passport_expiry_date: "",
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    const payload: CheckVisaRequest = {
      ...(form.traveller_id ? { traveller_id: form.traveller_id } : {}),
      ...(form.trip_id ? { trip_id: form.trip_id } : {}),
      ...(form.nationality ? { nationality: form.nationality } : {}),
      passport_country: form.passport_country,
      destination_country: form.destination_country,
      transit_countries: form.transit_countries
        .split(",")
        .map((c) => c.trim())
        .filter(Boolean),
      travel_purpose: form.travel_purpose,
      intended_length_of_stay: form.intended_length_of_stay,
      ...(form.passport_expiry_date ? { passport_expiry_date: form.passport_expiry_date } : {}),
    };

    try {
      const assessment = await checkVisa(payload);
      setResult(assessment);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to check visa requirements");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen bg-gray-50 py-10 px-4">
      <div className="max-w-3xl mx-auto space-y-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Visa &amp; Entry Requirements</h1>
          <p className="text-gray-500">
            An explainable travel-planning estimate from deterministic mock data —
            not legal advice. Always verify with an official government source before travelling.
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

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Passport Country <span className="text-gray-400">(required)</span>
              </label>
              <input
                type="text"
                required
                placeholder="e.g. Nigeria or NG"
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                value={form.passport_country}
                onChange={(e) => setForm({ ...form, passport_country: e.target.value })}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Nationality <span className="text-gray-400">(optional, defaults to passport country)</span>
              </label>
              <input
                type="text"
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                value={form.nationality}
                onChange={(e) => setForm({ ...form, nationality: e.target.value })}
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Destination Country <span className="text-gray-400">(required)</span>
            </label>
            <input
              type="text"
              required
              placeholder="e.g. Japan"
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              value={form.destination_country}
              onChange={(e) => setForm({ ...form, destination_country: e.target.value })}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Transit Countries <span className="text-gray-400">(optional, comma-separated)</span>
            </label>
            <input
              type="text"
              placeholder="e.g. UAE, USA"
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              value={form.transit_countries}
              onChange={(e) => setForm({ ...form, transit_countries: e.target.value })}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Travel Purpose</label>
            <div className="flex flex-wrap gap-2">
              {TRAVEL_PURPOSES.map((p) => (
                <button
                  key={p.value}
                  type="button"
                  onClick={() => setForm({ ...form, travel_purpose: p.value })}
                  className={`px-3 py-1.5 rounded-full text-sm font-medium border transition-colors ${
                    form.travel_purpose === p.value
                      ? "bg-blue-600 text-white border-blue-600"
                      : "bg-white text-gray-700 border-gray-300 hover:border-blue-400"
                  }`}
                >
                  {p.label}
                </button>
              ))}
            </div>
          </div>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Intended Length of Stay (days)
              </label>
              <input
                type="number"
                min={1}
                max={365}
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                value={form.intended_length_of_stay}
                onChange={(e) => setForm({ ...form, intended_length_of_stay: parseInt(e.target.value) || 1 })}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Passport Expiry Date <span className="text-gray-400">(optional)</span>
              </label>
              <input
                type="date"
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                value={form.passport_expiry_date}
                onChange={(e) => setForm({ ...form, passport_expiry_date: e.target.value })}
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-3 rounded-xl bg-blue-600 text-white font-semibold text-sm hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {loading ? "Checking entry requirements..." : "Check Entry Requirements"}
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

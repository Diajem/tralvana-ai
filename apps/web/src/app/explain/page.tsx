"use client";

import { Suspense, useState } from "react";
import { useSearchParams } from "next/navigation";
import { explainRecommendation } from "@/lib/api";
import type { Explanation } from "@/types/explain";

function ConfidenceBar({ confidence }: { confidence: number }) {
  const pct = Math.round(confidence * 100);
  const colour = pct >= 75 ? "bg-green-500" : pct >= 40 ? "bg-amber-400" : "bg-red-400";
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

function ExplanationView({ explanation }: { explanation: Explanation }) {
  return (
    <div className="space-y-6">
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <p className="text-sm text-gray-800">{explanation.summary}</p>
        <div className="mt-4">
          <ConfidenceBar confidence={explanation.confidence} />
          <p className="mt-2 text-xs text-gray-500">{explanation.confidence_explanation}</p>
        </div>
      </div>

      {explanation.recommendation_drivers.length > 0 && (
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <h2 className="text-sm font-semibold text-gray-900 mb-3">Why This Was Recommended</h2>
          <ul className="space-y-2">
            {explanation.recommendation_drivers.map((d, i) => (
              <li key={i} className="text-sm text-gray-700">
                <span className="font-medium text-blue-700">{d.module.replace(/_/g, " ")}:</span>{" "}
                {d.driver}
              </li>
            ))}
          </ul>
        </div>
      )}

      {explanation.tradeoffs.length > 0 && (
        <div className="rounded-xl bg-blue-50 border border-blue-200 p-6">
          <h2 className="text-sm font-semibold text-blue-900 mb-3">Key Trade-offs</h2>
          <ul className="space-y-1.5">
            {explanation.tradeoffs.map((t, i) => (
              <li key={i} className="text-sm text-blue-800">• {t}</li>
            ))}
          </ul>
        </div>
      )}

      {explanation.alternatives_considered.length > 0 && (
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <h2 className="text-sm font-semibold text-gray-900 mb-3">Alternatives Considered</h2>
          <ul className="space-y-2">
            {explanation.alternatives_considered.map((a, i) => (
              <li key={i} className="text-sm text-gray-700">
                <span className="font-medium">{a.module.replace(/_/g, " ")}:</span> {a.alternative}
                <span className="block text-xs text-gray-500">{a.why_not_chosen}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {explanation.risks.length > 0 && (
        <div className="rounded-xl bg-amber-50 border border-amber-200 p-6">
          <h2 className="text-sm font-semibold text-amber-800 mb-3">Risks</h2>
          <ul className="space-y-1.5">
            {explanation.risks.map((r, i) => (
              <li key={i} className="text-sm text-amber-700">• {r}</li>
            ))}
          </ul>
        </div>
      )}

      {explanation.assumptions.length > 0 && (
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <h2 className="text-sm font-semibold text-gray-900 mb-3">Assumptions</h2>
          <ul className="space-y-1">
            {explanation.assumptions.map((a, i) => (
              <li key={i} className="text-xs text-gray-500">• {a}</li>
            ))}
          </ul>
        </div>
      )}

      {explanation.missing_information.length > 0 && (
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <h2 className="text-sm font-semibold text-gray-900 mb-3">Missing Information</h2>
          <ul className="space-y-1">
            {explanation.missing_information.map((m, i) => (
              <li key={i} className="text-xs text-gray-500">• {m}</li>
            ))}
          </ul>
        </div>
      )}

      {explanation.what_would_change_the_result.length > 0 && (
        <div className="rounded-xl bg-gray-50 border border-gray-200 p-6">
          <h2 className="text-sm font-semibold text-gray-900 mb-3">What Could Change This</h2>
          <ul className="space-y-1.5">
            {explanation.what_would_change_the_result.map((c, i) => (
              <li key={i} className="text-sm text-gray-700">• {c}</li>
            ))}
          </ul>
        </div>
      )}

      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <h2 className="text-sm font-semibold text-gray-900 mb-3">Source Modules</h2>
        <div className="flex flex-wrap gap-2">
          {explanation.source_modules.map((s, i) => (
            <span
              key={i}
              className={`px-3 py-1 rounded-full text-xs font-medium ${
                s.status === "failed"
                  ? "bg-red-100 text-red-700"
                  : "bg-gray-100 text-gray-700"
              }`}
            >
              {s.module.replace(/_/g, " ")} — {s.status}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}

function ExplainPageContent() {
  const searchParams = useSearchParams();

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [explanation, setExplanation] = useState<Explanation | null>(null);

  const [form, setForm] = useState({
    conversation_id: searchParams.get("conversation_id") ?? "",
    trip_id: searchParams.get("trip_id") ?? "",
    question: "",
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const result = await explainRecommendation({
        ...(form.conversation_id ? { conversation_id: form.conversation_id } : {}),
        ...(form.trip_id ? { trip_id: form.trip_id } : {}),
        ...(form.question ? { question: form.question } : {}),
      });
      setExplanation(result);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to get explanation");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen bg-gray-50 py-10 px-4">
      <div className="max-w-3xl mx-auto space-y-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Explain This Recommendation</h1>
          <p className="text-gray-500">
            Ask why Tralvana recommended what it did — drivers, trade-offs, assumptions, risks,
            and what would change the answer. Reuses the reasoning already produced, nothing is
            recalculated here.
          </p>
        </div>

        {error && (
          <div className="rounded-lg bg-red-50 border border-red-200 p-4 text-red-700">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4 bg-white rounded-2xl shadow p-8">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Conversation ID <span className="text-gray-400">(optional)</span>
              </label>
              <input
                type="text"
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                value={form.conversation_id}
                onChange={(e) => setForm({ ...form, conversation_id: e.target.value })}
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
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Question <span className="text-gray-400">(optional — e.g. &quot;why not the cheaper option?&quot;)</span>
            </label>
            <input
              type="text"
              placeholder="Why did you recommend this?"
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              value={form.question}
              onChange={(e) => setForm({ ...form, question: e.target.value })}
            />
          </div>

          <button
            type="submit"
            disabled={loading || (!form.conversation_id && !form.trip_id)}
            className="w-full py-3 rounded-xl bg-blue-600 text-white font-semibold text-sm hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {loading ? "Explaining..." : "Explain This Recommendation"}
          </button>
          {!form.conversation_id && !form.trip_id && (
            <p className="text-xs text-gray-400 text-center">
              Provide a conversation ID or trip ID from a previous &quot;plan a trip&quot; request.
            </p>
          )}
        </form>

        {explanation && <ExplanationView explanation={explanation} />}
      </div>
    </main>
  );
}

export default function ExplainPage() {
  return (
    <Suspense fallback={null}>
      <ExplainPageContent />
    </Suspense>
  );
}

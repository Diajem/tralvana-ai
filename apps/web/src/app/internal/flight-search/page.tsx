"use client";

import { useState } from "react";
import { runFlightSearchDiagnostic } from "@/lib/api";

type Diagnostic = {
  booking_attempted: boolean;
  origin: string;
  destination: string;
  data_source: string;
  provider_status: string;
  results_count: number;
  request_id: string;
  sample: Record<string, unknown> | null;
};

export default function FlightSearchDiagnosticPage() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<Diagnostic | null>(null);
  const [error, setError] = useState("");

  async function runSearch() {
    setLoading(true);
    setError("");
    setResult(null);
    try {
      setResult(await runFlightSearchDiagnostic() as Diagnostic);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Search failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen bg-gray-50 px-4 py-12">
      <div className="mx-auto max-w-2xl space-y-6 rounded-2xl bg-white p-8 shadow">
        <div>
          <p className="text-sm font-semibold uppercase tracking-wide text-indigo-600">Internal diagnostic</p>
          <h1 className="mt-2 text-3xl font-bold text-gray-900">Live Duffel flight search</h1>
          <p className="mt-2 text-gray-600">LHR → JFK · 10–17 November 2026 · one adult</p>
          <p className="mt-1 text-sm text-gray-500">Search only. This cannot create an order, hold, payment, or booking.</p>
        </div>
        <button
          type="button"
          onClick={runSearch}
          disabled={loading}
          className="rounded-xl bg-indigo-600 px-5 py-3 font-semibold text-white disabled:opacity-50"
        >
          {loading ? "Searching Duffel…" : "Run live control search"}
        </button>
        {error && <p className="rounded-lg bg-red-50 p-4 text-red-700">{error}</p>}
        {result && (
          <dl className="grid grid-cols-2 gap-4 rounded-xl border border-gray-200 p-5 text-sm">
            <dt className="text-gray-500">Data source</dt><dd className="font-semibold">{result.data_source}</dd>
            <dt className="text-gray-500">Provider status</dt><dd className="font-semibold">{result.provider_status}</dd>
            <dt className="text-gray-500">Offers</dt><dd className="font-semibold">{result.results_count}</dd>
            <dt className="text-gray-500">Request ID</dt><dd className="break-all font-mono text-xs">{result.request_id || "—"}</dd>
            <dt className="text-gray-500">Booking attempted</dt><dd className="font-semibold">{String(result.booking_attempted)}</dd>
            <dt className="text-gray-500">First mapped offer</dt><dd className="break-words font-mono text-xs">{result.sample ? JSON.stringify(result.sample) : "None"}</dd>
          </dl>
        )}
      </div>
    </main>
  );
}

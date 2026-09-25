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

  const [route, setRoute] = useState<"control" | "jamaica">("control");

  async function runSearch() {
    setLoading(true);
    setError("");
    setResult(null);
    try {
      const params = route === "control"
        ? { origin: "LHR", destination: "JFK", departure_date: "2026-11-10", return_date: "2026-11-17" }
        : { origin: "VIE", destination: "MBJ", departure_date: "2026-10-10", return_date: "2026-10-22" };
      setResult(await runFlightSearchDiagnostic(params) as Diagnostic);
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
          <p className="mt-2 text-gray-600">
            {route === "control"
              ? "LHR → JFK · 10–17 November 2026 · one adult"
              : "VIE → MBJ · 10–22 October 2026 · one adult"}
          </p>
          <p className="mt-1 text-sm text-gray-500">Search only. This cannot create an order, hold, payment, or booking.</p>
        </div>
        <div className="flex flex-wrap gap-3">
          <button
            type="button"
            onClick={() => { setRoute("control"); setResult(null); setError(""); }}
            className={`rounded-xl border px-4 py-2 font-semibold ${route === "control" ? "border-indigo-600 bg-indigo-50 text-indigo-700" : "border-gray-300 text-gray-700"}`}
          >
            LHR → JFK control
          </button>
          <button
            type="button"
            onClick={() => { setRoute("jamaica"); setResult(null); setError(""); }}
            className={`rounded-xl border px-4 py-2 font-semibold ${route === "jamaica" ? "border-indigo-600 bg-indigo-50 text-indigo-700" : "border-gray-300 text-gray-700"}`}
          >
            VIE → MBJ test
          </button>
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

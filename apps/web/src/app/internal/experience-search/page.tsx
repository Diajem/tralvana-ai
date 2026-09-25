"use client";

import { useState } from "react";
import { runExperienceSearchDiagnostic } from "@/lib/api";

type Diagnostic = {
  booking_attempted: boolean;
  destination: string;
  resolved_destination: string | null;
  environment: string | null;
  provider: string | null;
  results_count: number;
  booking_enabled: boolean;
  sample: Record<string, unknown> | null;
};

const destinations = [
  "Montego Bay, Jamaica",
  "London, United Kingdom",
  "New York City, USA",
  "Vienna, Austria",
];

export default function ExperienceSearchDiagnosticPage() {
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<Diagnostic[]>([]);
  const [error, setError] = useState("");

  async function runSearches() {
    setLoading(true);
    setError("");
    setResults([]);
    try {
      const completed = await Promise.all(
        destinations.map((destination) =>
          runExperienceSearchDiagnostic({
            destination,
            start_date: "2026-10-10",
            end_date: "2026-10-22",
          }) as Promise<Diagnostic>
        )
      );
      setResults(completed);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Viator search failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen bg-gray-50 px-4 py-12">
      <div className="mx-auto max-w-4xl space-y-6 rounded-2xl bg-white p-8 shadow">
        <div>
          <p className="text-sm font-semibold uppercase tracking-wide text-indigo-600">Internal diagnostic</p>
          <h1 className="mt-2 text-3xl font-bold text-gray-900">Viator multi-destination inventory</h1>
          <p className="mt-2 text-gray-600">Jamaica, London, New York and Vienna · 10–22 October 2026</p>
          <p className="mt-1 text-sm text-gray-500">
            Search only. Booking and payment remain disabled pending Full + Booking approval and certification.
          </p>
        </div>
        <button
          type="button"
          onClick={runSearches}
          disabled={loading}
          className="rounded-xl bg-indigo-600 px-5 py-3 font-semibold text-white disabled:opacity-50"
        >
          {loading ? "Searching Viator…" : "Run four destination searches"}
        </button>
        {error && <p className="rounded-lg bg-red-50 p-4 text-red-700">{error}</p>}
        <div className="grid gap-4 md:grid-cols-2">
          {results.map((result) => (
            <section key={result.destination} className="rounded-xl border border-gray-200 p-5 text-sm">
              <h2 className="text-lg font-bold text-gray-900">{result.destination}</h2>
              <dl className="mt-3 grid grid-cols-2 gap-2">
                <dt className="text-gray-500">Resolved as</dt><dd>{result.resolved_destination ?? "—"}</dd>
                <dt className="text-gray-500">Environment</dt><dd>{result.environment ?? "—"}</dd>
                <dt className="text-gray-500">Products</dt><dd>{result.results_count}</dd>
                <dt className="text-gray-500">Booking enabled</dt><dd>{String(result.booking_enabled)}</dd>
              </dl>
              <p className="mt-3 break-words font-mono text-xs">
                {result.sample ? JSON.stringify(result.sample) : "No mapped product returned"}
              </p>
            </section>
          ))}
        </div>
      </div>
    </main>
  );
}

"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { listSavedPlans } from "@/lib/api";
import { useTralvanaAuth } from "@/lib/auth-context";
import type { SavedPlanSummary } from "@/types/planner";

function formatSavedAt(value: string): string {
  const date = new Date(value);
  return Number.isNaN(date.getTime())
    ? value
    : new Intl.DateTimeFormat("en-GB", { dateStyle: "medium", timeStyle: "short" }).format(date);
}

export default function MyTripsPage() {
  const { clerkEnabled, loaded, signedIn, getSessionToken } = useTralvanaAuth();
  const [trips, setTrips] = useState<SavedPlanSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (clerkEnabled && (!loaded || !signedIn)) return;
    let active = true;
    const load = async () => {
      const token = clerkEnabled
        ? await getSessionToken() ?? undefined
        : undefined;
      return listSavedPlans(token);
    };
    load()
      .then((saved) => { if (active) setTrips(saved); })
      .catch((err: unknown) => {
        if (active) setError(err instanceof Error ? err.message : "Unable to load saved trips");
      })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [clerkEnabled, getSessionToken, loaded, signedIn]);

  return (
    <main className="min-h-screen bg-slate-50 px-4 py-8 sm:px-6 sm:py-10">
      <div className="mx-auto max-w-5xl space-y-8">
        <nav className="flex items-center justify-between gap-4">
          <Link href="/" className="text-xl font-bold tracking-tight text-slate-950">Tralvana <span className="text-indigo-600">AI</span></Link>
          <Link href="/planner" className="rounded-full bg-indigo-600 px-4 py-2 text-sm font-bold text-white hover:bg-indigo-700">Plan a new trip</Link>
        </nav>

        <header>
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-indigo-600">Saved to your account</p>
          <h1 className="mt-3 text-4xl font-bold tracking-tight text-slate-950">My Trips</h1>
          <p className="mt-3 text-slate-600">Return to any plan and continue the same conversation with Tralvana AI.</p>
        </header>

        {loading && <p className="rounded-xl border bg-white p-5 text-sm text-slate-600">Loading your saved trips…</p>}
        {error && <p className="rounded-xl border border-red-200 bg-red-50 p-5 text-sm text-red-700">{error}</p>}
        {!loading && !error && trips.length === 0 && (
          <div className="rounded-2xl border border-slate-200 bg-white p-8 text-center">
            <h2 className="text-lg font-bold text-slate-950">No saved trips yet</h2>
            <p className="mt-2 text-sm text-slate-600">Your next planner conversation will appear here automatically.</p>
            <Link href="/planner" className="mt-5 inline-block rounded-xl bg-indigo-600 px-5 py-3 text-sm font-bold text-white">Start planning</Link>
          </div>
        )}

        <div className="grid gap-4 md:grid-cols-2">
          {trips.map((trip) => (
            <Link
              key={trip.conversation_id}
              href={`/planner?conversation=${encodeURIComponent(trip.conversation_id)}#overview`}
              className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm transition hover:border-indigo-300 hover:shadow-md"
            >
              <div className="flex items-start justify-between gap-4">
                <div>
                  <p className="text-xs font-bold uppercase tracking-wide text-indigo-600">{trip.status}</p>
                  <h2 className="mt-2 text-xl font-bold text-slate-950">{trip.title}</h2>
                </div>
                <span className="text-indigo-600">→</span>
              </div>
              <dl className="mt-5 space-y-2 text-sm">
                <div><dt className="inline text-slate-400">Route: </dt><dd className="inline font-medium text-slate-800">{trip.origin} → {trip.destination}</dd></div>
                <div><dt className="inline text-slate-400">When: </dt><dd className="inline text-slate-700">{trip.travel_period}</dd></div>
                <div><dt className="inline text-slate-400">Saved: </dt><dd className="inline text-slate-700">{formatSavedAt(trip.updated_at)}</dd></div>
              </dl>
            </Link>
          ))}
        </div>
      </div>
    </main>
  );
}

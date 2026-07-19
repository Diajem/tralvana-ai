"use client";

import { useState } from "react";
import { followAffiliateProgramme } from "@/lib/api";
import type { AffiliateProgramme } from "@/types/commercial";

export function AffiliateCheckout({
  programme,
  recommendationReference,
}: {
  programme: AffiliateProgramme;
  recommendationReference: string;
}) {
  const [opening, setOpening] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function follow() {
    setOpening(true);
    setError(null);
    try {
      await followAffiliateProgramme(programme, recommendationReference);
    } catch {
      setError("The partner link is temporarily unavailable. Please try again later.");
      setOpening(false);
    }
  }

  return (
    <aside className="rounded-xl border border-indigo-200 bg-indigo-50 p-6">
      <h2 className="text-lg font-semibold text-gray-900">Check live availability</h2>
      <p className="mt-2 text-sm text-gray-700">
        Continue to {programme.partner} to search current prices. This recommendation is not a
        reservation; the partner&apos;s price and availability may differ.
      </p>
      <p className="mt-3 text-xs font-medium text-indigo-900">{programme.disclosure_text}</p>
      <button
        type="button"
        onClick={follow}
        disabled={opening}
        className="mt-4 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-700 disabled:cursor-wait disabled:opacity-60"
      >
        {opening ? "Opening partner…" : `Continue to ${programme.partner} →`}
      </button>
      {error && <p className="mt-3 text-xs text-red-700">{error}</p>}
    </aside>
  );
}

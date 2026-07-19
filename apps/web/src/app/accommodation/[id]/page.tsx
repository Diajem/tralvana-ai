import { AffiliateCheckout } from "@/components/commercial/AffiliateCheckout";
import { getAccommodationOption, getAffiliateProgrammes } from "@/lib/api";
import type { AccommodationOption } from "@/types/accommodation";
import { notFound } from "next/navigation";

const RECOMMENDATION_LABELS: Record<string, { label: string; className: string }> = {
  BEST_OVERALL: { label: "Best Overall", className: "bg-blue-600 text-white" },
  BEST_VALUE: { label: "Best Value", className: "bg-emerald-600 text-white" },
  BEST_LOCATION: { label: "Best Location", className: "bg-indigo-600 text-white" },
  BEST_COMFORT: { label: "Best Comfort", className: "bg-purple-600 text-white" },
  BEST_FOR_FAMILY: { label: "Best for Family", className: "bg-amber-500 text-white" },
  BEST_FOR_BUSINESS: { label: "Best for Business", className: "bg-slate-700 text-white" },
  BEST_BUDGET: { label: "Best Budget", className: "bg-teal-600 text-white" },
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

function SubScoreBar({ label, score }: { label: string; score: number }) {
  const pct = Math.round(score * 100);
  return (
    <div>
      <div className="flex justify-between text-xs text-gray-500 mb-1">
        <span>{label}</span>
        <span>{pct}%</span>
      </div>
      <div className="h-1.5 w-full rounded-full bg-gray-200 overflow-hidden">
        <div className="h-full bg-indigo-400 rounded-full" style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}

export default async function AccommodationOptionPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  let accommodation: AccommodationOption;
  const affiliateProgrammes = await getAffiliateProgrammes().catch(() => []);
  const expedia = affiliateProgrammes.find((programme) => programme.partner === "Expedia");
  try {
    accommodation = await getAccommodationOption(id);
  } catch {
    notFound();
  }

  const badge = RECOMMENDATION_LABELS[accommodation.recommendation_type] ?? {
    label: accommodation.recommendation_type,
    className: "bg-gray-500 text-white",
  };

  const sandboxBanner =
    accommodation.data_source === "DUFFEL_STAYS_SANDBOX"
      ? "Duffel Stays sandbox data — not available for purchase."
      : accommodation.data_source === "MOCK_FALLBACK"
        ? "Duffel Stays sandbox was unavailable — showing mock fallback data, not real inventory."
        : null;

  return (
    <main className="min-h-screen bg-gray-50 py-10 px-4">
      <div className="max-w-3xl mx-auto space-y-8">

        {sandboxBanner && (
          <div className="rounded-lg bg-sky-50 border border-sky-200 p-4 text-sky-800 text-sm font-medium">
            {sandboxBanner}
          </div>
        )}

        {expedia && accommodation.data_source !== "DUFFEL_STAYS_SANDBOX" && (
          <AffiliateCheckout
            programme={expedia}
            recommendationReference={accommodation.accommodation_option_id}
          />
        )}

        {/* Header */}
        <div className="bg-white rounded-2xl shadow p-8">
          <div className="flex items-start justify-between gap-4 flex-wrap">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">{accommodation.property_name}</h1>
              <p className="text-gray-500 mt-1 text-sm">
                {accommodation.neighbourhood}, {accommodation.destination}
              </p>
            </div>
            <span className={`px-2.5 py-1 rounded-full text-xs font-medium ${badge.className}`}>
              {badge.label}
            </span>
          </div>

          <div className="mt-6 grid grid-cols-2 gap-4 sm:grid-cols-4 text-sm">
            <div>
              <p className="text-gray-400 text-xs mb-0.5">Type</p>
              <p className="font-medium text-gray-900">{accommodation.accommodation_type.replace(/_/g, " ")}</p>
            </div>
            <div>
              <p className="text-gray-400 text-xs mb-0.5">Star Rating</p>
              <p className="font-medium text-gray-900">{accommodation.star_rating}-star</p>
            </div>
            <div>
              <p className="text-gray-400 text-xs mb-0.5">Nightly Price</p>
              <p className="font-medium text-gray-900">
                {accommodation.currency} {accommodation.nightly_price.toLocaleString()}
              </p>
            </div>
            <div>
              <p className="text-gray-400 text-xs mb-0.5">Total Price</p>
              <p className="font-medium text-gray-900">
                {accommodation.currency} {accommodation.total_price.toLocaleString()}
              </p>
            </div>
          </div>

          <div className="mt-6">
            <MatchScoreBar score={accommodation.match_score} />
          </div>
        </div>

        {/* Score breakdown */}
        <div className="bg-white rounded-xl border border-gray-200 p-6 space-y-4">
          <h2 className="text-lg font-semibold text-gray-900 mb-1">Score Breakdown</h2>
          <SubScoreBar label="Comfort" score={accommodation.comfort_score} />
          <SubScoreBar label="Location" score={accommodation.location_score} />
          <SubScoreBar label="Safety" score={accommodation.safety_score} />
        </div>

        {/* Property details */}
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Property Details</h2>
          <table className="w-full text-sm">
            <tbody>
              <tr className="border-b border-gray-100">
                <td className="py-2 text-gray-600">Distance to Centre</td>
                <td className="py-2 text-right font-medium text-gray-900">{accommodation.distance_to_centre} km</td>
              </tr>
              <tr className="border-b border-gray-100">
                <td className="py-2 text-gray-600">Distance to Transport</td>
                <td className="py-2 text-right font-medium text-gray-900">{accommodation.distance_to_transport} km</td>
              </tr>
              <tr className="border-b border-gray-100">
                <td className="py-2 text-gray-600">Breakfast</td>
                <td className="py-2 text-right font-medium text-gray-900">
                  {accommodation.breakfast_included ? "Included" : "Not included"}
                </td>
              </tr>
              <tr className="border-b border-gray-100">
                <td className="py-2 text-gray-600">Cancellation Policy</td>
                <td className="py-2 text-right font-medium text-gray-900 capitalize">
                  {accommodation.cancellation_policy.replace(/_/g, " ")}
                </td>
              </tr>
              <tr className="border-b border-gray-100">
                <td className="py-2 text-gray-600">Guest Review Score</td>
                <td className="py-2 text-right font-medium text-gray-900">{accommodation.review_score}/10</td>
              </tr>
              <tr className="border-b border-gray-100">
                <td className="py-2 text-gray-600">Family Friendly</td>
                <td className="py-2 text-right font-medium text-gray-900">
                  {accommodation.family_friendly ? "Yes" : "No"}
                </td>
              </tr>
              <tr>
                <td className="py-2 text-gray-600">Business Friendly</td>
                <td className="py-2 text-right font-medium text-gray-900">
                  {accommodation.business_friendly ? "Yes" : "No"}
                </td>
              </tr>
            </tbody>
          </table>
          {accommodation.accessibility_features.length > 0 && (
            <div className="mt-4 pt-4 border-t border-gray-100">
              <p className="text-xs text-gray-500 mb-2">Accessibility Features</p>
              <div className="flex flex-wrap gap-2">
                {accommodation.accessibility_features.map((f, i) => (
                  <span key={i} className="px-2.5 py-1 rounded-full bg-gray-100 text-gray-700 text-xs">
                    {f.replace(/_/g, " ")}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Explanation */}
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-3">Why This Match Score</h2>
          <p className="text-sm text-gray-700">{accommodation.reasoning}</p>
        </div>

        {/* Risks */}
        {accommodation.risks.length > 0 && (
          <div>
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Risks</h2>
            <div className="space-y-3">
              {accommodation.risks.map((risk, i) => (
                <div
                  key={i}
                  className="border-l-4 border-l-amber-400 bg-amber-50 rounded-r-lg px-4 py-3"
                >
                  <p className="text-sm text-gray-800">{risk}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Assumptions */}
        {accommodation.assumptions.length > 0 && (
          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-3">Assumptions</h2>
            <ul className="space-y-1">
              {accommodation.assumptions.map((a, i) => (
                <li key={i} className="text-sm text-gray-600">• {a}</li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </main>
  );
}

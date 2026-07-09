import { getDestinationOption } from "@/lib/api";
import type { DestinationOption } from "@/types/destination";
import { notFound } from "next/navigation";

const RECOMMENDATION_LABELS: Record<string, { label: string; className: string }> = {
  BEST_OVERALL: { label: "Best Overall", className: "bg-blue-600 text-white" },
  BEST_FOR_FOOD: { label: "Best for Food", className: "bg-emerald-600 text-white" },
  BEST_FOR_FOOTBALL: { label: "Best for Football", className: "bg-green-700 text-white" },
  BEST_FOR_CULTURE: { label: "Best for Culture", className: "bg-indigo-600 text-white" },
  BEST_FOR_FAMILY: { label: "Best for Family", className: "bg-amber-500 text-white" },
  BEST_FOR_BUDGET: { label: "Best for Budget", className: "bg-teal-600 text-white" },
  BEST_FOR_PHOTOGRAPHY: { label: "Best for Photography", className: "bg-purple-600 text-white" },
  BEST_HIDDEN_GEM: { label: "Hidden Gem", className: "bg-fuchsia-600 text-white" },
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

export default async function DestinationOptionPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  let destination: DestinationOption;
  try {
    destination = await getDestinationOption(id);
  } catch {
    notFound();
  }

  const badge = RECOMMENDATION_LABELS[destination.recommendation_type] ?? {
    label: destination.recommendation_type,
    className: "bg-gray-500 text-white",
  };

  return (
    <main className="min-h-screen bg-gray-50 py-10 px-4">
      <div className="max-w-3xl mx-auto space-y-8">

        {/* Header */}
        <div className="bg-white rounded-2xl shadow p-8">
          <div className="flex items-start justify-between gap-4 flex-wrap">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">{destination.name}</h1>
              <p className="text-gray-500 mt-1 text-sm">
                {destination.destination_type === "CITY"
                  ? `${destination.country} · ${destination.region}`
                  : `${destination.neighbourhood ? `${destination.neighbourhood}, ` : ""}${destination.city}, ${destination.country}`}
              </p>
            </div>
            <span className={`px-2.5 py-1 rounded-full text-xs font-medium ${badge.className}`}>
              {badge.label}
            </span>
          </div>

          <p className="mt-4 text-sm text-gray-700">{destination.description}</p>

          {destination.interests_matched.length > 0 && (
            <div className="mt-4 flex flex-wrap gap-1.5">
              {destination.interests_matched.map((interest) => (
                <span
                  key={interest}
                  className="px-2 py-0.5 rounded-full bg-blue-50 text-blue-700 text-xs font-medium"
                >
                  {interest}
                </span>
              ))}
            </div>
          )}

          <div className="mt-6">
            <MatchScoreBar score={destination.match_score} />
          </div>
        </div>

        {/* Score breakdown */}
        <div className="bg-white rounded-xl border border-gray-200 p-6 space-y-4">
          <h2 className="text-lg font-semibold text-gray-900 mb-1">Score Breakdown</h2>
          <SubScoreBar label="Food" score={destination.food_score} />
          <SubScoreBar label="Culture" score={destination.culture_score} />
          <SubScoreBar label="Football" score={destination.football_score} />
          <SubScoreBar label="Nightlife" score={destination.nightlife_score} />
          <SubScoreBar label="Family Suitability" score={destination.family_score} />
          <SubScoreBar label="Safety" score={destination.safety_score} />
          <SubScoreBar label="Budget Fit (affordability)" score={destination.budget_score} />
          <SubScoreBar label="Transport Access" score={destination.transport_access_score} />
          <SubScoreBar label="Season Fit" score={destination.season_score} />
        </div>

        {/* Details */}
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Details</h2>
          <table className="w-full text-sm">
            <tbody>
              <tr className="border-b border-gray-100">
                <td className="py-2 text-gray-600">Type</td>
                <td className="py-2 text-right font-medium text-gray-900">
                  {destination.destination_type.replace(/_/g, " ")}
                </td>
              </tr>
              <tr className="border-b border-gray-100">
                <td className="py-2 text-gray-600">Distance from Centre</td>
                <td className="py-2 text-right font-medium text-gray-900">{destination.distance_from_centre} km</td>
              </tr>
              <tr>
                <td className="py-2 text-gray-600">Region</td>
                <td className="py-2 text-right font-medium text-gray-900">{destination.region}</td>
              </tr>
            </tbody>
          </table>
          {destination.best_for.length > 0 && (
            <div className="mt-4 pt-4 border-t border-gray-100">
              <p className="text-xs text-gray-500 mb-2">Best For</p>
              <div className="flex flex-wrap gap-2">
                {destination.best_for.map((b, i) => (
                  <span key={i} className="px-2.5 py-1 rounded-full bg-gray-100 text-gray-700 text-xs">
                    {b}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Explanation */}
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-3">Why This Match Score</h2>
          <p className="text-sm text-gray-700">{destination.reasoning}</p>
        </div>

        {/* Risks */}
        {destination.risks.length > 0 && (
          <div>
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Risks</h2>
            <div className="space-y-3">
              {destination.risks.map((risk, i) => (
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
        {destination.assumptions.length > 0 && (
          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-3">Assumptions</h2>
            <ul className="space-y-1">
              {destination.assumptions.map((a, i) => (
                <li key={i} className="text-sm text-gray-600">• {a}</li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </main>
  );
}

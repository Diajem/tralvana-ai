import { getBudgetOption } from "@/lib/api";
import type { BudgetOption } from "@/types/budget";
import { notFound } from "next/navigation";

const RECOMMENDATION_LABELS: Record<string, { label: string; className: string }> = {
  BEST_OVERALL: { label: "Best Overall", className: "bg-blue-600 text-white" },
  LOWEST_COST: { label: "Lowest Cost", className: "bg-teal-600 text-white" },
  MOST_COMFORTABLE: { label: "Most Comfortable", className: "bg-purple-600 text-white" },
  BEST_VALUE: { label: "Best Value", className: "bg-emerald-600 text-white" },
  BEST_FOR_FAMILY: { label: "Best for Family", className: "bg-amber-500 text-white" },
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

export default async function BudgetOptionPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  let option: BudgetOption;
  try {
    option = await getBudgetOption(id);
  } catch {
    notFound();
  }

  const badge = RECOMMENDATION_LABELS[option.recommendation_type] ?? {
    label: option.recommendation_type,
    className: "bg-gray-500 text-white",
  };

  return (
    <main className="min-h-screen bg-gray-50 py-10 px-4">
      <div className="max-w-3xl mx-auto space-y-8">

        {/* Header */}
        <div className="bg-white rounded-2xl shadow p-8">
          <div className="flex items-start justify-between gap-4 flex-wrap">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">
                {option.budget_style.charAt(0).toUpperCase() + option.budget_style.slice(1)} tier
              </h1>
              <p className="text-gray-500 mt-1 text-sm">
                {option.destination || "Global average"} · {option.duration_days} day(s) ·{" "}
                {option.adults} adult(s){option.children > 0 ? `, ${option.children} child(ren)` : ""}
              </p>
            </div>
            <span className={`px-2.5 py-1 rounded-full text-xs font-medium ${badge.className}`}>
              {badge.label}
            </span>
          </div>

          <p className="mt-4 text-3xl font-bold text-gray-900">
            {option.currency} {option.total_cost_usd.toLocaleString()}
          </p>
          <p className="text-sm text-gray-500">
            {option.currency} {option.cost_per_day_usd}/day · {option.currency}{" "}
            {option.cost_per_person_usd}/person
          </p>

          <div className="mt-6">
            <MatchScoreBar score={option.match_score} />
          </div>
        </div>

        {/* Cost breakdown */}
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Cost Breakdown</h2>
          <table className="w-full text-sm">
            <tbody>
              <tr className="border-b border-gray-100">
                <td className="py-2 text-gray-600">Flights</td>
                <td className="py-2 text-right font-medium text-gray-900">
                  {option.currency} {option.flight_cost_usd.toLocaleString()}
                </td>
              </tr>
              <tr className="border-b border-gray-100">
                <td className="py-2 text-gray-600">Accommodation</td>
                <td className="py-2 text-right font-medium text-gray-900">
                  {option.currency} {option.accommodation_usd.toLocaleString()}
                </td>
              </tr>
              <tr className="border-b border-gray-100">
                <td className="py-2 text-gray-600">Food</td>
                <td className="py-2 text-right font-medium text-gray-900">
                  {option.currency} {option.food_usd.toLocaleString()}
                </td>
              </tr>
              <tr className="border-b border-gray-100">
                <td className="py-2 text-gray-600">Activities</td>
                <td className="py-2 text-right font-medium text-gray-900">
                  {option.currency} {option.activities_usd.toLocaleString()}
                </td>
              </tr>
              <tr>
                <td className="py-2 text-gray-600">Miscellaneous</td>
                <td className="py-2 text-right font-medium text-gray-900">
                  {option.currency} {option.misc_usd.toLocaleString()}
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        {/* Score breakdown */}
        <div className="bg-white rounded-xl border border-gray-200 p-6 space-y-4">
          <h2 className="text-lg font-semibold text-gray-900 mb-1">Tier Characteristics</h2>
          <SubScoreBar label="Affordability" score={option.affordability_score} />
          <SubScoreBar label="Comfort" score={option.comfort_score} />
          <SubScoreBar label="Cost Certainty" score={option.cost_certainty_score} />
          <SubScoreBar label="Family Suitability" score={option.family_suitability_score} />
        </div>

        {/* Explanation */}
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-3">Why This Match Score</h2>
          <p className="text-sm text-gray-700">{option.reasoning}</p>
        </div>

        {/* Risks */}
        {option.risks.length > 0 && (
          <div>
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Risks</h2>
            <div className="space-y-3">
              {option.risks.map((risk, i) => (
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
        {option.assumptions.length > 0 && (
          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-3">Assumptions</h2>
            <ul className="space-y-1">
              {option.assumptions.map((a, i) => (
                <li key={i} className="text-sm text-gray-600">• {a}</li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </main>
  );
}

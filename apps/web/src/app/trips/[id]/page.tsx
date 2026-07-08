import { getTripPlan } from "@/lib/api";
import type { TripPlan, DayPlan, TripRisk, BudgetBreakdown } from "@/types/trip";
import { notFound } from "next/navigation";

// ------------------------------------------------------------------
// Sub-components
// ------------------------------------------------------------------

function StatusBadge({ status }: { status: string }) {
  const map: Record<string, string> = {
    READY: "bg-green-100 text-green-800",
    DRAFT: "bg-yellow-100 text-yellow-800",
    NEEDS_INFORMATION: "bg-amber-100 text-amber-800",
    ARCHIVED: "bg-gray-100 text-gray-600",
  };
  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
        map[status] ?? "bg-gray-100 text-gray-700"
      }`}
    >
      {status.replace(/_/g, " ")}
    </span>
  );
}

function ConfidenceBar({ confidence }: { confidence: number }) {
  const pct = Math.round(confidence * 100);
  const colour =
    pct >= 65 ? "bg-green-500" : pct >= 40 ? "bg-amber-400" : "bg-gray-400";
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

function DayCard({ day }: { day: DayPlan }) {
  return (
    <div className="border border-gray-200 rounded-xl p-5 bg-white hover:shadow-sm transition-shadow">
      <h3 className="font-semibold text-gray-900 mb-1">{day.title}</h3>
      <p className="text-xs text-blue-600 font-medium mb-3">{day.theme}</p>
      <div className="space-y-2 text-sm text-gray-700">
        <div className="flex gap-2">
          <span className="w-24 shrink-0 text-gray-400 font-medium">Morning</span>
          <span>{day.morning}</span>
        </div>
        <div className="flex gap-2">
          <span className="w-24 shrink-0 text-gray-400 font-medium">Afternoon</span>
          <span>{day.afternoon}</span>
        </div>
        <div className="flex gap-2">
          <span className="w-24 shrink-0 text-gray-400 font-medium">Evening</span>
          <span>{day.evening}</span>
        </div>
      </div>
      <div className="mt-3 pt-3 border-t border-gray-100 flex items-center justify-between text-xs text-gray-500">
        <span>{day.accommodation}</span>
        <span className="font-medium text-gray-700">~${day.estimated_daily_cost_usd}/day</span>
      </div>
      {day.notes && (
        <p className="mt-2 text-xs text-amber-700 bg-amber-50 rounded px-2 py-1">{day.notes}</p>
      )}
    </div>
  );
}

function BudgetCard({ budget }: { budget: BudgetBreakdown }) {
  const rows = [
    { label: "Flights", value: budget.flights_usd },
    { label: "Accommodation", value: budget.accommodation_usd },
    { label: "Food", value: budget.food_usd },
    { label: "Activities", value: budget.activities_usd },
    { label: "Miscellaneous", value: budget.miscellaneous_usd },
  ];
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-6">
      <h2 className="text-lg font-semibold text-gray-900 mb-4">Budget Estimate</h2>
      <table className="w-full text-sm">
        <tbody>
          {rows.map((r) => (
            <tr key={r.label} className="border-b border-gray-100 last:border-0">
              <td className="py-2 text-gray-600">{r.label}</td>
              <td className="py-2 text-right font-medium text-gray-900">
                ${r.value.toLocaleString()}
              </td>
            </tr>
          ))}
        </tbody>
        <tfoot>
          <tr>
            <td className="pt-3 font-bold text-gray-900">Total (estimate)</td>
            <td className="pt-3 text-right font-bold text-blue-700">
              ${budget.total_estimate_usd.toLocaleString()}
            </td>
          </tr>
        </tfoot>
      </table>
      <p className="mt-3 text-xs text-gray-500">
        Range: ${budget.total_range_usd.low.toLocaleString()} –{" "}
        ${budget.total_range_usd.high.toLocaleString()}
      </p>
      <p className="mt-1 text-xs text-gray-400">{budget.basis}</p>
      <ul className="mt-2 space-y-0.5">
        {budget.notes.map((n, i) => (
          <li key={i} className="text-xs text-gray-400">• {n}</li>
        ))}
      </ul>
    </div>
  );
}

function RiskCard({ risk }: { risk: TripRisk }) {
  const severityColour: Record<string, string> = {
    low: "border-l-green-400 bg-green-50",
    medium: "border-l-amber-400 bg-amber-50",
    high: "border-l-red-400 bg-red-50",
  };
  const textColour: Record<string, string> = {
    low: "text-green-800",
    medium: "text-amber-800",
    high: "text-red-800",
  };
  return (
    <div
      className={`border-l-4 rounded-r-lg px-4 py-3 ${severityColour[risk.severity] ?? "border-l-gray-300 bg-gray-50"}`}
    >
      <div className={`text-xs font-semibold uppercase tracking-wide mb-1 ${textColour[risk.severity] ?? "text-gray-700"}`}>
        {risk.type} · {risk.severity}
      </div>
      <p className="text-sm text-gray-800 mb-1">{risk.description}</p>
      <p className="text-xs text-gray-600">Mitigation: {risk.mitigation}</p>
    </div>
  );
}

// ------------------------------------------------------------------
// Page
// ------------------------------------------------------------------

export default async function TripPlanPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  let trip: TripPlan;
  try {
    trip = await getTripPlan(id);
  } catch {
    notFound();
  }

  const budget = trip.estimated_budget_breakdown as BudgetBreakdown;

  return (
    <main className="min-h-screen bg-gray-50 py-10 px-4">
      <div className="max-w-4xl mx-auto space-y-8">

        {/* Header */}
        <div className="bg-white rounded-2xl shadow p-8">
          <div className="flex items-start justify-between gap-4 flex-wrap">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">{trip.title}</h1>
              <p className="text-gray-500 mt-1 text-sm">{trip.trip_summary}</p>
            </div>
            <StatusBadge status={trip.status} />
          </div>

          <div className="mt-6 grid grid-cols-2 gap-4 sm:grid-cols-4 text-sm">
            <div>
              <p className="text-gray-400 text-xs mb-0.5">From</p>
              <p className="font-medium text-gray-900">{trip.origin}</p>
            </div>
            <div>
              <p className="text-gray-400 text-xs mb-0.5">To</p>
              <p className="font-medium text-gray-900">{trip.destination}</p>
            </div>
            <div>
              <p className="text-gray-400 text-xs mb-0.5">Duration</p>
              <p className="font-medium text-gray-900">{trip.duration_days} days</p>
            </div>
            <div>
              <p className="text-gray-400 text-xs mb-0.5">Style</p>
              <p className="font-medium text-gray-900 capitalize">{trip.travel_style}</p>
            </div>
          </div>

          <div className="mt-6">
            <ConfidenceBar confidence={trip.confidence} />
          </div>
        </div>

        {/* Missing info */}
        {trip.missing_information.length > 0 && (
          <div className="rounded-xl bg-amber-50 border border-amber-200 p-6">
            <h2 className="font-semibold text-amber-800 mb-2">Missing Information</h2>
            <ul className="space-y-1">
              {trip.missing_information.map((m, i) => (
                <li key={i} className="text-sm text-amber-700">• {m}</li>
              ))}
            </ul>
          </div>
        )}

        {/* Recommended destinations */}
        {trip.recommended_destinations.length > 0 && (
          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Suggested Destinations</h2>
            <div className="grid gap-3 sm:grid-cols-3">
              {trip.recommended_destinations.map((d, i) => (
                <div key={i} className="rounded-lg bg-blue-50 border border-blue-100 p-4">
                  <p className="font-semibold text-blue-900">{d.city}</p>
                  <p className="text-xs text-blue-700">{d.country}</p>
                  <p className="text-xs text-gray-600 mt-1">{d.reason}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Itinerary */}
        <div>
          <h2 className="text-lg font-semibold text-gray-900 mb-4">
            Day-by-Day Itinerary
          </h2>
          <div className="grid gap-4">
            {trip.draft_itinerary.map((day) => (
              <DayCard key={day.day} day={day} />
            ))}
          </div>
        </div>

        {/* Budget */}
        <BudgetCard budget={budget} />

        {/* Risks */}
        <div>
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Risk Assessment</h2>
          <div className="space-y-3">
            {trip.risks.map((risk, i) => (
              <RiskCard key={i} risk={risk} />
            ))}
          </div>
        </div>

        {/* Assumptions */}
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-3">Planning Assumptions</h2>
          <ul className="space-y-1">
            {trip.assumptions.map((a, i) => (
              <li key={i} className="text-sm text-gray-600">• {a}</li>
            ))}
          </ul>
        </div>

        {/* Next actions */}
        {trip.next_actions.length > 0 && (
          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-3">Recommended Next Steps</h2>
            <ol className="space-y-1">
              {trip.next_actions.map((a, i) => (
                <li key={i} className="text-sm text-gray-700">
                  <span className="font-medium text-blue-600 mr-1">{i + 1}.</span>
                  {a}
                </li>
              ))}
            </ol>
          </div>
        )}

        {/* Agents */}
        {trip.recommended_agents.length > 0 && (
          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-3">Suitable Agents</h2>
            <div className="flex flex-wrap gap-2">
              {trip.recommended_agents.map((a) => (
                <span
                  key={a}
                  className="px-3 py-1 rounded-full bg-gray-100 text-gray-700 text-xs font-medium"
                >
                  {a}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>
    </main>
  );
}

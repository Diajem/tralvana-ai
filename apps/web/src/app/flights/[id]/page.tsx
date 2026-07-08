import { getFlightOption } from "@/lib/api";
import type { FlightOption } from "@/types/flight";
import { notFound } from "next/navigation";

const RECOMMENDATION_LABELS: Record<string, { label: string; className: string }> = {
  BEST_OVERALL: { label: "Best Overall", className: "bg-blue-600 text-white" },
  LOWEST_PRICE: { label: "Lowest Price", className: "bg-emerald-600 text-white" },
  SHORTEST_DURATION: { label: "Shortest Duration", className: "bg-indigo-600 text-white" },
  BEST_FOR_FAMILY: { label: "Best for Family", className: "bg-amber-500 text-white" },
  BEST_FOR_BUSINESS: { label: "Best for Business", className: "bg-slate-700 text-white" },
  BEST_FOR_COMFORT: { label: "Best for Comfort", className: "bg-purple-600 text-white" },
  BEST_FOR_BUDGET: { label: "Best for Budget", className: "bg-teal-600 text-white" },
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

export default async function FlightOptionPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  let flight: FlightOption;
  try {
    flight = await getFlightOption(id);
  } catch {
    notFound();
  }

  const badge = RECOMMENDATION_LABELS[flight.recommendation_type] ?? {
    label: flight.recommendation_type,
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
                {flight.airline} {flight.flight_number}
              </h1>
              <p className="text-gray-500 mt-1 text-sm">
                {flight.origin} → {flight.destination}
              </p>
            </div>
            <span className={`px-2.5 py-1 rounded-full text-xs font-medium ${badge.className}`}>
              {badge.label}
            </span>
          </div>

          <div className="mt-6 grid grid-cols-2 gap-4 sm:grid-cols-4 text-sm">
            <div>
              <p className="text-gray-400 text-xs mb-0.5">Departs</p>
              <p className="font-medium text-gray-900">{flight.departure_time} · {flight.departure_date}</p>
            </div>
            <div>
              <p className="text-gray-400 text-xs mb-0.5">Arrives</p>
              <p className="font-medium text-gray-900">{flight.arrival_time}</p>
            </div>
            <div>
              <p className="text-gray-400 text-xs mb-0.5">Duration</p>
              <p className="font-medium text-gray-900">{flight.total_duration}</p>
            </div>
            <div>
              <p className="text-gray-400 text-xs mb-0.5">Cabin</p>
              <p className="font-medium text-gray-900 capitalize">{flight.cabin_class}</p>
            </div>
          </div>

          <div className="mt-6">
            <MatchScoreBar score={flight.match_score} />
          </div>
        </div>

        {/* Route details */}
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Flight Details</h2>
          <table className="w-full text-sm">
            <tbody>
              <tr className="border-b border-gray-100">
                <td className="py-2 text-gray-600">Stops</td>
                <td className="py-2 text-right font-medium text-gray-900">
                  {flight.stops === 0 ? "Direct" : `${flight.stops} stop${flight.stops > 1 ? "s" : ""}`}
                </td>
              </tr>
              {flight.stops > 0 && (
                <tr className="border-b border-gray-100">
                  <td className="py-2 text-gray-600">Layover</td>
                  <td className="py-2 text-right font-medium text-gray-900">{flight.layover_duration}</td>
                </tr>
              )}
              <tr className="border-b border-gray-100">
                <td className="py-2 text-gray-600">Price</td>
                <td className="py-2 text-right font-medium text-gray-900">
                  {flight.currency} {flight.estimated_price.toLocaleString()}
                </td>
              </tr>
              <tr className="border-b border-gray-100">
                <td className="py-2 text-gray-600">Baggage</td>
                <td className="py-2 text-right font-medium text-gray-900">
                  {flight.baggage_included ? "Included" : "Not included"}
                </td>
              </tr>
              <tr className="border-b border-gray-100">
                <td className="py-2 text-gray-600">Refundability</td>
                <td className="py-2 text-right font-medium text-gray-900 capitalize">
                  {flight.refundability.replace(/_/g, " ")}
                </td>
              </tr>
              <tr>
                <td className="py-2 text-gray-600">Flexibility</td>
                <td className="py-2 text-right font-medium text-gray-900 capitalize">{flight.flexibility}</td>
              </tr>
            </tbody>
          </table>
        </div>

        {/* Explanation */}
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-3">Why This Match Score</h2>
          <p className="text-sm text-gray-700">{flight.reasoning}</p>
        </div>

        {/* Risks */}
        {flight.risks.length > 0 && (
          <div>
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Risks</h2>
            <div className="space-y-3">
              {flight.risks.map((risk, i) => (
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
        {flight.assumptions.length > 0 && (
          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-3">Assumptions</h2>
            <ul className="space-y-1">
              {flight.assumptions.map((a, i) => (
                <li key={i} className="text-sm text-gray-600">• {a}</li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </main>
  );
}

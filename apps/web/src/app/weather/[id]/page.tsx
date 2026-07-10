import { getWeatherAssessment } from "@/lib/api";
import type { WeatherAssessment } from "@/types/weather";
import { notFound } from "next/navigation";

const MONTHS = [
  "January", "February", "March", "April", "May", "June",
  "July", "August", "September", "October", "November", "December",
];

const STATUS_LABELS: Record<string, { label: string; className: string }> = {
  EXCELLENT: { label: "Excellent", className: "bg-green-600 text-white" },
  GOOD: { label: "Good", className: "bg-emerald-500 text-white" },
  ACCEPTABLE: { label: "Acceptable", className: "bg-amber-500 text-white" },
  CHALLENGING: { label: "Challenging", className: "bg-orange-600 text-white" },
  NOT_RECOMMENDED: { label: "Not Recommended", className: "bg-red-600 text-white" },
};

const RISK_LEVEL_CLASS: Record<string, string> = {
  LOW: "text-green-700 bg-green-50",
  MODERATE: "text-amber-700 bg-amber-50",
  HIGH: "text-orange-700 bg-orange-50",
  SEVERE: "text-red-700 bg-red-50",
};

function ScoreBar({ label, score }: { label: string; score: number }) {
  const pct = Math.round(score * 100);
  const colour = pct >= 70 ? "bg-green-500" : pct >= 45 ? "bg-amber-400" : "bg-red-400";
  return (
    <div>
      <div className="flex justify-between text-xs text-gray-500 mb-1">
        <span>{label}</span>
        <span>{pct}%</span>
      </div>
      <div className="h-2 w-full rounded-full bg-gray-200 overflow-hidden">
        <div className={`h-full ${colour} rounded-full`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}

function RiskLevelBadge({ label, level }: { label: string; level: string }) {
  return (
    <div className={`rounded-lg px-3 py-2 ${RISK_LEVEL_CLASS[level] ?? "text-gray-700 bg-gray-50"}`}>
      <p className="text-xs font-medium">{label}</p>
      <p className="text-sm font-semibold">{level}</p>
    </div>
  );
}

export default async function WeatherAssessmentPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  let assessment: WeatherAssessment;
  try {
    assessment = await getWeatherAssessment(id);
  } catch {
    notFound();
  }

  const badge = STATUS_LABELS[assessment.weather_status] ?? {
    label: assessment.weather_status,
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
                {assessment.destination} — {MONTHS[assessment.month_of_travel - 1]}
              </h1>
              <p className="text-gray-500 mt-1 text-sm">{assessment.season.replace(/_/g, " ")}</p>
            </div>
            <span className={`px-2.5 py-1 rounded-full text-xs font-medium ${badge.className}`}>
              {badge.label}
            </span>
          </div>

          <p className="mt-4 text-sm text-gray-700">{assessment.weather_summary}</p>

          <div className="mt-6 space-y-3">
            <ScoreBar label="Weather Suitability" score={assessment.weather_suitability_score} />
            <ScoreBar label="Confidence" score={assessment.confidence} />
          </div>
        </div>

        {/* Climate details */}
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Climate Details</h2>
          <table className="w-full text-sm">
            <tbody>
              <tr className="border-b border-gray-100">
                <td className="py-2 text-gray-600">Average Temperature</td>
                <td className="py-2 text-right font-medium text-gray-900">
                  {assessment.average_temperature !== null ? `${assessment.average_temperature}°C` : "Unknown"}
                </td>
              </tr>
              <tr className="border-b border-gray-100">
                <td className="py-2 text-gray-600">Rainfall</td>
                <td className="py-2 text-right font-medium text-gray-900">{assessment.rainfall_level}</td>
              </tr>
              <tr className="border-b border-gray-100">
                <td className="py-2 text-gray-600">Humidity</td>
                <td className="py-2 text-right font-medium text-gray-900">{assessment.humidity_level}</td>
              </tr>
              <tr>
                <td className="py-2 text-gray-600">Daylight Hours</td>
                <td className="py-2 text-right font-medium text-gray-900">
                  {assessment.daylight_hours !== null ? `${assessment.daylight_hours}h/day` : "Unknown"}
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        {/* Sub-scores */}
        <div className="bg-white rounded-xl border border-gray-200 p-6 space-y-4">
          <h2 className="text-lg font-semibold text-gray-900 mb-1">Suitability Breakdown</h2>
          <ScoreBar label="Outdoor Activity" score={assessment.outdoor_activity_score} />
          <ScoreBar label="Photography" score={assessment.photography_score} />
          <ScoreBar label="Family Suitability" score={assessment.family_score} />
        </div>

        {/* Explanation */}
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-3">Assessment</h2>
          <p className="text-sm text-gray-700">{assessment.explanation}</p>
          <p className="text-sm text-gray-600 mt-3 italic">{assessment.personal_suitability}</p>
        </div>

        {/* Safety */}
        <div className="bg-white rounded-xl border border-gray-200 p-6 space-y-4">
          <h2 className="text-lg font-semibold text-gray-900 mb-1">Safety</h2>
          <p className="text-sm text-gray-700">{assessment.safety_summary}</p>
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
            <RiskLevelBadge label="Natural Hazard Risk" level={assessment.natural_hazard_risk} />
            <RiskLevelBadge label="Transport Disruption" level={assessment.transport_disruption_risk} />
            <RiskLevelBadge label="Health Risk" level={assessment.health_risk} />
          </div>
        </div>

        {/* Alternative months */}
        {assessment.alternative_months.length > 0 && (
          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-3">Alternative Months</h2>
            <div className="flex flex-wrap gap-2">
              {assessment.alternative_months.map((m) => (
                <span
                  key={m.month}
                  className="px-3 py-1.5 rounded-full bg-emerald-50 text-emerald-700 text-sm font-medium"
                >
                  {m.month_name} — {STATUS_LABELS[m.weather_status]?.label ?? m.weather_status} ({Math.round(m.weather_suitability_score * 100)}%)
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Packing */}
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-3">Packing Recommendations</h2>
          <ul className="space-y-1">
            {assessment.packing_recommendations.map((p, i) => (
              <li key={i} className="text-sm text-gray-700">• {p}</li>
            ))}
          </ul>
        </div>

        {/* Recommendation */}
        <div className="bg-blue-50 border border-blue-200 rounded-xl p-6">
          <h2 className="text-lg font-semibold text-blue-900 mb-2">Recommendation</h2>
          <p className="text-sm text-blue-800">{assessment.recommendation}</p>
        </div>

        {/* Risks */}
        {assessment.risks.length > 0 && (
          <div>
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Risks</h2>
            <div className="space-y-3">
              {assessment.risks.map((risk, i) => (
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
        {assessment.assumptions.length > 0 && (
          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-3">Assumptions</h2>
            <ul className="space-y-1">
              {assessment.assumptions.map((a, i) => (
                <li key={i} className="text-sm text-gray-600">• {a}</li>
              ))}
            </ul>
          </div>
        )}

        <p className="text-xs text-gray-400 text-center">
          This is a travel decision aid, not a weather forecast. Always check an official forecast
          closer to your travel date.
        </p>
      </div>
    </main>
  );
}

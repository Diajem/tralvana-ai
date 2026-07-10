import { getVisaAssessment } from "@/lib/api";
import type { VisaAssessment } from "@/types/visa";
import { notFound } from "next/navigation";

const STATUS_LABELS: Record<string, { label: string; className: string }> = {
  VISA_NOT_REQUIRED: { label: "Visa Not Required", className: "bg-green-600 text-white" },
  VISA_REQUIRED: { label: "Visa Required", className: "bg-red-600 text-white" },
  ETA_REQUIRED: { label: "ETA Required", className: "bg-amber-500 text-white" },
  EVISA_AVAILABLE: { label: "e-Visa Available", className: "bg-blue-600 text-white" },
  CHECK_MANUALLY: { label: "Check Manually", className: "bg-gray-500 text-white" },
  ENTRY_RESTRICTED: { label: "Entry Restricted", className: "bg-red-800 text-white" },
};

function ConfidenceBar({ score }: { score: number }) {
  const pct = Math.round(score * 100);
  const colour = pct >= 70 ? "bg-green-500" : pct >= 45 ? "bg-amber-400" : "bg-red-400";
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

export default async function VisaAssessmentPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  let assessment: VisaAssessment;
  try {
    assessment = await getVisaAssessment(id);
  } catch {
    notFound();
  }

  const badge = STATUS_LABELS[assessment.visa_status] ?? {
    label: assessment.visa_status,
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
                {assessment.nationality} → {assessment.destination_country}
              </h1>
              <p className="text-gray-500 mt-1 text-sm">
                {assessment.travel_purpose.replace(/_/g, " ")} · {assessment.intended_length_of_stay} day(s)
              </p>
            </div>
            <span className={`px-2.5 py-1 rounded-full text-xs font-medium ${badge.className}`}>
              {badge.label}
            </span>
          </div>

          <p className="mt-4 text-sm text-gray-700">
            <span className="font-medium">Visa type:</span> {assessment.visa_type} ·{" "}
            <span className="font-medium">Processing time:</span> {assessment.processing_time}
          </p>

          <div className="mt-6">
            <ConfidenceBar score={assessment.confidence} />
          </div>
        </div>

        {/* Explanation */}
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-3">Assessment</h2>
          <p className="text-sm text-gray-700">{assessment.explanation}</p>
        </div>

        {/* Requirements */}
        <div className="bg-white rounded-xl border border-gray-200 p-6 space-y-4">
          <h2 className="text-lg font-semibold text-gray-900 mb-1">Requirements</h2>
          <div>
            <p className="text-xs font-semibold text-gray-700 mb-1">Entry Requirements</p>
            <ul className="space-y-0.5">
              {assessment.entry_requirements.map((r, i) => (
                <li key={i} className="text-sm text-gray-600">• {r}</li>
              ))}
            </ul>
          </div>
          <div>
            <p className="text-xs font-semibold text-gray-700 mb-1">Supporting Documents</p>
            <ul className="space-y-0.5">
              {assessment.supporting_documents.map((r, i) => (
                <li key={i} className="text-sm text-gray-600">• {r}</li>
              ))}
            </ul>
          </div>
          {assessment.vaccination_requirements.length > 0 && (
            <div>
              <p className="text-xs font-semibold text-gray-700 mb-1">Vaccination Requirements</p>
              <ul className="space-y-0.5">
                {assessment.vaccination_requirements.map((r, i) => (
                  <li key={i} className="text-sm text-gray-600">• {r}</li>
                ))}
              </ul>
            </div>
          )}
          {assessment.transit_countries.length > 0 && (
            <div>
              <p className="text-xs font-semibold text-gray-700 mb-1">Transit Countries</p>
              <p className="text-sm text-gray-600">{assessment.transit_countries.join(", ")}</p>
            </div>
          )}
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
          This is explainable travel-planning intelligence, not legal advice. Always verify with an
          official government source before travelling.
        </p>
      </div>
    </main>
  );
}

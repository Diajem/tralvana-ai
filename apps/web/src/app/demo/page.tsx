"use client";

import { useState } from "react";
import { runJapanDemo, type DemoResponse } from "@/lib/api";

// ------------------------------------------------------------------
// Section components
// ------------------------------------------------------------------

function SectionCard({
  title,
  badge,
  children,
}: {
  title: string;
  badge?: string;
  children: React.ReactNode;
}) {
  return (
    <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-bold text-gray-900">{title}</h2>
        {badge && (
          <span className="text-xs font-medium px-2.5 py-1 rounded-full bg-blue-100 text-blue-800">
            {badge}
          </span>
        )}
      </div>
      {children}
    </div>
  );
}

function ConfidenceBadge({ value }: { value: number }) {
  const pct = Math.round(value * 100);
  const colour =
    pct >= 75 ? "bg-green-100 text-green-800" : pct >= 50 ? "bg-amber-100 text-amber-800" : "bg-gray-100 text-gray-700";
  return (
    <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${colour}`}>
      {pct}% confidence
    </span>
  );
}

function TraitBar({ name, value }: { name: string; value: number }) {
  const pct = Math.min(Math.round(value * 100), 100);
  return (
    <div className="flex items-center gap-3">
      <span className="w-36 text-xs text-gray-500 capitalize">{name.replace(/_/g, " ")}</span>
      <div className="flex-1 h-2 rounded-full bg-gray-100 overflow-hidden">
        <div
          className="h-full rounded-full bg-blue-400"
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="w-8 text-right text-xs text-gray-500">{pct}%</span>
    </div>
  );
}

function RiskPill({ risk }: { risk: { type: string; severity: string; description: string; mitigation: string } }) {
  const map: Record<string, string> = {
    low: "border-l-green-400 bg-green-50",
    medium: "border-l-amber-400 bg-amber-50",
    high: "border-l-red-400 bg-red-50",
  };
  return (
    <div className={`border-l-4 rounded-r-lg px-4 py-3 ${map[risk.severity] ?? "border-l-gray-300 bg-gray-50"}`}>
      <p className="text-xs font-semibold uppercase text-gray-500 mb-0.5">{risk.type} · {risk.severity}</p>
      <p className="text-sm text-gray-800 mb-1">{risk.description}</p>
      <p className="text-xs text-gray-500">Mitigation: {risk.mitigation}</p>
    </div>
  );
}

// ------------------------------------------------------------------
// Main demo page
// ------------------------------------------------------------------

export default function DemoPage() {
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<DemoResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleRun = async () => {
    setLoading(true);
    setError(null);
    setData(null);
    try {
      const result = await runJapanDemo();
      setData(result);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Demo failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50 py-12 px-4">
      <div className="max-w-5xl mx-auto space-y-8">

        {/* Hero */}
        <div className="text-center space-y-4">
          <div className="inline-flex items-center gap-2 bg-blue-100 text-blue-800 text-xs font-semibold px-3 py-1 rounded-full">
            TravelOS · End-to-End Demo
          </div>
          <h1 className="text-4xl font-extrabold text-gray-900">
            Japan Football &amp; Food Tour
          </h1>
          <p className="text-gray-500 max-w-2xl mx-auto text-sm leading-relaxed">
            Runs the complete TravelOS pipeline in one call: Traveller Profile → DNA Inference →
            Goal → Goal Reasoning → Knowledge Graph → Conversation → Trip Planning.
          </p>
          <button
            onClick={handleRun}
            disabled={loading}
            className="inline-flex items-center gap-2 px-8 py-3 rounded-xl bg-blue-600 text-white font-semibold text-sm
              hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-md hover:shadow-lg"
          >
            {loading ? (
              <>
                <svg className="animate-spin w-4 h-4" viewBox="0 0 24 24" fill="none">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"/>
                </svg>
                Running pipeline...
              </>
            ) : (
              "Run Japan Football & Food Demo"
            )}
          </button>
        </div>

        {/* Error */}
        {error && (
          <div className="rounded-xl bg-red-50 border border-red-200 p-4 text-red-700 text-sm">
            {error}
          </div>
        )}

        {/* Results */}
        {data && (
          <div className="space-y-6">

            {/* Pipeline summary */}
            <SectionCard title="Pipeline Summary" badge={`${data.pipeline_summary.stages_completed} stages`}>
              <div className="flex items-center gap-3 mb-4">
                <ConfidenceBadge value={data.pipeline_summary.overall_confidence} />
                <span className="text-xs text-gray-400">Generated {new Date(data.generated_at).toLocaleTimeString()}</span>
              </div>
              <div className="flex flex-wrap gap-2 mb-4">
                {(data.pipeline_summary.pipeline as string[]).map((stage: string, i: number) => (
                  <div key={i} className="flex items-center gap-1.5 text-xs text-gray-700 bg-gray-50 border border-gray-200 px-3 py-1 rounded-full">
                    <span className="w-4 h-4 rounded-full bg-green-500 text-white flex items-center justify-center text-[10px] font-bold">{i + 1}</span>
                    {stage}
                  </div>
                ))}
              </div>
              <div className="text-xs text-gray-400">
                Data sources: {(data.pipeline_summary.data_sources as string[]).join(" · ")}
              </div>
            </SectionCard>

            {/* Traveller */}
            <SectionCard title="Traveller Profile" badge="Stage 1">
              <p className="text-sm text-gray-700 mb-3">{data.traveller.summary}</p>
              <div className="flex flex-wrap gap-2">
                {(data.traveller.travel_interests as string[]).map((i: string) => (
                  <span key={i} className="px-2 py-0.5 bg-indigo-50 text-indigo-700 text-xs font-medium rounded-full">
                    {i}
                  </span>
                ))}
              </div>
            </SectionCard>

            {/* DNA */}
            <SectionCard title="Traveller DNA" badge="Stage 2">
              <div className="flex items-center gap-3 mb-3">
                <span className="text-xl font-bold text-blue-700">{data.dna.primary_type}</span>
                <ConfidenceBadge value={data.dna.confidence} />
              </div>
              {data.dna.description && (
                <p className="text-sm text-gray-600 mb-4">{data.dna.description}</p>
              )}
              <div className="flex flex-wrap gap-1.5 mb-5">
                {(data.dna.secondary_types as string[]).map((t: string) => (
                  <span key={t} className="px-2 py-0.5 bg-blue-50 text-blue-700 text-xs rounded-full">
                    {t}
                  </span>
                ))}
              </div>
              <div className="space-y-2">
                {Object.entries(data.dna.top_traits as Record<string, number>).map(([name, val]) => (
                  <TraitBar key={name} name={name} value={val} />
                ))}
              </div>
            </SectionCard>

            {/* Goal */}
            <SectionCard title="Travel Goal" badge="Stage 3">
              <div className="flex items-center gap-3 mb-2">
                <h3 className="font-semibold text-gray-900">{data.goal.title}</h3>
                <span className="text-xs px-2 py-0.5 bg-amber-100 text-amber-800 rounded-full">
                  {data.goal.status}
                </span>
              </div>
              <p className="text-sm text-gray-600 mb-4">{data.goal.goal_summary}</p>
              <div className="mb-3">
                <div className="flex justify-between text-xs text-gray-500 mb-1">
                  <span>Goal Readiness</span>
                  <span>{Math.round(data.goal.planning_readiness_score * 100)}%</span>
                </div>
                <div className="h-2 w-full rounded-full bg-gray-200">
                  <div
                    className="h-full rounded-full bg-green-500"
                    style={{ width: `${Math.round(data.goal.planning_readiness_score * 100)}%` }}
                  />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-3 text-xs text-gray-600 mt-3">
                <div><span className="text-gray-400">Duration:</span> {data.goal.duration_days} days</div>
                <div><span className="text-gray-400">Travellers:</span> {data.goal.travellers?.adults} adults</div>
                <div><span className="text-gray-400">Budget:</span> {data.goal.budget?.currency} {data.goal.budget?.min_usd}–{data.goal.budget?.max_usd}</div>
                <div><span className="text-gray-400">Destination:</span> {data.goal.destination}</div>
              </div>
              {(data.goal.success_criteria as string[]).length > 0 && (
                <div className="mt-3 pt-3 border-t border-gray-100">
                  <p className="text-xs font-medium text-gray-500 mb-1">Success Criteria</p>
                  <ul className="space-y-0.5">
                    {(data.goal.success_criteria as string[]).map((c: string, i: number) => (
                      <li key={i} className="text-xs text-gray-700">• {c}</li>
                    ))}
                  </ul>
                </div>
              )}
            </SectionCard>

            {/* Conversation */}
            <SectionCard title="Conversation Engine" badge="Stage 5">
              <div className="bg-gray-50 rounded-xl p-4 mb-4">
                <p className="text-xs text-gray-400 mb-1">User message</p>
                <p className="text-sm text-gray-800 italic">&ldquo;{data.conversation.message_sent}&rdquo;</p>
              </div>
              <div className="flex gap-2 mb-3">
                <span className="text-xs px-2 py-0.5 bg-blue-100 text-blue-800 rounded-full font-medium">
                  {data.conversation.intent}
                </span>
                <ConfidenceBadge value={data.conversation.confidence} />
              </div>
              <div className="bg-blue-50 rounded-xl p-4 text-sm text-gray-800">
                {data.conversation.response}
              </div>
              {data.conversation.trip_id && (
                <p className="mt-2 text-xs text-green-700">
                  Trip plan auto-generated — ID: {data.conversation.trip_id}
                </p>
              )}
            </SectionCard>

            {/* Knowledge Graph */}
            <SectionCard title="Knowledge Graph Insights" badge="Stage 4">
              <div className="grid grid-cols-2 gap-3 text-sm mb-5">
                <div>
                  <span className="text-gray-400 text-xs">City</span>
                  <p className="font-semibold">{data.knowledge_insights.destination_city}, {data.knowledge_insights.country}</p>
                </div>
                <div>
                  <span className="text-gray-400 text-xs">Safety Level</span>
                  <p className="font-semibold capitalize">{data.knowledge_insights.safety_level}</p>
                </div>
                <div>
                  <span className="text-gray-400 text-xs">Population</span>
                  <p className="font-semibold">{(data.knowledge_insights.city_population as number)?.toLocaleString()}</p>
                </div>
                <div>
                  <span className="text-gray-400 text-xs">Tags</span>
                  <div className="flex flex-wrap gap-1 mt-0.5">
                    {(data.knowledge_insights.city_tags as string[]).map((t: string) => (
                      <span key={t} className="px-1.5 py-0.5 bg-gray-100 text-gray-600 text-xs rounded">{t}</span>
                    ))}
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                {data.knowledge_insights.airports?.length > 0 && (
                  <div>
                    <p className="text-xs font-semibold text-gray-500 mb-1">Airports</p>
                    {(data.knowledge_insights.airports as {name: string; iata_code: string}[]).map((a) => (
                      <p key={a.iata_code} className="text-xs text-gray-700">{a.name} ({a.iata_code})</p>
                    ))}
                  </div>
                )}
                {data.knowledge_insights.football_clubs?.length > 0 && (
                  <div>
                    <p className="text-xs font-semibold text-gray-500 mb-1">Football Clubs</p>
                    {(data.knowledge_insights.football_clubs as {name: string; league: string}[]).map((c) => (
                      <p key={c.name} className="text-xs text-gray-700">{c.name} · {c.league}</p>
                    ))}
                  </div>
                )}
                {data.knowledge_insights.attractions?.length > 0 && (
                  <div>
                    <p className="text-xs font-semibold text-gray-500 mb-1">Attractions</p>
                    {(data.knowledge_insights.attractions as {name: string; type: string}[]).map((a) => (
                      <p key={a.name} className="text-xs text-gray-700">{a.name} ({a.type})</p>
                    ))}
                  </div>
                )}
                {data.knowledge_insights.events?.length > 0 && (
                  <div>
                    <p className="text-xs font-semibold text-gray-500 mb-1">Events</p>
                    {(data.knowledge_insights.events as {name: string; month: number}[]).map((e) => (
                      <p key={e.name} className="text-xs text-gray-700">{e.name} (Month {e.month})</p>
                    ))}
                  </div>
                )}
                {data.knowledge_insights.weather_records?.length > 0 && (
                  <div className="sm:col-span-2">
                    <p className="text-xs font-semibold text-gray-500 mb-1">Weather</p>
                    <div className="flex flex-wrap gap-2">
                      {(data.knowledge_insights.weather_records as {month: number; avg_temp_c: number; condition: string; season: string}[]).map((w) => (
                        <div key={w.month} className="bg-sky-50 border border-sky-100 rounded-lg px-3 py-2 text-xs">
                          <p className="font-semibold text-sky-800">Month {w.month}</p>
                          <p className="text-gray-600">{w.avg_temp_c}°C · {w.condition}</p>
                          <p className="text-gray-400 capitalize">{w.season}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </SectionCard>

            {/* Itinerary */}
            <SectionCard title="10-Day Draft Itinerary" badge="Stage 6">
              <p className="text-sm text-gray-500 mb-4">{data.trip_plan.trip_summary}</p>
              <div className="flex gap-2 mb-5">
                <ConfidenceBadge value={data.trip_plan.confidence} />
                <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                  data.trip_plan.status === "READY" ? "bg-green-100 text-green-800" :
                  data.trip_plan.status === "DRAFT" ? "bg-yellow-100 text-yellow-800" : "bg-gray-100 text-gray-700"
                }`}>{data.trip_plan.status}</span>
              </div>
              <div className="space-y-3">
                {(data.trip_plan.draft_itinerary as {day: number; title: string; theme: string; morning: string; afternoon: string; evening: string; accommodation: string; estimated_daily_cost_usd: number; notes: string}[]).map((day) => (
                  <div key={day.day} className="border border-gray-200 rounded-xl p-4">
                    <div className="flex items-center justify-between mb-2">
                      <h3 className="font-semibold text-gray-900 text-sm">{day.title}</h3>
                      <span className="text-xs text-gray-400">~${day.estimated_daily_cost_usd}/day</span>
                    </div>
                    <div className="grid grid-cols-3 gap-2 text-xs text-gray-600">
                      <div><span className="text-gray-400 font-medium block">Morning</span>{day.morning}</div>
                      <div><span className="text-gray-400 font-medium block">Afternoon</span>{day.afternoon}</div>
                      <div><span className="text-gray-400 font-medium block">Evening</span>{day.evening}</div>
                    </div>
                    {day.notes && (
                      <p className="mt-2 text-xs text-amber-700 bg-amber-50 rounded px-2 py-1">{day.notes}</p>
                    )}
                  </div>
                ))}
              </div>
            </SectionCard>

            {/* Budget */}
            <SectionCard title="Budget Breakdown" badge="Stage 6">
              {(() => {
                const b = data.trip_plan.estimated_budget_breakdown;
                const rows = [
                  { label: "Flights", value: b.flights_usd },
                  { label: "Accommodation", value: b.accommodation_usd },
                  { label: "Food", value: b.food_usd },
                  { label: "Activities", value: b.activities_usd },
                  { label: "Miscellaneous", value: b.miscellaneous_usd },
                ];
                return (
                  <div>
                    <table className="w-full text-sm mb-4">
                      <tbody>
                        {rows.map((r) => (
                          <tr key={r.label} className="border-b border-gray-100 last:border-0">
                            <td className="py-2 text-gray-600">{r.label}</td>
                            <td className="py-2 text-right font-medium">${(r.value as number).toLocaleString()}</td>
                          </tr>
                        ))}
                      </tbody>
                      <tfoot>
                        <tr>
                          <td className="pt-3 font-bold text-gray-900">Total (2 adults)</td>
                          <td className="pt-3 text-right font-bold text-blue-700">${(b.total_estimate_usd as number).toLocaleString()}</td>
                        </tr>
                      </tfoot>
                    </table>
                    <p className="text-xs text-gray-400">{b.basis as string}</p>
                    <p className="text-xs text-gray-400">Range: ${(b.total_range_usd as {low: number; high: number}).low.toLocaleString()} – ${(b.total_range_usd as {low: number; high: number}).high.toLocaleString()}</p>
                  </div>
                );
              })()}
            </SectionCard>

            {/* Risks */}
            <SectionCard title="Risk Assessment" badge="Stage 6">
              <div className="space-y-3">
                {(data.trip_plan.risks as {type: string; severity: string; description: string; mitigation: string}[]).map((risk, i) => (
                  <RiskPill key={i} risk={risk} />
                ))}
              </div>
            </SectionCard>

            {/* Next actions */}
            <SectionCard title="Recommended Next Steps" badge="Stage 7">
              <ol className="space-y-2">
                {(data.trip_plan.next_actions as string[]).map((a: string, i: number) => (
                  <li key={i} className="flex gap-2 text-sm text-gray-700">
                    <span className="font-bold text-blue-500 shrink-0">{i + 1}.</span>
                    {a}
                  </li>
                ))}
              </ol>
            </SectionCard>

          </div>
        )}
      </div>
    </main>
  );
}

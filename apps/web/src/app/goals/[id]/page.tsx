import Link from "next/link";
import { getGoal } from "@/lib/api";
import type { Goal } from "@/types/goal";

interface Props {
  params: Promise<{ id: string }>;
}

const STATUS_COLORS: Record<string, string> = {
  DRAFT:              "bg-gray-100 text-gray-600",
  ACTIVE:             "bg-blue-50 text-blue-700",
  READY_FOR_PLANNING: "bg-amber-50 text-amber-700",
  PLANNED:            "bg-emerald-50 text-emerald-700",
  ARCHIVED:           "bg-red-50 text-red-500",
};

const GOAL_TYPE_LABELS: Record<string, string> = {
  RELAXATION:       "🌴 Relaxation",
  ADVENTURE:        "🧗 Adventure",
  FOOTBALL_TRAVEL:  "⚽ Football Travel",
  FAMILY_TRIP:      "👨‍👩‍👧 Family Trip",
  BUSINESS_TRAVEL:  "💼 Business Travel",
  FOOD_TOUR:        "🍜 Food Tour",
  PHOTOGRAPHY:      "📷 Photography",
  PILGRIMAGE:       "🕌 Pilgrimage",
  DIASPORA_TRAVEL:  "🌍 Diaspora Travel",
  ROMANTIC_TRIP:    "💑 Romantic Trip",
  GENERAL_TRAVEL:   "✈️ General Travel",
};

function ReadinessBar({ score }: { score: number }) {
  const pct = Math.round(score * 100);
  const color = pct >= 85 ? "bg-emerald-500" : pct >= 50 ? "bg-amber-400" : "bg-gray-300";
  return (
    <div>
      <div className="flex justify-between text-xs text-gray-500 mb-1">
        <span>Planning readiness</span>
        <span className="font-semibold text-gray-900">{pct}%</span>
      </div>
      <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
        <div className={`h-full rounded-full transition-all ${color}`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="bg-white rounded-2xl shadow-sm p-6">
      <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-widest mb-4">{title}</h2>
      {children}
    </div>
  );
}

function Tag({ label }: { label: string }) {
  return (
    <span className="text-xs px-2.5 py-1 rounded-full bg-indigo-50 text-indigo-700 capitalize">
      {label.replace(/_/g, " ")}
    </span>
  );
}

function computeReadiness(goal: Goal): { score: number; missing: string[] } {
  const missing: string[] = [];
  let score = 0;
  if (goal.title) score += 0.15; else missing.push("Title not set");
  if (goal.goal_type !== "GENERAL_TRAVEL") score += 0.10; else missing.push("Goal type is still 'General Travel' — be more specific");
  if (goal.budget.min_usd && goal.budget.max_usd) score += 0.20; else missing.push("Budget range (min/max) not specified");
  if (goal.timeframe.earliest && goal.timeframe.latest) score += 0.20; else missing.push("Travel dates or timeframe not provided");
  if (goal.travellers.adults >= 1) score += 0.10;
  if (goal.interests.length > 0) score += 0.10; else missing.push("No travel interests specified");
  if (goal.success_criteria.length > 0) score += 0.10; else missing.push("Success criteria not defined");
  if (goal.constraints.length > 0) score += 0.05;
  return { score, missing };
}

export default async function GoalPage({ params }: Props) {
  const { id } = await params;

  let goal: Goal | null = null;
  let fetchError: string | null = null;

  try {
    goal = await getGoal(id);
  } catch {
    fetchError = "Could not load goal. Make sure the API is running on port 8000.";
  }

  if (fetchError || !goal) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-gray-50">
        <div className="text-center">
          <p className="text-red-500 text-sm">{fetchError ?? "Goal not found."}</p>
          <Link href="/goals/new" className="mt-4 inline-block text-sm text-indigo-600 hover:underline">
            Create a goal
          </Link>
        </div>
      </main>
    );
  }

  const { score, missing } = computeReadiness(goal);
  const b = goal.budget;
  const t = goal.timeframe;
  const statusColor = STATUS_COLORS[goal.status] ?? "bg-gray-100 text-gray-600";

  const AGENT_MAP: Record<string, string[]> = {
    RELAXATION:       ["FlightAgent", "HotelAgent", "ExperienceAgent"],
    ADVENTURE:        ["FlightAgent", "HotelAgent", "ExperienceAgent", "VisaAgent"],
    FOOTBALL_TRAVEL:  ["FlightAgent", "HotelAgent", "ExperienceAgent"],
    FAMILY_TRIP:      ["FlightAgent", "HotelAgent", "ExperienceAgent"],
    BUSINESS_TRAVEL:  ["FlightAgent", "HotelAgent"],
    FOOD_TOUR:        ["FlightAgent", "HotelAgent", "ExperienceAgent"],
    PHOTOGRAPHY:      ["FlightAgent", "HotelAgent", "ExperienceAgent"],
    PILGRIMAGE:       ["FlightAgent", "HotelAgent", "VisaAgent", "ExperienceAgent"],
    DIASPORA_TRAVEL:  ["FlightAgent", "HotelAgent", "VisaAgent", "ExperienceAgent"],
    ROMANTIC_TRIP:    ["FlightAgent", "HotelAgent", "ExperienceAgent"],
    GENERAL_TRAVEL:   ["FlightAgent", "HotelAgent"],
  };
  const agents = AGENT_MAP[goal.goal_type] ?? ["FlightAgent", "HotelAgent"];

  return (
    <main className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-2xl mx-auto space-y-4">

        {/* Header */}
        <div className="bg-white rounded-2xl shadow-sm p-8">
          <div className="flex items-start justify-between gap-4">
            <div>
              <p className="text-xs text-gray-400 font-mono mb-1">{goal.goal_id}</p>
              <h1 className="text-2xl font-bold text-gray-900">{goal.title}</h1>
              <p className="text-gray-500 text-sm mt-1">
                {GOAL_TYPE_LABELS[goal.goal_type] ?? goal.goal_type}
              </p>
            </div>
            <span className={`shrink-0 text-xs px-2.5 py-1 rounded-full font-medium ${statusColor}`}>
              {goal.status.replace(/_/g, " ")}
            </span>
          </div>
          <div className="mt-6">
            <ReadinessBar score={score} />
          </div>
        </div>

        {/* Missing information */}
        {missing.length > 0 && (
          <div className="bg-amber-50 border border-amber-200 rounded-2xl p-6">
            <h2 className="text-xs font-semibold text-amber-700 uppercase tracking-widest mb-3">
              Missing information
            </h2>
            <ul className="space-y-1.5">
              {missing.map((item) => (
                <li key={item} className="flex items-start gap-2 text-sm text-amber-800">
                  <span className="mt-0.5">⚠️</span>
                  <span>{item}</span>
                </li>
              ))}
            </ul>
            <Link
              href="/goals/new"
              className="mt-4 inline-block text-xs text-amber-700 font-medium hover:underline"
            >
              Edit goal →
            </Link>
          </div>
        )}

        {/* Budget */}
        <Section title="Budget">
          {b.min_usd && b.max_usd ? (
            <p className="text-2xl font-bold text-gray-900">
              ${b.min_usd.toLocaleString()}
              <span className="text-gray-400 font-normal"> – </span>
              ${b.max_usd.toLocaleString()}
              <span className="text-sm font-medium text-gray-400 ml-1">{b.currency}</span>
            </p>
          ) : (
            <p className="text-sm text-gray-400 italic">Not specified</p>
          )}
        </Section>

        {/* Timeframe */}
        <Section title="Timeframe">
          {t.earliest || t.latest || t.duration_days ? (
            <div className="flex flex-wrap gap-6 text-sm">
              {t.earliest && (
                <div>
                  <p className="text-gray-400 text-xs mb-1">Earliest</p>
                  <p className="font-semibold text-gray-900">
                    {new Date(t.earliest).toLocaleDateString("en-GB", { dateStyle: "medium" })}
                  </p>
                </div>
              )}
              {t.latest && (
                <div>
                  <p className="text-gray-400 text-xs mb-1">Latest</p>
                  <p className="font-semibold text-gray-900">
                    {new Date(t.latest).toLocaleDateString("en-GB", { dateStyle: "medium" })}
                  </p>
                </div>
              )}
              {t.duration_days && (
                <div>
                  <p className="text-gray-400 text-xs mb-1">Duration</p>
                  <p className="font-semibold text-gray-900">{t.duration_days} days</p>
                </div>
              )}
            </div>
          ) : (
            <p className="text-sm text-gray-400 italic">Not specified</p>
          )}
        </Section>

        {/* Travellers */}
        <Section title="Travellers">
          <div className="flex gap-6 text-sm">
            <div>
              <p className="text-gray-400 text-xs mb-1">Adults</p>
              <p className="font-semibold text-gray-900">{goal.travellers.adults}</p>
            </div>
            {goal.travellers.children > 0 && (
              <div>
                <p className="text-gray-400 text-xs mb-1">Children</p>
                <p className="font-semibold text-gray-900">{goal.travellers.children}</p>
              </div>
            )}
            {goal.travellers.infants > 0 && (
              <div>
                <p className="text-gray-400 text-xs mb-1">Infants</p>
                <p className="font-semibold text-gray-900">{goal.travellers.infants}</p>
              </div>
            )}
          </div>
        </Section>

        {/* Interests */}
        {goal.interests.length > 0 && (
          <Section title="Interests">
            <div className="flex flex-wrap gap-1.5">
              {goal.interests.map((i) => <Tag key={i} label={i} />)}
            </div>
          </Section>
        )}

        {/* Success criteria */}
        {goal.success_criteria.length > 0 && (
          <Section title="Success criteria">
            <ul className="space-y-1.5">
              {goal.success_criteria.map((c) => (
                <li key={c} className="flex items-start gap-2 text-sm text-gray-700">
                  <span className="text-emerald-500 mt-0.5">✓</span>
                  <span>{c}</span>
                </li>
              ))}
            </ul>
          </Section>
        )}

        {/* Constraints */}
        {goal.constraints.length > 0 && (
          <Section title="Constraints">
            <ul className="space-y-1.5">
              {goal.constraints.map((c) => (
                <li key={c} className="flex items-start gap-2 text-sm text-gray-700">
                  <span className="text-amber-500 mt-0.5">•</span>
                  <span>{c}</span>
                </li>
              ))}
            </ul>
          </Section>
        )}

        {/* Suitable agents */}
        <Section title="Planning agents">
          <p className="text-xs text-gray-400 mb-3">
            These AI agents will be activated when planning begins.
          </p>
          <div className="flex flex-wrap gap-2">
            {agents.map((a) => (
              <span
                key={a}
                className="text-xs px-2.5 py-1 rounded-full bg-gray-100 text-gray-700 font-medium"
              >
                {a}
              </span>
            ))}
          </div>
        </Section>

        {/* Footer */}
        <div className="flex items-center justify-between px-1 text-xs text-gray-400">
          <span>
            Created{" "}
            {new Date(goal.created_at).toLocaleDateString("en-GB", { dateStyle: "long" })}
          </span>
          <Link href="/goals/new" className="text-indigo-600 hover:underline">
            New goal
          </Link>
        </div>
      </div>
    </main>
  );
}

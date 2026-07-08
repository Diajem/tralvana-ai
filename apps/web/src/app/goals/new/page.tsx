"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { createGoal } from "@/lib/api";
import type { GoalType } from "@/types/goal";

const GOAL_TYPES: { value: GoalType; label: string; emoji: string }[] = [
  { value: "RELAXATION",      label: "Relaxation",       emoji: "🌴" },
  { value: "ADVENTURE",       label: "Adventure",        emoji: "🧗" },
  { value: "FOOTBALL_TRAVEL", label: "Football Travel",  emoji: "⚽" },
  { value: "FAMILY_TRIP",     label: "Family Trip",      emoji: "👨‍👩‍👧" },
  { value: "BUSINESS_TRAVEL", label: "Business Travel",  emoji: "💼" },
  { value: "FOOD_TOUR",       label: "Food Tour",        emoji: "🍜" },
  { value: "PHOTOGRAPHY",     label: "Photography",      emoji: "📷" },
  { value: "PILGRIMAGE",      label: "Pilgrimage",       emoji: "🕌" },
  { value: "DIASPORA_TRAVEL", label: "Diaspora Travel",  emoji: "🌍" },
  { value: "ROMANTIC_TRIP",   label: "Romantic Trip",    emoji: "💑" },
  { value: "GENERAL_TRAVEL",  label: "General Travel",   emoji: "✈️" },
];

const INTERESTS = [
  "beach", "city", "adventure", "culture", "food_drink",
  "wellness", "sport", "nature", "luxury", "business",
  "history", "religious", "heritage", "photography",
];

export default function NewGoalPage() {
  const router = useRouter();
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [title, setTitle] = useState("");
  const [travellerId, setTravellerId] = useState("");
  const [goalType, setGoalType] = useState<GoalType>("GENERAL_TRAVEL");
  const [minBudget, setMinBudget] = useState("");
  const [maxBudget, setMaxBudget] = useState("");
  const [earliest, setEarliest] = useState("");
  const [latest, setLatest] = useState("");
  const [durationDays, setDurationDays] = useState("");
  const [adults, setAdults] = useState("1");
  const [children, setChildren] = useState("0");
  const [interests, setInterests] = useState<string[]>([]);
  const [constraints, setConstraints] = useState("");
  const [successCriteria, setSuccessCriteria] = useState("");

  function toggleInterest(interest: string) {
    setInterests((prev) =>
      prev.includes(interest) ? prev.filter((i) => i !== interest) : [...prev, interest]
    );
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!travellerId.trim()) {
      setError("Traveller ID is required.");
      return;
    }
    setSubmitting(true);
    setError(null);

    try {
      const goal = await createGoal({
        traveller_id: travellerId.trim(),
        title: title.trim(),
        goal_type: goalType,
        priority: 3,
        budget: {
          min_usd: minBudget ? parseInt(minBudget, 10) : null,
          max_usd: maxBudget ? parseInt(maxBudget, 10) : null,
          currency: "USD",
        },
        timeframe: {
          earliest: earliest || null,
          latest: latest || null,
          duration_days: durationDays ? parseInt(durationDays, 10) : null,
          flexible: true,
        },
        travellers: {
          adults: parseInt(adults, 10) || 1,
          children: parseInt(children, 10) || 0,
          infants: 0,
        },
        interests,
        constraints: constraints ? constraints.split("\n").map((s) => s.trim()).filter(Boolean) : [],
        success_criteria: successCriteria
          ? successCriteria.split("\n").map((s) => s.trim()).filter(Boolean)
          : [],
        flexibility: { dates: true, duration: true, budget: false },
      });
      router.push(`/goals/${goal.goal_id}`);
    } catch {
      setError("Failed to create goal. Make sure the API is running on port 8000.");
      setSubmitting(false);
    }
  }

  return (
    <main className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-2xl mx-auto">
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-gray-900">New Travel Goal</h1>
          <p className="text-gray-500 text-sm mt-1">
            Tell us what you want to achieve — we&apos;ll help you plan around it.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-5">
          {/* Traveller ID */}
          <div className="bg-white rounded-2xl shadow-sm p-6 space-y-4">
            <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-widest">
              Who is this for?
            </h2>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Traveller ID
              </label>
              <input
                type="text"
                required
                placeholder="Paste your traveller ID from your profile"
                value={travellerId}
                onChange={(e) => setTravellerId(e.target.value)}
                className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Goal title
              </label>
              <input
                type="text"
                required
                placeholder="e.g. Summer holiday in Barcelona"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>
          </div>

          {/* Goal type */}
          <div className="bg-white rounded-2xl shadow-sm p-6">
            <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-widest mb-4">
              What kind of trip?
            </h2>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
              {GOAL_TYPES.map(({ value, label, emoji }) => (
                <button
                  key={value}
                  type="button"
                  onClick={() => setGoalType(value)}
                  className={`flex items-center gap-2 px-3 py-2.5 rounded-xl text-sm font-medium border transition-colors ${
                    goalType === value
                      ? "bg-indigo-600 text-white border-indigo-600"
                      : "bg-white text-gray-700 border-gray-200 hover:border-indigo-300"
                  }`}
                >
                  <span>{emoji}</span>
                  <span>{label}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Budget */}
          <div className="bg-white rounded-2xl shadow-sm p-6 space-y-4">
            <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-widest">
              Budget (USD)
            </h2>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-xs text-gray-500 mb-1">Minimum</label>
                <input
                  type="number"
                  min={0}
                  placeholder="500"
                  value={minBudget}
                  onChange={(e) => setMinBudget(e.target.value)}
                  className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>
              <div>
                <label className="block text-xs text-gray-500 mb-1">Maximum</label>
                <input
                  type="number"
                  min={0}
                  placeholder="3000"
                  value={maxBudget}
                  onChange={(e) => setMaxBudget(e.target.value)}
                  className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>
            </div>
          </div>

          {/* Timeframe */}
          <div className="bg-white rounded-2xl shadow-sm p-6 space-y-4">
            <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-widest">
              Timeframe
            </h2>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-xs text-gray-500 mb-1">Earliest departure</label>
                <input
                  type="date"
                  value={earliest}
                  onChange={(e) => setEarliest(e.target.value)}
                  className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>
              <div>
                <label className="block text-xs text-gray-500 mb-1">Latest return</label>
                <input
                  type="date"
                  value={latest}
                  onChange={(e) => setLatest(e.target.value)}
                  className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>
            </div>
            <div>
              <label className="block text-xs text-gray-500 mb-1">Duration (days)</label>
              <input
                type="number"
                min={1}
                max={365}
                placeholder="7"
                value={durationDays}
                onChange={(e) => setDurationDays(e.target.value)}
                className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>
          </div>

          {/* Travellers */}
          <div className="bg-white rounded-2xl shadow-sm p-6 space-y-4">
            <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-widest">
              Travellers
            </h2>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-xs text-gray-500 mb-1">Adults</label>
                <input
                  type="number"
                  min={1}
                  max={20}
                  value={adults}
                  onChange={(e) => setAdults(e.target.value)}
                  className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>
              <div>
                <label className="block text-xs text-gray-500 mb-1">Children</label>
                <input
                  type="number"
                  min={0}
                  max={20}
                  value={children}
                  onChange={(e) => setChildren(e.target.value)}
                  className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>
            </div>
          </div>

          {/* Interests */}
          <div className="bg-white rounded-2xl shadow-sm p-6">
            <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-widest mb-4">
              Interests
            </h2>
            <div className="flex flex-wrap gap-2">
              {INTERESTS.map((interest) => (
                <button
                  key={interest}
                  type="button"
                  onClick={() => toggleInterest(interest)}
                  className={`px-3 py-1.5 rounded-full text-xs font-medium capitalize transition-colors ${
                    interests.includes(interest)
                      ? "bg-indigo-100 text-indigo-700 border border-indigo-300"
                      : "bg-gray-100 text-gray-600 border border-transparent hover:border-gray-300"
                  }`}
                >
                  {interest.replace(/_/g, " ")}
                </button>
              ))}
            </div>
          </div>

          {/* Constraints + Success criteria */}
          <div className="bg-white rounded-2xl shadow-sm p-6 space-y-4">
            <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-widest">
              Details (optional)
            </h2>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Constraints
              </label>
              <textarea
                rows={2}
                placeholder="One constraint per line — e.g. Must be halal-friendly&#10;No budget airlines"
                value={constraints}
                onChange={(e) => setConstraints(e.target.value)}
                className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 resize-none"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                What does success look like?
              </label>
              <textarea
                rows={2}
                placeholder="One criterion per line — e.g. See a live football match&#10;Try authentic local cuisine"
                value={successCriteria}
                onChange={(e) => setSuccessCriteria(e.target.value)}
                className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 resize-none"
              />
            </div>
          </div>

          {error && (
            <p className="text-red-500 text-sm px-1">{error}</p>
          )}

          <button
            type="submit"
            disabled={submitting}
            className="w-full bg-indigo-600 text-white rounded-xl py-3 font-semibold text-sm hover:bg-indigo-700 disabled:opacity-50 transition-colors"
          >
            {submitting ? "Creating goal…" : "Create goal"}
          </button>
        </form>
      </div>
    </main>
  );
}

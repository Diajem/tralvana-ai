"use client";

import type { TravellerPreferences } from "@/types/traveller";

interface Props {
  value: TravellerPreferences;
  onChange: (v: TravellerPreferences) => void;
}

const INTERESTS = [
  { label: "Beach", key: "beach" },
  { label: "City", key: "city" },
  { label: "Adventure", key: "adventure" },
  { label: "Culture", key: "culture" },
  { label: "Food & Drink", key: "food_drink" },
  { label: "Wellness", key: "wellness" },
  { label: "Sport", key: "sport" },
  { label: "Nature", key: "nature" },
  { label: "Luxury", key: "luxury" },
  { label: "Business", key: "business" },
];

const BUDGET_STYLES = [
  { key: "backpacker", label: "Backpacker" },
  { key: "budget", label: "Budget" },
  { key: "balanced", label: "Balanced" },
  { key: "comfort", label: "Comfort" },
  { key: "luxury", label: "Luxury" },
] as const;

const CURRENCIES = ["USD", "EUR", "GBP", "NGN", "AED", "JPY", "CAD", "AUD", "ZAR", "KES"];
const LANGUAGES = [
  { code: "en", label: "English" },
  { code: "fr", label: "French" },
  { code: "es", label: "Spanish" },
  { code: "pt", label: "Portuguese" },
  { code: "ar", label: "Arabic" },
  { code: "zh", label: "Mandarin" },
  { code: "ha", label: "Hausa" },
  { code: "yo", label: "Yoruba" },
];

const inputClass =
  "w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500";

export default function StepTravelStyle({ value, onChange }: Props) {
  const toggleInterest = (key: string) => {
    const updated = value.travel_interests.includes(key)
      ? value.travel_interests.filter((i) => i !== key)
      : [...value.travel_interests, key];
    onChange({ ...value, travel_interests: updated });
  };

  return (
    <div className="space-y-5">
      <div>
        <h2 className="text-xl font-semibold text-gray-900">Travel style</h2>
        <p className="text-sm text-gray-500 mt-1">
          TravelOS personalises every recommendation around these.
        </p>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Home airport{" "}
            <span className="text-gray-400 font-normal">(IATA code)</span>
          </label>
          <input
            type="text"
            value={value.home_airport}
            onChange={(e) =>
              onChange({ ...value, home_airport: e.target.value.toUpperCase().slice(0, 3) })
            }
            placeholder="LOS"
            className={inputClass}
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Preferred currency
          </label>
          <select
            value={value.preferred_currency}
            onChange={(e) => onChange({ ...value, preferred_currency: e.target.value })}
            className={inputClass}
          >
            {CURRENCIES.map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </select>
        </div>

        <div className="col-span-2">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Preferred language
          </label>
          <select
            value={value.preferred_language}
            onChange={(e) => onChange({ ...value, preferred_language: e.target.value })}
            className={inputClass}
          >
            {LANGUAGES.map((l) => (
              <option key={l.code} value={l.code}>
                {l.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Budget style
        </label>
        <div className="flex gap-2 flex-wrap">
          {BUDGET_STYLES.map(({ key, label }) => (
            <button
              key={key}
              type="button"
              onClick={() => onChange({ ...value, budget_style: key })}
              className={`px-3 py-1.5 rounded-lg text-sm font-medium border transition-colors ${
                value.budget_style === key
                  ? "border-indigo-600 bg-indigo-50 text-indigo-700"
                  : "border-gray-200 text-gray-500 hover:border-gray-300"
              }`}
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Travel interests{" "}
          <span className="text-gray-400 font-normal">(select all that apply)</span>
        </label>
        <div className="flex flex-wrap gap-2">
          {INTERESTS.map(({ label, key }) => (
            <button
              key={key}
              type="button"
              onClick={() => toggleInterest(key)}
              className={`px-3 py-1.5 rounded-lg text-sm border transition-colors ${
                value.travel_interests.includes(key)
                  ? "border-indigo-600 bg-indigo-50 text-indigo-700 font-medium"
                  : "border-gray-200 text-gray-500 hover:border-gray-300"
              }`}
            >
              {label}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

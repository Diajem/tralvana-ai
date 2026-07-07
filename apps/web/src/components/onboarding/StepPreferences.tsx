import type { TravellerPreferences } from "@/types/traveller";

interface Props {
  value: TravellerPreferences;
  onChange: (v: TravellerPreferences) => void;
}

const selectClass =
  "w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500";

export default function StepPreferences({ value, onChange }: Props) {
  const update =
    (field: keyof TravellerPreferences) =>
    (e: React.ChangeEvent<HTMLSelectElement>) =>
      onChange({ ...value, [field]: e.target.value });

  return (
    <div className="space-y-5">
      <div>
        <h2 className="text-xl font-semibold text-gray-900">
          Travel preferences
        </h2>
        <p className="text-sm text-gray-500 mt-1">
          TravelOS applies these to every recommendation.
        </p>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Seat
          </label>
          <select value={value.seat} onChange={update("seat")} className={selectClass}>
            <option value="window">Window</option>
            <option value="aisle">Aisle</option>
            <option value="no_preference">No preference</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Cabin class
          </label>
          <select value={value.cabin_class} onChange={update("cabin_class")} className={selectClass}>
            <option value="economy">Economy</option>
            <option value="business">Business</option>
            <option value="first">First</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Meal
          </label>
          <select value={value.meal} onChange={update("meal")} className={selectClass}>
            <option value="standard">Standard</option>
            <option value="vegetarian">Vegetarian</option>
            <option value="vegan">Vegan</option>
            <option value="halal">Halal</option>
            <option value="kosher">Kosher</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Accommodation
          </label>
          <select
            value={value.accommodation_type}
            onChange={update("accommodation_type")}
            className={selectClass}
          >
            <option value="hotel">Hotel</option>
            <option value="apartment">Apartment</option>
            <option value="hostel">Hostel</option>
            <option value="resort">Resort</option>
          </select>
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Budget tier
        </label>
        <div className="flex gap-3">
          {(["budget", "mid", "luxury"] as const).map((tier) => (
            <button
              key={tier}
              type="button"
              onClick={() => onChange({ ...value, budget_tier: tier })}
              className={`flex-1 py-2 rounded-lg text-sm font-medium border transition-colors ${
                value.budget_tier === tier
                  ? "border-indigo-600 bg-indigo-50 text-indigo-700"
                  : "border-gray-200 text-gray-500 hover:border-gray-300"
              }`}
            >
              {tier.charAt(0).toUpperCase() + tier.slice(1)}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

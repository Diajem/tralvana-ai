import type { TravellerPreferences } from "@/types/traveller";

interface Props {
  value: TravellerPreferences;
  onChange: (v: TravellerPreferences) => void;
}

const HOTEL_PREFS = [
  { label: "Pool", key: "pool" },
  { label: "Gym", key: "gym" },
  { label: "Wifi", key: "wifi" },
  { label: "Breakfast", key: "breakfast" },
  { label: "Spa", key: "spa" },
  { label: "Parking", key: "parking" },
  { label: "Pet friendly", key: "pet_friendly" },
];

const ACCESS_NEEDS = [
  { label: "Wheelchair access", key: "wheelchair_access" },
  { label: "Visual assistance", key: "visual_assistance" },
  { label: "Hearing assistance", key: "hearing_assistance" },
  { label: "Extra legroom", key: "extra_legroom" },
  { label: "Dietary options", key: "dietary_options" },
];

const selectClass =
  "w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500";

export default function StepPreferences({ value, onChange }: Props) {
  const update =
    (field: keyof TravellerPreferences) =>
    (e: React.ChangeEvent<HTMLSelectElement>) =>
      onChange({ ...value, [field]: e.target.value });

  const toggleList = (
    field: "hotel_preferences" | "accessibility_needs",
    key: string
  ) => {
    const current = value[field] as string[];
    const updated = current.includes(key)
      ? current.filter((i) => i !== key)
      : [...current, key];
    onChange({ ...value, [field]: updated });
  };

  const inList = (field: "hotel_preferences" | "accessibility_needs", key: string) =>
    (value[field] as string[]).includes(key);

  return (
    <div className="space-y-5">
      <div>
        <h2 className="text-xl font-semibold text-gray-900">Comfort & access</h2>
        <p className="text-sm text-gray-500 mt-1">
          Flight comfort, accommodation preferences, and accessibility needs.
        </p>
      </div>

      {/* Flight */}
      <div className="grid grid-cols-3 gap-3">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Seat</label>
          <select value={value.seat} onChange={update("seat")} className={selectClass}>
            <option value="window">Window</option>
            <option value="aisle">Aisle</option>
            <option value="no_preference">No pref.</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Cabin</label>
          <select value={value.cabin_class} onChange={update("cabin_class")} className={selectClass}>
            <option value="economy">Economy</option>
            <option value="business">Business</option>
            <option value="first">First</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Meal</label>
          <select value={value.meal} onChange={update("meal")} className={selectClass}>
            <option value="standard">Standard</option>
            <option value="vegetarian">Vegetarian</option>
            <option value="vegan">Vegan</option>
            <option value="halal">Halal</option>
            <option value="kosher">Kosher</option>
          </select>
        </div>
      </div>

      {/* Accommodation */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Accommodation type
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

      {/* Hotel preferences */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Hotel preferences{" "}
          <span className="text-gray-400 font-normal">(optional)</span>
        </label>
        <div className="flex flex-wrap gap-2">
          {HOTEL_PREFS.map(({ label, key }) => (
            <button
              key={key}
              type="button"
              onClick={() => toggleList("hotel_preferences", key)}
              className={`px-3 py-1.5 rounded-lg text-sm border transition-colors ${
                inList("hotel_preferences", key)
                  ? "border-indigo-600 bg-indigo-50 text-indigo-700 font-medium"
                  : "border-gray-200 text-gray-500 hover:border-gray-300"
              }`}
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      {/* Accessibility */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Accessibility needs{" "}
          <span className="text-gray-400 font-normal">(optional)</span>
        </label>
        <div className="flex flex-wrap gap-2">
          {ACCESS_NEEDS.map(({ label, key }) => (
            <button
              key={key}
              type="button"
              onClick={() => toggleList("accessibility_needs", key)}
              className={`px-3 py-1.5 rounded-lg text-sm border transition-colors ${
                inList("accessibility_needs", key)
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

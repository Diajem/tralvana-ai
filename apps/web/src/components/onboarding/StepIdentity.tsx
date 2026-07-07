import type { TravellerIdentity } from "@/types/traveller";

interface Props {
  value: TravellerIdentity;
  onChange: (v: TravellerIdentity) => void;
}

const inputClass =
  "w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500";

export default function StepIdentity({ value, onChange }: Props) {
  const update =
    (field: keyof TravellerIdentity) =>
    (e: React.ChangeEvent<HTMLInputElement>) =>
      onChange({ ...value, [field]: e.target.value });

  return (
    <div className="space-y-5">
      <div>
        <h2 className="text-xl font-semibold text-gray-900">Who are you?</h2>
        <p className="text-sm text-gray-500 mt-1">
          Your profile is the foundation of TravelOS.
        </p>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Full name
        </label>
        <input
          type="text"
          value={value.name}
          onChange={update("name")}
          placeholder="Peter Adeyemi"
          className={inputClass}
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Email
        </label>
        <input
          type="email"
          value={value.email}
          onChange={update("email")}
          placeholder="peter@example.com"
          className={inputClass}
        />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Locale
          </label>
          <input
            type="text"
            value={value.locale}
            onChange={update("locale")}
            placeholder="en-NG"
            className={inputClass}
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Timezone
          </label>
          <input
            type="text"
            value={value.timezone}
            onChange={update("timezone")}
            placeholder="Africa/Lagos"
            className={inputClass}
          />
        </div>
      </div>
    </div>
  );
}

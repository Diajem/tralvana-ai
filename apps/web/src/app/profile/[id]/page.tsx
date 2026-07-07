import Link from "next/link";
import { getProfile } from "@/lib/api";
import type { TravellerProfile } from "@/types/traveller";

interface Props {
  params: Promise<{ id: string }>;
}

function Tag({ label, color = "gray" }: { label: string; color?: "indigo" | "blue" | "emerald" | "amber" | "gray" }) {
  const classes = {
    indigo: "bg-indigo-50 text-indigo-700",
    blue: "bg-blue-50 text-blue-700",
    emerald: "bg-emerald-50 text-emerald-700",
    amber: "bg-amber-50 text-amber-700",
    gray: "bg-gray-100 text-gray-600",
  };
  return (
    <span className={`text-xs px-2.5 py-1 rounded-full capitalize ${classes[color]}`}>
      {label.replace(/_/g, " ")}
    </span>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="bg-white rounded-2xl shadow-sm p-6">
      <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-widest mb-4">
        {title}
      </h2>
      {children}
    </div>
  );
}

export default async function ProfilePage({ params }: Props) {
  const { id } = await params;

  let profile: TravellerProfile | null = null;
  let error: string | null = null;

  try {
    profile = await getProfile(id);
  } catch {
    error = "Could not load profile. Make sure the API is running on port 8000.";
  }

  if (error || !profile) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-gray-50">
        <div className="text-center">
          <p className="text-red-500 text-sm">{error ?? "Profile not found."}</p>
          <Link
            href="/onboarding"
            className="mt-4 inline-block text-sm text-indigo-600 hover:underline"
          >
            Create a profile
          </Link>
        </div>
      </main>
    );
  }

  const { identity, preferences, loyalty, created_at } = profile;
  const hasLoyalty =
    loyalty.airline_programs.length > 0 || loyalty.hotel_programs.length > 0;

  return (
    <main className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-2xl mx-auto space-y-4">

        {/* Header */}
        <div className="bg-white rounded-2xl shadow-sm p-8">
          <div className="flex items-start justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">{identity.name}</h1>
              <p className="text-gray-500 text-sm mt-1">{identity.email}</p>
              <p className="text-xs text-gray-400 mt-2 font-mono break-all">{profile.id}</p>
            </div>
            <span className="shrink-0 text-xs bg-emerald-50 text-emerald-700 px-2 py-1 rounded-full font-medium">
              Active
            </span>
          </div>
          <div className="mt-6 pt-5 border-t border-gray-100 flex flex-wrap gap-4 text-sm text-gray-500">
            <span>Language: <strong className="text-gray-900">{identity.locale}</strong></span>
            <span>Timezone: <strong className="text-gray-900">{identity.timezone}</strong></span>
          </div>
        </div>

        {/* Travel Style */}
        <Section title="Travel Style">
          <div className="grid grid-cols-2 gap-x-8 gap-y-3 mb-4">
            {preferences.home_airport && (
              <div className="flex justify-between text-sm">
                <span className="text-gray-500">Home airport</span>
                <strong className="text-gray-900">{preferences.home_airport}</strong>
              </div>
            )}
            <div className="flex justify-between text-sm">
              <span className="text-gray-500">Currency</span>
              <strong className="text-gray-900">{preferences.preferred_currency}</strong>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-gray-500">Language</span>
              <strong className="text-gray-900">{preferences.preferred_language}</strong>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-gray-500">Budget style</span>
              <strong className="text-gray-900 capitalize">{preferences.budget_style}</strong>
            </div>
          </div>
          {preferences.travel_interests.length > 0 && (
            <div>
              <p className="text-xs text-gray-400 mb-2">Interests</p>
              <div className="flex flex-wrap gap-1.5">
                {preferences.travel_interests.map((i) => (
                  <Tag key={i} label={i} color="indigo" />
                ))}
              </div>
            </div>
          )}
        </Section>

        {/* Flight & Accommodation */}
        <Section title="Comfort Preferences">
          <div className="grid grid-cols-3 gap-4 mb-4">
            <div className="text-sm">
              <p className="text-gray-400 text-xs mb-1">Seat</p>
              <p className="font-medium text-gray-900 capitalize">
                {preferences.seat.replace("_", " ")}
              </p>
            </div>
            <div className="text-sm">
              <p className="text-gray-400 text-xs mb-1">Cabin</p>
              <p className="font-medium text-gray-900 capitalize">{preferences.cabin_class}</p>
            </div>
            <div className="text-sm">
              <p className="text-gray-400 text-xs mb-1">Meal</p>
              <p className="font-medium text-gray-900 capitalize">{preferences.meal}</p>
            </div>
          </div>

          <div className="pt-4 border-t border-gray-100">
            <div className="flex justify-between text-sm mb-3">
              <span className="text-gray-500">Accommodation</span>
              <strong className="text-gray-900 capitalize">{preferences.accommodation_type}</strong>
            </div>

            {preferences.hotel_preferences.length > 0 && (
              <div className="mb-3">
                <p className="text-xs text-gray-400 mb-1.5">Hotel must-haves</p>
                <div className="flex flex-wrap gap-1.5">
                  {preferences.hotel_preferences.map((p) => (
                    <Tag key={p} label={p} color="blue" />
                  ))}
                </div>
              </div>
            )}

            {preferences.accessibility_needs.length > 0 && (
              <div>
                <p className="text-xs text-gray-400 mb-1.5">Accessibility</p>
                <div className="flex flex-wrap gap-1.5">
                  {preferences.accessibility_needs.map((n) => (
                    <Tag key={n} label={n} color="amber" />
                  ))}
                </div>
              </div>
            )}
          </div>
        </Section>

        {/* Loyalty */}
        {hasLoyalty && (
          <Section title="Loyalty Programs">
            <div className="flex flex-wrap gap-2">
              {loyalty.airline_programs.map((p, i) => (
                <Tag key={i} label={`${p.carrier} · ${p.number}`} color="blue" />
              ))}
              {loyalty.hotel_programs.map((p, i) => (
                <Tag key={i} label={`${p.brand} · ${p.number}`} color="emerald" />
              ))}
            </div>
          </Section>
        )}

        {/* Footer */}
        <div className="flex items-center justify-between px-1 text-xs text-gray-400">
          <span>
            Created{" "}
            {new Date(created_at).toLocaleDateString("en-GB", { dateStyle: "long" })}
          </span>
          <Link href="/onboarding" className="text-indigo-600 hover:underline">
            New profile
          </Link>
        </div>
      </div>
    </main>
  );
}

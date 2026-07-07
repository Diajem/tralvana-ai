import Link from "next/link";
import { getProfile } from "@/lib/api";
import type { TravellerProfile } from "@/types/traveller";

interface Props {
  params: Promise<{ id: string }>;
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

  return (
    <main className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-2xl mx-auto space-y-4">

        {/* Header card */}
        <div className="bg-white rounded-2xl shadow-sm p-8">
          <div className="flex items-start justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">{identity.name}</h1>
              <p className="text-gray-500 text-sm mt-1">{identity.email}</p>
              <p className="text-xs text-gray-400 mt-2 font-mono break-all">{profile.id}</p>
            </div>
            <span className="text-xs bg-emerald-50 text-emerald-700 px-2 py-1 rounded-full font-medium shrink-0">
              Active
            </span>
          </div>

          <div className="mt-6 pt-6 border-t border-gray-100 flex gap-6 text-sm text-gray-500">
            <span>Locale: <strong className="text-gray-900">{identity.locale}</strong></span>
            <span>Timezone: <strong className="text-gray-900">{identity.timezone}</strong></span>
          </div>
        </div>

        {/* Preferences card */}
        <div className="bg-white rounded-2xl shadow-sm p-6">
          <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-4">
            Travel Preferences
          </h2>
          <dl className="grid grid-cols-2 gap-x-8 gap-y-3">
            {Object.entries(preferences).map(([k, v]) => (
              <div key={k} className="flex justify-between text-sm">
                <dt className="text-gray-500 capitalize">{k.replace("_", " ")}</dt>
                <dd className="text-gray-900 font-medium capitalize">
                  {String(v).replace("_", " ")}
                </dd>
              </div>
            ))}
          </dl>
        </div>

        {/* Loyalty card */}
        {(loyalty.airline_programs.length > 0 ||
          loyalty.hotel_programs.length > 0) && (
          <div className="bg-white rounded-2xl shadow-sm p-6">
            <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-4">
              Loyalty Programs
            </h2>
            <div className="flex flex-wrap gap-2">
              {loyalty.airline_programs.map((p, i) => (
                <span
                  key={i}
                  className="text-xs bg-blue-50 text-blue-700 px-3 py-1 rounded-full"
                >
                  {p.carrier} · {p.number}
                </span>
              ))}
              {loyalty.hotel_programs.map((p, i) => (
                <span
                  key={i}
                  className="text-xs bg-emerald-50 text-emerald-700 px-3 py-1 rounded-full"
                >
                  {p.brand} · {p.number}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Footer */}
        <div className="flex items-center justify-between px-1 text-xs text-gray-400">
          <span>
            Created {new Date(created_at).toLocaleDateString("en-GB", { dateStyle: "long" })}
          </span>
          <Link href="/onboarding" className="text-indigo-600 hover:underline">
            New profile
          </Link>
        </div>
      </div>
    </main>
  );
}

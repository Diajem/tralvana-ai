import Link from "next/link";

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24 text-center">
      <h1 className="text-4xl font-bold text-gray-900">Tralvana AI</h1>
      <p className="mt-4 text-lg text-gray-500 max-w-xl">
        Describe your trip in your own words. Tralvana pulls together destinations, flights,
        accommodation, budget, visa requirements, and weather into one coherent plan.
      </p>
      <div className="mt-10 flex flex-col items-center gap-3 sm:flex-row">
        <Link
          href="/planner"
          className="px-6 py-3 bg-indigo-600 text-white rounded-lg text-sm font-medium hover:bg-indigo-700 transition-colors"
        >
          Plan My Trip
        </Link>
        <Link
          href="/onboarding"
          className="px-6 py-3 bg-white border border-gray-300 text-gray-700 rounded-lg text-sm font-medium hover:border-indigo-400 transition-colors"
        >
          Create your Traveller Profile
        </Link>
      </div>
    </main>
  );
}

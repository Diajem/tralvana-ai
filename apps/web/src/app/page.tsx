import Link from "next/link";

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24">
      <h1 className="text-4xl font-bold text-gray-900">Tralvana AI</h1>
      <p className="mt-4 text-lg text-gray-500">AI-native travel operating system</p>
      <div className="mt-10">
        <Link
          href="/onboarding"
          className="px-6 py-3 bg-indigo-600 text-white rounded-lg text-sm font-medium hover:bg-indigo-700 transition-colors"
        >
          Create your Traveller Profile
        </Link>
      </div>
    </main>
  );
}

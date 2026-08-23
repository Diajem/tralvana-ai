import Link from "next/link";

const capabilities = [
  ["Flights", "Compare routes and surface the trade-offs that matter."],
  ["Accommodation", "Match stays to your budget, comfort, and location needs."],
  ["Visa guidance", "Bring nationality and destination requirements into the plan."],
  ["Budget", "See a clear, category-by-category planning estimate."],
  ["Weather", "Plan around seasonal conditions and travel risks."],
  ["Live events", "Find relevant Ticketmaster listings during your travel dates."],
] as const;

const steps = [
  ["1", "Describe the whole trip", "Use normal language—destination, dates, travellers, interests, origin, and budget."],
  ["2", "Tralvana connects the decisions", "One Trip Brain coordinates travel, budget, entry guidance, weather, and activities."],
  ["3", "Get one explainable plan", "Review the daily outline, assumptions, risks, alternatives, and what still needs checking."],
] as const;

export default function Home() {
  return (
    <main className="min-h-screen bg-slate-950 text-white">
      <nav className="mx-auto flex max-w-6xl items-center justify-between px-6 py-6 lg:px-8">
        <Link href="/" className="text-xl font-bold tracking-tight">
          Tralvana <span className="text-cyan-400">AI</span>
        </Link>
        <div className="hidden items-center gap-7 text-sm text-slate-300 sm:flex">
          <a href="#how-it-works" className="hover:text-white">How it works</a>
          <a href="#capabilities" className="hover:text-white">What it plans</a>
          <Link href="/my-trips" className="hover:text-white">My Trips</Link>
          <Link href="/demo" className="hover:text-white">See the technology</Link>
        </div>
      </nav>

      <section className="relative overflow-hidden px-6 pb-24 pt-20 lg:px-8 lg:pb-32 lg:pt-28">
        <div className="absolute left-1/2 top-0 h-[520px] w-[820px] -translate-x-1/2 rounded-full bg-indigo-600/20 blur-3xl" />
        <div className="relative mx-auto max-w-5xl text-center">
          <div className="mb-6 inline-flex rounded-full border border-cyan-400/30 bg-cyan-400/10 px-4 py-2 text-xs font-semibold uppercase tracking-[0.18em] text-cyan-300">
            One intelligent plan for the whole journey
          </div>
          <h1 className="text-5xl font-bold tracking-tight sm:text-6xl lg:text-7xl">
            Stop planning your trip
            <span className="block bg-gradient-to-r from-cyan-300 to-indigo-400 bg-clip-text text-transparent">
              in ten different places.
            </span>
          </h1>
          <p className="mx-auto mt-7 max-w-3xl text-lg leading-8 text-slate-300 sm:text-xl">
            Tell Tralvana where you want to go. It brings flights, stays, budget,
            visa guidance, weather, and events together into one explainable itinerary.
          </p>
          <div className="mt-10 flex flex-col items-center justify-center gap-4 sm:flex-row">
            <Link href="/planner" className="w-full rounded-xl bg-cyan-400 px-7 py-4 text-base font-bold text-slate-950 transition hover:bg-cyan-300 sm:w-auto">
              Build My Trip
            </Link>
            <Link href="/onboarding" className="w-full rounded-xl border border-slate-600 bg-white/5 px-7 py-4 text-base font-semibold text-white transition hover:border-slate-400 hover:bg-white/10 sm:w-auto">
              Create Traveller Profile
            </Link>
          </div>
          <p className="mt-5 text-xs text-slate-500">
            Live results, estimates, general guidance, and curated ideas are clearly labelled.
          </p>
        </div>
      </section>

      <section id="how-it-works" className="border-y border-white/10 bg-white/[0.03] px-6 py-20 lg:px-8">
        <div className="mx-auto max-w-6xl">
          <p className="text-sm font-semibold uppercase tracking-[0.18em] text-cyan-400">How it works</p>
          <h2 className="mt-3 max-w-2xl text-3xl font-bold tracking-tight sm:text-4xl">
            One conversation. One connected travel decision.
          </h2>
          <div className="mt-12 grid gap-6 md:grid-cols-3">
            {steps.map(([number, title, description]) => (
              <article key={number} className="rounded-2xl border border-white/10 bg-slate-900 p-7">
                <span className="flex h-10 w-10 items-center justify-center rounded-full bg-indigo-500 text-sm font-bold">{number}</span>
                <h3 className="mt-6 text-lg font-semibold">{title}</h3>
                <p className="mt-3 text-sm leading-6 text-slate-400">{description}</p>
              </article>
            ))}
          </div>
        </div>
      </section>

      <section id="capabilities" className="px-6 py-24 lg:px-8">
        <div className="mx-auto max-w-6xl">
          <div className="max-w-3xl">
            <p className="text-sm font-semibold uppercase tracking-[0.18em] text-cyan-400">Built around the whole trip</p>
            <h2 className="mt-3 text-3xl font-bold tracking-tight sm:text-4xl">
              Travel decisions should work together—not fight each other.
            </h2>
            <p className="mt-5 text-slate-400">
              Tralvana coordinates seven specialist intelligence modules and explains its recommendations,
              alternatives, confidence, assumptions, and risks.
            </p>
          </div>
          <div className="mt-12 grid gap-px overflow-hidden rounded-2xl border border-white/10 bg-white/10 sm:grid-cols-2 lg:grid-cols-3">
            {capabilities.map(([title, description]) => (
              <article key={title} className="bg-slate-950 p-7">
                <div className="mb-5 h-1 w-10 rounded-full bg-gradient-to-r from-cyan-400 to-indigo-500" />
                <h3 className="font-semibold">{title}</h3>
                <p className="mt-2 text-sm leading-6 text-slate-400">{description}</p>
              </article>
            ))}
          </div>
        </div>
      </section>

      <section className="px-6 pb-24 lg:px-8">
        <div className="mx-auto max-w-6xl rounded-3xl bg-gradient-to-br from-indigo-600 to-indigo-900 px-7 py-12 text-center sm:px-12 sm:py-16">
          <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">Your trip deserves one clear plan.</h2>
          <p className="mx-auto mt-4 max-w-2xl text-indigo-100">
            Start with the journey you have in mind. Tralvana will ask for anything essential that is missing.
          </p>
          <Link href="/planner" className="mt-8 inline-flex rounded-xl bg-white px-7 py-4 font-bold text-indigo-800 transition hover:bg-cyan-50">
            Start Planning
          </Link>
        </div>
      </section>

      <footer className="border-t border-white/10 px-6 py-8 text-center text-xs text-slate-500">
        <p>© 2026 Tralvana AI. Planning intelligence—not a booking or legal-advice service.</p>
      </footer>
    </main>
  );
}

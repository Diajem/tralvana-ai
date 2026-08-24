"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { getLatestSavedPlan, getSavedPlan, planTrip } from "@/lib/api";
import { useTralvanaAuth } from "@/lib/auth-context";
import type { DailyOutlineEntry, GroundingNotice, PlanningReadiness, PlanTripResponse, TripItinerary } from "@/types/planner";

function ReadinessBadge({ score }: { score: number }) {
  const pct = Math.round(score);
  const colour = pct >= 70 ? "bg-green-100 text-green-800" : pct >= 45 ? "bg-amber-100 text-amber-800" : "bg-red-100 text-red-800";
  return (
    <span className={`px-3 py-1 rounded-full text-sm font-semibold ${colour}`}>
      {pct}% ready
    </span>
  );
}

function SectionCard({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-6">
      <h2 className="text-lg font-semibold text-gray-900 mb-3">{title}</h2>
      {children}
    </div>
  );
}

function ProviderImage({
  url,
  alt,
  source,
  fallback,
}: {
  url?: unknown;
  alt: string;
  source?: unknown;
  fallback: string;
}) {
  const imageUrl = typeof url === "string" && url.startsWith("https://") ? url : null;
  return (
    <div
      role={imageUrl ? "img" : undefined}
      aria-label={imageUrl ? alt : undefined}
      className={`relative mb-4 h-36 overflow-hidden rounded-xl bg-gradient-to-br ${fallback}`}
      style={imageUrl ? { backgroundImage: `url(${JSON.stringify(imageUrl).slice(1, -1)})`, backgroundPosition: "center", backgroundSize: "cover" } : undefined}
    >
      {!imageUrl && (
        <div className="flex h-full items-end p-4 text-xs font-semibold uppercase tracking-[0.16em] text-white/90">
          Visual preview
        </div>
      )}
      {imageUrl && typeof source === "string" && (
        <span className="absolute bottom-2 right-2 rounded-full bg-black/60 px-2 py-1 text-[10px] font-medium text-white">
          Image: {source}
        </span>
      )}
    </div>
  );
}

function PlanningReadinessCard({
  readiness,
  onAnswer,
}: {
  readiness: PlanningReadiness;
  onAnswer: () => void;
}) {
  const readyLabel = readiness.stage === "SEARCH_READY"
    ? "Ready for live search"
    : readiness.stage === "INSPIRATION_READY"
      ? "Inspiration plan ready"
      : "Still understanding your trip";
  return (
    <section className="rounded-2xl border border-cyan-200 bg-gradient-to-r from-cyan-50 to-indigo-50 p-5 shadow-sm sm:p-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="text-xs font-bold uppercase tracking-[0.16em] text-cyan-700">Trip readiness</p>
          <h2 className="mt-1 text-xl font-bold text-slate-950">{readyLabel}</h2>
          {readiness.profile_fields_used.length > 0 && (
            <p className="mt-2 text-xs text-slate-600">
              Remembered from your profile: {readiness.profile_fields_used.map(fmtKey).join(", ")}.
            </p>
          )}
        </div>
        <ReadinessBadge score={readiness.score} />
      </div>
      {readiness.next_question ? (
        <div className="mt-5 rounded-xl bg-white p-4 ring-1 ring-cyan-100">
          <p className="text-sm font-semibold text-slate-950">{readiness.next_question}</p>
          <button type="button" onClick={onAnswer} className="mt-3 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-bold text-white hover:bg-indigo-700">
            Answer this question
          </button>
        </div>
      ) : (
        <p className="mt-4 text-sm font-medium text-emerald-700">The essential planning details are complete.</p>
      )}
      {!readiness.can_live_search && readiness.missing_essential.length > 0 && (
        <details className="mt-4 text-sm text-slate-600">
          <summary className="cursor-pointer font-semibold text-slate-700">Details still needed for reliable live results</summary>
          <ul className="mt-2 grid gap-1 sm:grid-cols-2">
            {readiness.missing_essential.map((item) => <li key={item}>• {item}</li>)}
          </ul>
        </details>
      )}
    </section>
  );
}

function fmtKey(key: string): string {
  return key.replace(/_/g, " ");
}

const MONEY_FIELDS = new Set([
  "estimated_price", "nightly_price", "total_price", "total_cost_usd",
  "cost_per_day_usd", "cost_per_person_usd", "flight_cost_usd",
  "accommodation_usd", "food_usd", "activities_usd", "misc_usd",
  "declared_budget", "transport_allocation", "accommodation_allocation",
  "food_allocation", "activities_allocation", "contingency_allocation",
]);

const STARTER_PROMPTS = [
  {
    label: "City break",
    value: "Plan a 5-day city break to New York from Manchester in October for 2 adults with a £3,000 budget. We like food, culture and shopping.",
  },
  {
    label: "Beach holiday",
    value: "Plan a 7-day beach holiday to Montego Bay from London in November for 2 adults with a £2,800 budget. We like food, music and culture.",
  },
  {
    label: "Football trip",
    value: "Plan a 3-day football trip to Barcelona from London in November for 2 adults with a £1,500 budget. Include food and major attractions.",
  },
] as const;

function fmtValue(key: string, value: unknown, data: Record<string, unknown>): string {
  if (MONEY_FIELDS.has(key) && typeof value === "number") {
    const currency = typeof data.currency === "string" ? data.currency : "USD";
    try {
      return new Intl.NumberFormat("en-GB", {
        style: "currency",
        currency,
        maximumFractionDigits: 0,
      }).format(value);
    } catch {
      return `${currency} ${value.toLocaleString()}`;
    }
  }
  if (key === "match_score" && typeof value === "number") {
    return `${Math.round(value * 100)}%`;
  }
  if (key === "local_date" && typeof value === "string") {
    const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(value);
    if (match) {
      const [, year, month, day] = match;
      return new Intl.DateTimeFormat("en-GB", {
        day: "numeric",
        month: "short",
        year: "numeric",
        timeZone: "UTC",
      }).format(new Date(Date.UTC(Number(year), Number(month) - 1, Number(day))));
    }
  }
  if (key === "local_time" && typeof value === "string") {
    const match = /^(\d{2}):(\d{2})/.exec(value);
    if (match) return `${match[1]}:${match[2]}`;
  }
  if (typeof value === "boolean") return value ? "Yes" : "No";
  if (Array.isArray(value)) return value.join(", ");
  return String(value).replace(/_/g, " ");
}

function RecommendationFacts({ data }: { data: Record<string, unknown> }) {
  // Show a curated, readable subset rather than dumping every raw
  // field — but never invent a value that isn't already in `data`.
  const preferredOrder = [
    "airline", "flight_number", "property_name", "name", "city", "budget_style",
    "category", "venue_area", "local_date", "local_time", "date_status",
    "availability_status", "team_level",
    "estimated_price", "nightly_price", "total_price", "currency",
    "duration_days", "adults", "children", "total_cost_usd", "cost_per_day_usd",
    "declared_budget", "assessment_status", "affordability_status",
    "transport_allocation", "accommodation_allocation", "food_allocation",
    "activities_allocation", "contingency_allocation", "allocation_basis",
    "flight_cost_usd", "accommodation_usd", "food_usd", "activities_usd", "misc_usd",
    "star_rating", "review_score", "match_score", "recommendation_type",
    "cabin_class", "accommodation_type", "stops", "total_duration",
    "cancellation_policy", "breakfast_included", "visa_status", "visa_required",
    "visa_type", "assessment_scope", "nationalities_considered", "nationalities_pending",
    "processing_time", "month_of_travel", "season", "weather_status",
    "weather_summary", "safety_summary", "natural_hazard_risk",
    "transport_disruption_risk", "recommendation",
  ];
  const entries = preferredOrder
    .filter((k) => k in data && data[k] !== null && data[k] !== undefined && data[k] !== "")
    .map((k) => [k, data[k]] as const);

  if (entries.length === 0) return null;

  return (
    <dl className="grid grid-cols-2 gap-x-4 gap-y-2 text-sm sm:grid-cols-3">
      {entries.map(([key, value]) => (
        <div key={key}>
          <dt className="text-gray-400 text-xs capitalize">{fmtKey(key)}</dt>
          <dd className="font-medium text-gray-900">{fmtValue(key, value, data)}</dd>
        </div>
      ))}
    </dl>
  );
}

function PassportAssessments({ data }: { data: Record<string, unknown> }) {
  const assessments = Array.isArray(data.individual_assessments)
    ? data.individual_assessments.filter(
        (item): item is Record<string, unknown> => Boolean(item) && typeof item === "object",
      )
    : [];
  if (assessments.length <= 1) return null;

  return (
    <div className="mt-4 grid gap-3 sm:grid-cols-2">
      {assessments.map((assessment, index) => (
        <div key={`${String(assessment.nationality || "passport")}-${index}`} className="rounded-xl border border-indigo-100 bg-indigo-50/60 p-3">
          <p className="text-xs font-bold uppercase tracking-wide text-indigo-600">
            {String(assessment.nationality || assessment.passport_country || "Passport")}
          </p>
          <p className="mt-1 font-semibold text-slate-950">
            {String(assessment.visa_type || assessment.visa_status || "Check required")}
          </p>
          <p className="mt-1 text-xs leading-5 text-slate-600">
            {String(assessment.recommendation || "Confirm the current official entry requirements before travel.")}
          </p>
        </div>
      ))}
    </div>
  );
}

function ProviderStatus({ data, domain }: { data: Record<string, unknown>; domain: "flight" | "hotel" }) {
  const source = String(data.data_source || "").toUpperCase();
  if (source.includes("SANDBOX")) {
    return <p className="mb-3 rounded-lg bg-amber-50 px-3 py-2 text-xs font-semibold leading-5 text-amber-800">Sandbox test data — demonstrates the {domain} integration but is not available to purchase.</p>;
  }
  if (source === "MOCK" || source === "MOCK_FALLBACK") {
    return <p className="mb-3 rounded-lg bg-blue-50 px-3 py-2 text-xs font-semibold leading-5 text-blue-800">Indicative planning estimate — not live inventory or a bookable quote.</p>;
  }
  return null;
}

function TripBriefCard({ itinerary }: { itinerary: TripItinerary }) {
  const brief = itinerary.trip_brief;
  const childAges = brief.travellers.minor_ages || [];
  const childAgesText = childAges.length
    ? ` aged ${childAges.length === 1 ? childAges[0] : `${childAges.slice(0, -1).join(", ")} and ${childAges.at(-1)}`}`
    : "";
  const travellers = [
    `${brief.travellers.adults} adult${brief.travellers.adults === 1 ? "" : "s"}`,
    brief.travellers.children
      ? `${brief.travellers.children} child${brief.travellers.children === 1 ? "" : "ren"}${childAgesText}`
      : "",
    brief.travellers.infants
      ? `${brief.travellers.infants} infant${brief.travellers.infants === 1 ? "" : "s"}`
      : "",
  ].filter(Boolean).join(", ");
  const departure = brief.departure_options?.length > 1
    ? brief.departure_options.join(" or ")
    : brief.origin || "Not supplied";
  const occasion = brief.special_occasion
    ? `${brief.special_occasion.type}${brief.special_occasion.date ? ` · ${brief.special_occasion.date}` : ""}`
    : "Not supplied";
  const companion = brief.companion_plan
    ? `${brief.companion_plan.relationship || "Companion"}${brief.companion_plan.origin ? ` travelling separately from ${brief.companion_plan.origin}` : ""}`
    : "Not supplied";

  return (
    <SectionCard title="Trip Details We Are Using">
      <dl className="grid grid-cols-2 gap-x-4 gap-y-3 text-sm sm:grid-cols-3">
        {[
          ["Fly from", departure],
          ["Airport preference", brief.airport_preference || "Not supplied"],
          ["Preferred airlines", brief.airline_preferences?.length ? brief.airline_preferences.join(", ") : "Not supplied"],
          ["To", brief.destination_region ? `${brief.destination}, ${brief.destination_region}` : brief.destination],
          ["Stay areas", brief.local_areas?.length ? brief.local_areas.join(", ") : "Not supplied"],
          ["Duration", `${brief.duration_days} days`],
          ["Travel period", brief.travel_period],
          ["Travellers", travellers],
          ["Passport nationalities", brief.nationalities?.length ? brief.nationalities.join(", ") : brief.nationality || "Not supplied"],
          ["Country of residence", brief.country_of_residence || "Not supplied"],
          ["Residence or visa documents", brief.residency_documents?.length ? brief.residency_documents.join(", ") : "Not supplied"],
          ["Flight cabin", brief.cabin_class || "Not supplied"],
          ["Hotel arrangement", brief.accommodation_preferences?.length ? brief.accommodation_preferences.join(", ") : "Not supplied"],
          ["Dining out", brief.dining_out_count !== null ? `${brief.dining_out_count} planned restaurant meal${brief.dining_out_count === 1 ? "" : "s"}` : "Not supplied"],
          ["Dining preferences", brief.dining_preferences?.length ? brief.dining_preferences.join(", ") : "Not supplied"],
          ["Baggage guidance", brief.baggage_information_requested ? "Requested — confirm against the selected live fare" : "Not requested"],
          ["Accessibility", brief.accessibility_needs?.length ? brief.accessibility_needs.join(", ") : "Not supplied"],
          ["Dietary needs", brief.dietary_requirements?.length ? brief.dietary_requirements.join(", ") : "Not supplied"],
          ["Must avoid", brief.negative_constraints?.length ? brief.negative_constraints.join(", ") : "Not supplied"],
          ["Interests", brief.interests.length ? brief.interests.join(", ") : "Not supplied"],
          ["Special occasion", occasion],
          ["Separate arrival", companion],
        ].map(([label, value]) => (
          <div key={label}>
            <dt className="text-xs text-gray-400">{label}</dt>
            <dd className="font-medium text-gray-900">{value}</dd>
          </div>
        ))}
      </dl>
      {brief.duration_note && (
        <p className="mt-4 rounded-lg bg-amber-50 px-3 py-2 text-xs leading-5 text-amber-800">
          <span className="font-semibold">Duration check:</span> {brief.duration_note}
        </p>
      )}
      {brief.date_inference_note && (
        <p className="mt-4 rounded-lg bg-blue-50 px-3 py-2 text-xs leading-5 text-blue-800">
          <span className="font-semibold">Date assumed:</span> {brief.date_inference_note}
        </p>
      )}
    </SectionCard>
  );
}

function RequestedStayPlanCard({ itinerary }: { itinerary: TripItinerary }) {
  const stays = itinerary.trip_brief.stay_plan || [];
  if (!stays.length) return null;

  return (
    <SectionCard title="Your Requested Stay Plan">
      <div className="grid gap-3 md:grid-cols-2">
        {stays.map((stay, index) => (
          <div key={`${stay.start_date}-${index}`} className="rounded-xl border border-indigo-100 bg-indigo-50/60 p-4">
            <p className="text-xs font-bold uppercase tracking-wide text-indigo-600">
              Stay {index + 1} · Requested, not booked
            </p>
            <p className="mt-2 font-semibold text-slate-950">
              {stay.property_name || stay.style || "Accommodation to search"}
            </p>
            <p className="mt-1 text-sm text-slate-600">
              {stay.area || "Area to confirm"}
            </p>
            <p className="mt-2 text-sm font-medium text-slate-800">
              {stay.start_date || "Start date needed"} → {stay.end_date || "End date needed"}
            </p>
          </div>
        ))}
      </div>
      <p className="mt-4 text-xs leading-5 text-amber-700">
        These are your requested stays. Tralvana has not yet confirmed a room, rate, or booking.
      </p>
    </SectionCard>
  );
}

function RequestedEventsCard({ itinerary }: { itinerary: TripItinerary }) {
  const events = itinerary.trip_brief.requested_events || [];
  if (!events.length) return null;

  return (
    <SectionCard title="Events You Asked For">
      <div className="grid gap-3 md:grid-cols-2">
        {events.map((event) => (
          <div key={event.name} className="rounded-xl border border-indigo-100 bg-indigo-50/60 p-4">
            <p className="text-xs font-bold uppercase tracking-wide text-indigo-600">
              Requested · Not yet confirmed
            </p>
            <p className="mt-2 font-semibold text-slate-950">{event.name}</p>
            <p className="mt-1 text-sm text-slate-600">{event.type}</p>
            <p className="mt-2 text-sm text-slate-800">
              {event.ticket_requested
                ? "Ticket requested — official fixture date, ticket quantity and availability still need checking."
                : "Official fixture date and availability still need checking."}
            </p>
          </div>
        ))}
      </div>
    </SectionCard>
  );
}

function RequestedActivitiesCard({ itinerary }: { itinerary: TripItinerary }) {
  const activities = itinerary.trip_brief.requested_activities || [];
  if (!activities.length) return null;

  return (
    <SectionCard title="Activities You Asked For">
      <div className="grid gap-3 sm:grid-cols-2">
        {activities.map((activity) => (
          <div key={activity} className="rounded-xl border border-indigo-100 bg-indigo-50/60 p-4">
            <p className="text-xs font-bold uppercase tracking-wide text-indigo-600">
              Included in your plan
            </p>
            <p className="mt-2 font-semibold text-slate-950">{activity}</p>
            <p className="mt-1 text-xs leading-5 text-slate-600">
              Availability, opening times and tickets must be checked for the confirmed travel year.
            </p>
          </div>
        ))}
      </div>
    </SectionCard>
  );
}

function ReadinessCard({ itinerary }: { itinerary: TripItinerary }) {
  const readiness = itinerary.booking_readiness;
  return (
    <SectionCard title="What Is Still Needed">
      {readiness.items_needed.length ? (
        <ul className="space-y-2">
          {readiness.items_needed.map((item) => (
            <li key={item} className="text-sm text-gray-700">• {item}</li>
          ))}
        </ul>
      ) : (
        <p className="text-sm text-green-700">
          The planning inputs are complete. Recheck all live prices and availability before paying.
        </p>
      )}
    </SectionCard>
  );
}

function DailyOutlineCard({ entry }: { entry: DailyOutlineEntry }) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5">
      <p className="font-semibold text-gray-900">{entry.title}</p>
      <div className="mt-3 space-y-2 text-sm text-gray-700">
        <p><span className="text-gray-400">Morning:</span> {entry.morning}</p>
        <p><span className="text-gray-400">Afternoon:</span> {entry.afternoon}</p>
        <p><span className="text-gray-400">Evening:</span> {entry.evening}</p>
      </div>
      <div className="mt-3 pt-3 border-t border-gray-100 text-xs text-gray-500">
        <span>{entry.accommodation}</span>
      </div>
      {entry.notes && <p className="mt-2 text-xs text-amber-700">{entry.notes}</p>}
    </div>
  );
}

function GroundingCard({ notice }: { notice: GroundingNotice }) {
  const colour =
    notice.level === "LIVE"
      ? "border-green-200 bg-green-50 text-green-800"
      : notice.level === "SANDBOX"
        ? "border-blue-200 bg-blue-50 text-blue-800"
        : "border-amber-200 bg-amber-50 text-amber-800";

  return (
    <div className={`rounded-xl border p-4 ${colour}`}>
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-sm font-semibold">{notice.title}</p>
          <p className="mt-1 text-xs leading-5 opacity-90">{notice.message}</p>
        </div>
        <span className="shrink-0 rounded-full bg-white/70 px-2 py-1 text-[10px] font-bold">
          {fmtKey(notice.level)}
        </span>
      </div>
    </div>
  );
}

function ItineraryView({
  itinerary,
  readiness,
  onAnswer,
  onStartOver,
}: {
  itinerary: TripItinerary;
  readiness: PlanningReadiness | null;
  onAnswer: () => void;
  onStartOver: () => void;
}) {
  const [showAllDays, setShowAllDays] = useState(false);
  const hasLiveEvents = itinerary.event_recommendations.some(
    (event) => event.data_source === "TICKETMASTER_DISCOVERY_API"
  );
  const days = showAllDays
    ? itinerary.daily_outline
    : itinerary.daily_outline.slice(0, 4);
  const brief = itinerary.trip_brief;
  const travellerSummary = [
    `${brief.travellers.adults} adult${brief.travellers.adults === 1 ? "" : "s"}`,
    brief.travellers.children
      ? `${brief.travellers.children} child${brief.travellers.children === 1 ? "" : "ren"}`
      : "",
    brief.travellers.infants
      ? `${brief.travellers.infants} infant${brief.travellers.infants === 1 ? "" : "s"}`
      : "",
  ].filter(Boolean).join(", ");

  return (
    <div className="space-y-8 pb-16">
      <section className="overflow-hidden rounded-3xl bg-gradient-to-br from-slate-950 via-indigo-950 to-indigo-700 p-7 text-white shadow-xl sm:p-10">
        <div className="flex flex-wrap items-start justify-between gap-5">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-cyan-300">Your trip plan</p>
            <h2 className="mt-3 text-3xl font-bold tracking-tight sm:text-4xl">
              {brief.origin ? `${brief.origin} → ` : ""}{brief.destination}
            </h2>
            <p className="mt-2 text-sm text-indigo-100">
              {brief.travel_period} · {brief.duration_days} days · {travellerSummary}
            </p>
          </div>
          <ReadinessBadge score={itinerary.booking_readiness.score} />
        </div>
        <p className="mt-6 max-w-3xl text-sm leading-7 text-slate-200 sm:text-base">
          {itinerary.executive_summary}
        </p>
        <div className="mt-7 flex flex-wrap gap-3">
          <a href="#essentials" className="rounded-xl bg-cyan-400 px-4 py-2.5 text-sm font-bold text-slate-950 hover:bg-cyan-300">
            View travel essentials
          </a>
          <a href="#daily-plan" className="rounded-xl border border-white/20 bg-white/10 px-4 py-2.5 text-sm font-semibold hover:bg-white/15">
            See daily plan
          </a>
          <button type="button" onClick={onStartOver} className="rounded-xl px-4 py-2.5 text-sm font-semibold text-indigo-100 hover:bg-white/10">
            Start a new trip
          </button>
        </div>
      </section>

      {readiness && <PlanningReadinessCard readiness={readiness} onAnswer={onAnswer} />}

      <nav className="sticky top-0 z-10 -mx-2 overflow-x-auto border-y border-slate-200 bg-gray-50/95 px-2 py-3 backdrop-blur">
        <div className="flex min-w-max gap-2 text-sm font-semibold text-slate-600">
          {[
            ["overview", "Overview"],
            ["essentials", "Travel & stay"],
            ["entry", "Entry & weather"],
            ["activities", "Things to do"],
            ["daily-plan", "Daily plan"],
            ["plan-details", "Checks & details"],
          ].map(([id, label]) => (
            <a key={id} href={`#${id}`} className="rounded-full bg-white px-4 py-2 shadow-sm ring-1 ring-slate-200 hover:text-indigo-700">
              {label}
            </a>
          ))}
        </div>
      </nav>

      <section id="overview" className="scroll-mt-20 space-y-4">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-indigo-600">At a glance</p>
          <h2 className="mt-1 text-2xl font-bold text-slate-950">Your plan and what comes next</h2>
        </div>
        <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
          <TripBriefCard itinerary={itinerary} />
          <ReadinessCard itinerary={itinerary} />
        </div>
      </section>

      <section id="essentials" className="scroll-mt-20 space-y-4">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-indigo-600">Travel essentials</p>
          <h2 className="mt-1 text-2xl font-bold text-slate-950">Flights, stay and budget</h2>
        </div>
        <RequestedStayPlanCard itinerary={itinerary} />
        <div className="grid grid-cols-1 gap-5 lg:grid-cols-3">
          <SectionCard title="Flight">
            {itinerary.flight_recommendation ? (
              <><ProviderStatus data={itinerary.flight_recommendation} domain="flight" /><RecommendationFacts data={itinerary.flight_recommendation} /></>
            ) : (
              <p className="text-sm leading-6 text-amber-700">A current flight result is still needed. No invented airline or fare is shown.</p>
            )}
          </SectionCard>
          <SectionCard title="Accommodation">
            {itinerary.accommodation_recommendation ? (
              <>
                <ProviderImage
                  url={itinerary.accommodation_recommendation.image_url}
                  alt={String(itinerary.accommodation_recommendation.property_name || "Recommended accommodation")}
                  source={itinerary.accommodation_recommendation.image_source}
                  fallback="from-teal-700 via-cyan-600 to-sky-400"
                />
                <ProviderStatus data={itinerary.accommodation_recommendation} domain="hotel" />
                <RecommendationFacts data={itinerary.accommodation_recommendation} />
              </>
            ) : (
              <>
                <ProviderImage alt="Accommodation visual placeholder" fallback="from-teal-700 via-cyan-600 to-sky-400" />
                <p className="text-sm leading-6 text-amber-700">A current hotel result is still needed. A real property photo will appear only when its provider supplies one.</p>
              </>
            )}
          </SectionCard>
          <SectionCard title="Budget">
            {itinerary.budget_summary ? (
              <RecommendationFacts data={itinerary.budget_summary} />
            ) : (
              <p className="text-sm leading-6 text-slate-600">Add your total trip budget to receive a suggested allocation.</p>
            )}
          </SectionCard>
        </div>
      </section>

      <section id="entry" className="scroll-mt-20 space-y-4">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-indigo-600">Before you travel</p>
          <h2 className="mt-1 text-2xl font-bold text-slate-950">Entry guidance and seasonal conditions</h2>
        </div>
        <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
          <SectionCard title="Passport & entry guidance">
            {itinerary.visa_summary ? (
              <>
                <RecommendationFacts data={itinerary.visa_summary} />
                <PassportAssessments data={itinerary.visa_summary} />
              </>
            ) : <p className="text-sm text-slate-600">Add passport nationality for entry guidance.</p>}
          </SectionCard>
          <SectionCard title="Weather expectations">
            {itinerary.weather_expectations ? <RecommendationFacts data={itinerary.weather_expectations} /> : <p className="text-sm text-slate-600">Seasonal guidance is not available for this destination yet.</p>}
          </SectionCard>
        </div>
      </section>

      <section id="activities" className="scroll-mt-20 space-y-4">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-indigo-600">Things to do</p>
          <h2 className="mt-1 text-2xl font-bold text-slate-950">
            {hasLiveEvents ? "Events during your dates" : "Ideas matched to your interests"}
          </h2>
          <p className="mt-2 text-sm text-slate-500">
            {hasLiveEvents
              ? "Current listings are linked to official pages; confirm ticket availability before paying."
              : "These are planning ideas, not confirmed dated listings."}
          </p>
        </div>
        <RequestedEventsCard itinerary={itinerary} />
        <RequestedActivitiesCard itinerary={itinerary} />
        {itinerary.event_recommendations.length > 0 ? (
          <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
            {itinerary.event_recommendations.map((event) => (
              <div key={event.event_option_id} className="rounded-xl border border-gray-200 bg-white p-6">
                <ProviderImage
                  url={event.image_url}
                  alt={event.image_alt || event.name}
                  source={event.image_source}
                  fallback="from-fuchsia-700 via-violet-600 to-indigo-500"
                />
                <h3 className="mb-3 text-lg font-semibold text-gray-900">{event.name}</h3>
                <RecommendationFacts data={event} />
                <p className="mt-3 text-sm leading-6 text-gray-600">{event.description}</p>
                {event.ticket_url && (
                  <a className="mt-3 inline-flex text-sm font-semibold text-indigo-700 hover:text-indigo-900" href={event.ticket_url} target="_blank" rel="noreferrer">
                    Check official event page
                  </a>
                )}
              </div>
            ))}
          </div>
        ) : (
          <div className="rounded-2xl border border-dashed border-slate-300 bg-white p-6 text-sm text-slate-600">No matching event ideas were available for this plan.</div>
        )}
      </section>

      {itinerary.daily_outline.length > 0 && (
        <section id="daily-plan" className="scroll-mt-20 space-y-4">
          <div className="flex flex-wrap items-end justify-between gap-3">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.16em] text-indigo-600">Day by day</p>
              <h2 className="mt-1 text-2xl font-bold text-slate-950">A practical daily outline</h2>
            </div>
            {itinerary.daily_outline.length > 4 && (
              <button type="button" onClick={() => setShowAllDays((value) => !value)} className="rounded-xl border border-indigo-200 bg-white px-4 py-2 text-sm font-semibold text-indigo-700 hover:bg-indigo-50">
                {showAllDays ? "Show first 4 days" : `Show all ${itinerary.daily_outline.length} days`}
              </button>
            )}
          </div>
          <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
            {days.map((entry) => <DailyOutlineCard key={entry.day} entry={entry} />)}
          </div>
        </section>
      )}

      <section className="space-y-4">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-indigo-600">Explore more</p>
          <h2 className="mt-1 text-2xl font-bold text-slate-950">Keep discovering as you scroll</h2>
        </div>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {[
            ["Family dining", "Restaurant and food imagery will come from a verified dining source, never an invented venue.", "from-amber-600 via-orange-500 to-rose-400"],
            ["Places and attractions", "Requested places stay visible here while opening times and tickets are confirmed.", "from-emerald-700 via-teal-500 to-cyan-400"],
            ["Hotel neighbourhoods", "Compare the location and family fit before moving to a live room search.", "from-indigo-800 via-violet-600 to-fuchsia-400"],
          ].map(([title, description, colour]) => (
            <div key={title} className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
              <div className={`h-28 bg-gradient-to-br ${colour}`} />
              <div className="p-4">
                <h3 className="font-bold text-slate-950">{title}</h3>
                <p className="mt-2 text-sm leading-6 text-slate-600">{description}</p>
              </div>
            </div>
          ))}
        </div>
      </section>

      <section id="plan-details" className="scroll-mt-20 space-y-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-indigo-600">Transparency</p>
          <h2 className="mt-1 text-2xl font-bold text-slate-950">Checks and planning details</h2>
          <p className="mt-2 text-sm text-slate-500">Open these only when you want to inspect how the plan was produced.</p>
        </div>

        {itinerary.grounding_notices.length > 0 && (
          <details className="group rounded-2xl border border-slate-200 bg-white p-5">
            <summary className="cursor-pointer list-none font-semibold text-slate-900">What has been checked <span className="float-right text-slate-400 group-open:rotate-180">⌄</span></summary>
            <div className="mt-4 grid grid-cols-1 gap-3 lg:grid-cols-2">
              {itinerary.grounding_notices.map((notice) => <GroundingCard key={`${notice.domain}-${notice.data_source}`} notice={notice} />)}
            </div>
          </details>
        )}

        <details className="group rounded-2xl border border-slate-200 bg-white p-5">
          <summary className="cursor-pointer list-none font-semibold text-slate-900">Why this plan and confidence <span className="float-right text-slate-400 group-open:rotate-180">⌄</span></summary>
          <div className="mt-4 space-y-3 text-sm leading-6 text-slate-600">
            <p>{itinerary.confidence_explanation}</p>
            {itinerary.why_this_itinerary.map((item, index) => <p key={index}><span className="font-semibold capitalize text-slate-900">{fmtKey(item.module)}:</span> {item.driver}</p>)}
          </div>
        </details>

        {(itinerary.risks.length > 0 || itinerary.assumptions.length > 0) && (
          <details className="group rounded-2xl border border-amber-200 bg-amber-50 p-5">
            <summary className="cursor-pointer list-none font-semibold text-amber-900">Risks and assumptions <span className="float-right text-amber-500 group-open:rotate-180">⌄</span></summary>
            <div className="mt-4 grid gap-5 lg:grid-cols-2">
              <div>
                <p className="mb-2 text-sm font-semibold text-amber-900">Risks</p>
                <ul className="space-y-2">{itinerary.risks.map((item, index) => <li key={index} className="text-sm leading-5 text-amber-800">• {item}</li>)}</ul>
              </div>
              <div>
                <p className="mb-2 text-sm font-semibold text-amber-900">Assumptions</p>
                <ul className="space-y-2">{itinerary.assumptions.map((item, index) => <li key={index} className="text-sm leading-5 text-amber-800">• {item}</li>)}</ul>
              </div>
            </div>
          </details>
        )}
      </section>
    </div>
  );
}

export default function PlannerPage() {
  const { clerkEnabled, loaded, signedIn, getSessionToken } = useTralvanaAuth();
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<PlanTripResponse | null>(null);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [restoring, setRestoring] = useState(true);

  useEffect(() => {
    if (clerkEnabled && (!loaded || !signedIn)) return;
    let active = true;
    const restore = async () => {
      try {
        const token = clerkEnabled
          ? await getSessionToken() ?? undefined
          : undefined;
        const params = new URLSearchParams(window.location.search);
        const requestedConversation = params.get("conversation");
        const saved = requestedConversation
          ? await getSavedPlan(requestedConversation, token)
          : await getLatestSavedPlan(token);
        if (!active || !saved) return;
        setResult(saved);
        setConversationId(saved.conversation_id);
        if (!requestedConversation) {
          window.history.replaceState(
            null,
            "",
            `/planner?conversation=${encodeURIComponent(saved.conversation_id)}${saved.itinerary ? "#overview" : ""}`
          );
        }
      } catch (err: unknown) {
        if (active) {
          setError(err instanceof Error ? err.message : "Unable to restore your saved trip");
        }
      } finally {
        if (active) setRestoring(false);
      }
    };
    void restore();
    return () => { active = false; };
  }, [clerkEnabled, getSessionToken, loaded, signedIn]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!message.trim()) return;
    setLoading(true);
    setError(null);

    try {
      const response = await planTrip({
        message,
        ...(conversationId ? { conversation_id: conversationId } : {}),
      });
      setResult(response);
      setConversationId(response.conversation_id);
      setMessage("");
      window.history.replaceState(
        null,
        "",
        `/planner?conversation=${encodeURIComponent(response.conversation_id)}${response.itinerary ? "#overview" : ""}`
      );
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to plan your trip");
    } finally {
      setLoading(false);
    }
  };

  const startOver = () => {
    setMessage("");
    setError(null);
    setResult(null);
    setConversationId(null);
    window.history.replaceState(null, "", "/planner");
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const focusAnswer = () => {
    const question = result?.planning_readiness?.next_question;
    if (question) setMessage("");
    window.scrollTo({ top: 180, behavior: "smooth" });
    window.setTimeout(() => document.getElementById("trip-message")?.focus(), 350);
  };

  return (
    <main className="min-h-screen bg-slate-50 px-4 py-8 sm:px-6 sm:py-10">
      <div className="mx-auto max-w-6xl space-y-8">
        <div className="flex items-center justify-between gap-4">
          <Link href="/" className="text-xl font-bold tracking-tight text-slate-950">Tralvana <span className="text-indigo-600">AI</span></Link>
          <div className="flex items-center gap-4">
            <Link href="/my-trips" className="text-sm font-semibold text-slate-600 hover:text-indigo-700">My Trips</Link>
            {conversationId && (
              <button type="button" onClick={startOver} className="text-sm font-semibold text-indigo-700 hover:text-indigo-900">New trip</button>
            )}
          </div>
        </div>

        {restoring && (
          <div className="rounded-xl border border-indigo-100 bg-indigo-50 px-4 py-3 text-sm font-medium text-indigo-800">
            Restoring your latest saved trip…
          </div>
        )}

        <header className={result?.itinerary ? "sr-only" : "max-w-3xl"}>
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-indigo-600">One connected travel plan</p>
          <h1 className="mt-3 text-4xl font-bold tracking-tight text-slate-950 sm:text-5xl">Where would you like to go?</h1>
          <p className="mt-4 text-base leading-7 text-slate-600 sm:text-lg">
            Describe the complete trip in normal language. Include where you are leaving from,
            destination, dates, travellers, passport nationality, interests and an approximate budget.
          </p>
        </header>

        <form onSubmit={handleSubmit} className={`rounded-2xl border bg-white shadow-sm ${result?.itinerary ? "border-indigo-100 p-4" : "border-slate-200 p-5 sm:p-7"}`}>
          <div>
            <label className="mb-2 block text-sm font-semibold text-slate-800">
              {result?.planning_readiness?.next_question
                ? result.planning_readiness.next_question
                : conversationId ? "Refine this plan" : "Describe your trip"}
            </label>
            <textarea
              id="trip-message"
              className={`w-full resize-y rounded-xl border border-slate-300 px-4 py-3 text-sm leading-6 text-slate-900 outline-none transition placeholder:text-slate-400 focus:border-indigo-500 focus:ring-4 focus:ring-indigo-100 ${result?.itinerary ? "min-h-[76px]" : "min-h-[140px]"}`}
              placeholder={conversationId
                ? result?.planning_readiness?.next_question
                  ? "Type your answer here. Tralvana will keep the trip details you already supplied."
                  : "Change anything—for example: lower the budget, add two children, choose a quieter area, or include more African restaurants."
                : "Example: Plan a 7-day trip to New York from Manchester in September for 2 Irish adults. Our budget is £3,500 and we like food, culture, shopping and live sport."}
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              required
            />
          </div>
          {!conversationId && (
            <div className="mt-3 flex flex-wrap gap-2">
              {STARTER_PROMPTS.map((prompt) => (
                <button key={prompt.label} type="button" onClick={() => setMessage(prompt.value)} className="rounded-full border border-slate-200 bg-slate-50 px-3 py-2 text-xs font-semibold text-slate-600 hover:border-indigo-300 hover:bg-indigo-50 hover:text-indigo-700">
                  {prompt.label}
                </button>
              ))}
            </div>
          )}
          <button
            type="submit"
            disabled={loading}
            className="mt-4 w-full rounded-xl bg-indigo-600 py-3.5 text-sm font-bold text-white transition hover:bg-indigo-700 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {loading
              ? "Understanding and updating your trip…"
              : result?.planning_readiness?.next_question
                ? "Send My Answer"
                : conversationId ? "Update My Plan" : "Build My Trip"}
          </button>
          <p className="mt-3 text-center text-xs text-slate-400">Current results, estimates and general guidance are labelled clearly.</p>
        </form>

        {error && (
          <div className="rounded-lg bg-red-50 border border-red-200 p-4 text-red-700 text-sm">
            {error}
          </div>
        )}

        {result && !result.itinerary && (
          <div className="space-y-3 rounded-2xl border border-indigo-100 bg-white p-6 shadow-sm">
            <h2 className="text-lg font-bold text-slate-950">
              {result.missing_information.length > 0
                ? "A little more information is needed"
                : "Your Tralvana answer"}
            </h2>
            <p className="whitespace-pre-line text-sm leading-6 text-slate-700">{result.response.replaceAll("**", "")}</p>
            {result.planning_readiness?.next_question && (
              <div className="rounded-xl border border-cyan-200 bg-cyan-50 p-4">
                <p className="text-xs font-bold uppercase tracking-[0.14em] text-cyan-700">Next question</p>
                <p className="mt-2 text-sm font-semibold text-slate-950">{result.planning_readiness.next_question}</p>
              </div>
            )}
            {result.missing_information.length > 0 && (
              <ul className="space-y-2 rounded-xl bg-indigo-50 p-4">
                {result.missing_information.map((m, i) => (
                  <li key={i} className="text-sm font-medium text-indigo-900">• {m}</li>
                ))}
              </ul>
            )}
          </div>
        )}

        {result?.itinerary && (
          <ItineraryView
            itinerary={result.itinerary}
            readiness={result.planning_readiness}
            onAnswer={focusAnswer}
            onStartOver={startOver}
          />
        )}
      </div>
    </main>
  );
}

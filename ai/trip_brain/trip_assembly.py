"""
Trip Assembly Engine (T-040) — synthesizes Trip Brain's already-computed
UnifiedRecommendation into one coherent, consultant-style TripItinerary.

Trip Brain (ai/trip_brain/coordinator.py) remains the sole orchestrator
of the selected Discovery modules. This
module never re-scores, re-ranks, or recalculates anything a Discovery
module, Trip Brain, or the Explainability Engine already produced; it
only reads fields already computed (AgentResult.data's `top_option`,
UnifiedRecommendation.explanation) and assembles them into the shape
docs/AI_TRAVEL_PLANNER.md's Definition of Done requires.

Two things are genuinely new here, both compositional, neither a new
scoring model:

1. **Daily outline** — built by the pre-existing
   ai/planning/itinerary_builder.py (T-008, Sprint 1's deterministic
   goal-type-templated day planner), called here, never duplicated.
2. **Executive summary** — a natural-language paragraph assembled from
   facts each module already decided (destination, flight, property,
   budget tier, visa outcome, weather fit), not a new judgement about
   which one to prefer. Every clause is conditional on the fact it
   quotes actually being present — nothing is invented when a module
   didn't run or came back empty.

Deliberately NOT called from ai/trip_brain/coordinator.py — TripBrain.plan()
is unchanged. This is a second, separate caller of Trip Brain's output,
the same relationship ai/concierge/conversation_engine.py already has
with it (see services/api/app/routers/planner.py, T-040's one new call
site).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Any

from ai.planning.itinerary_builder import itinerary_builder
from ai.shared.agent_result import AgentResult
from ai.shared.agent_status import AgentStatus
from ai.trip_brain.models import UnifiedRecommendation


@dataclass
class GroundingNotice:
    """Public, provider-neutral description of how current a planner fact is.

    The planner must never make a mock estimate, sandbox response, static
    guidance rule, climate profile, or generic activity idea look like live
    availability.  These values are deliberately presentation facts rather
    than confidence scores: they describe provenance and the action the
    traveller still needs to take.
    """

    domain: str
    level: str
    title: str
    message: str
    data_source: str
    is_current: bool
    requires_confirmation: bool
    retrieved_at: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "domain": self.domain,
            "level": self.level,
            "title": self.title,
            "message": self.message,
            "data_source": self.data_source,
            "is_current": self.is_current,
            "requires_confirmation": self.requires_confirmation,
            "retrieved_at": self.retrieved_at,
        }


@dataclass
class TripItinerary:
    executive_summary: str
    trip_brief: dict[str, Any]
    booking_readiness: dict[str, Any]
    destination_recommendation: dict[str, Any] | None
    flight_recommendation: dict[str, Any] | None
    accommodation_recommendation: dict[str, Any] | None
    budget_summary: dict[str, Any] | None
    visa_summary: dict[str, Any] | None
    weather_expectations: dict[str, Any] | None
    event_recommendations: list[dict[str, Any]]
    risks: list[str]
    assumptions: list[str]
    daily_outline: list[dict[str, Any]]
    why_this_itinerary: list[dict[str, str]]
    confidence: float
    confidence_explanation: str
    alternative_options: list[dict[str, Any]]
    grounding_notices: list[GroundingNotice] = field(default_factory=list)
    modules_used: list[str] = field(default_factory=list)
    modules_unavailable: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "executive_summary": self.executive_summary,
            "trip_brief": self.trip_brief,
            "booking_readiness": self.booking_readiness,
            "destination_recommendation": self.destination_recommendation,
            "flight_recommendation": self.flight_recommendation,
            "accommodation_recommendation": self.accommodation_recommendation,
            "budget_summary": self.budget_summary,
            "visa_summary": self.visa_summary,
            "weather_expectations": self.weather_expectations,
            "event_recommendations": self.event_recommendations,
            "risks": self.risks,
            "assumptions": self.assumptions,
            "daily_outline": self.daily_outline,
            "why_this_itinerary": self.why_this_itinerary,
            "confidence": self.confidence,
            "confidence_explanation": self.confidence_explanation,
            "alternative_options": self.alternative_options,
            "grounding_notices": [notice.to_dict() for notice in self.grounding_notices],
            "modules_used": self.modules_used,
            "modules_unavailable": self.modules_unavailable,
        }


# AgentResult.agent_name -> the itinerary section it feeds, matching
# ai/trip_brain/discovery_adapters.py's MODULE_RUNNERS naming exactly.
class TripAssemblyEngine:
    def assemble(
        self,
        unified: UnifiedRecommendation,
        destination: str,
        duration_days: int,
        goal_type: str = "GENERAL_TRAVEL",
        budget_style: str = "balanced",
        interests: list[str] | None = None,
        trip_brief: dict[str, Any] | None = None,
    ) -> TripItinerary:
        by_module = {r.agent_name: r for r in unified.results}

        destination_rec = self._top_option(by_module.get("destination_intelligence"))
        raw_flight_rec = self._top_option(by_module.get("flight_intelligence"))
        raw_accommodation_rec = self._top_option(
            by_module.get("accommodation_intelligence")
        )
        flight_rec = self._current_provider_option(raw_flight_rec)
        accommodation_rec = self._current_provider_option(raw_accommodation_rec)
        brief = self._normalise_trip_brief(
            trip_brief,
            destination=destination,
            duration_days=duration_days,
            interests=interests or [],
        )
        budget_rec = self._declared_budget_summary(brief)
        visa_rec = self._assessment(by_module.get("visa_intelligence"))
        weather_rec = self._assessment(by_module.get("weather_intelligence"))
        event_result = by_module.get("event_intelligence")
        event_recs = self._options(event_result)
        event_evidence = (
            event_result.data
            if event_result is not None
            and event_result.status != AgentStatus.FAILED
            else {}
        )

        daily_outline = itinerary_builder.build(
            destination=destination or "your destination",
            duration_days=max(int(duration_days or 1), 1),
            goal_type=goal_type or "GENERAL_TRAVEL",
            budget_style=budget_style or "balanced",
            interests=interests,
        )
        daily_outline = self._apply_trip_specific_details(daily_outline, brief)

        booking_readiness = self._booking_readiness(
            brief=brief,
            flight=flight_rec,
            accommodation=accommodation_rec,
            events=event_recs,
        )

        executive_summary = self._executive_summary(
            brief=brief,
            flight=flight_rec,
            accommodation=accommodation_rec,
            budget=budget_rec,
            visa=visa_rec,
            weather=weather_rec,
            events=event_recs,
            confidence=unified.overall_confidence,
            modules_succeeded=unified.modules_succeeded,
            readiness=booking_readiness,
        )
        grounding_notices = self._grounding_notices(
            destination=destination_rec,
            flight=flight_rec,
            accommodation=accommodation_rec,
            budget=budget_rec,
            visa=visa_rec,
            weather=weather_rec,
            events=event_recs,
            event_evidence=event_evidence,
            interests=interests or [],
            brief=brief,
        )

        return TripItinerary(
            executive_summary=executive_summary,
            trip_brief=brief,
            booking_readiness=booking_readiness,
            destination_recommendation=destination_rec,
            flight_recommendation=flight_rec,
            accommodation_recommendation=accommodation_rec,
            budget_summary=budget_rec,
            visa_summary=visa_rec,
            weather_expectations=weather_rec,
            event_recommendations=event_recs,
            risks=self._coherent_risks(
                brief=brief,
                visa=visa_rec,
                weather=weather_rec,
                events=event_recs,
                flight=flight_rec,
                accommodation=accommodation_rec,
            ),
            assumptions=self._coherent_assumptions(
                brief=brief,
                flight=flight_rec,
                accommodation=accommodation_rec,
            ),
            daily_outline=daily_outline,
            why_this_itinerary=self._coherent_drivers(
                brief=brief,
                weather=weather_rec,
                events=event_recs,
            ),
            confidence=min(
                unified.overall_confidence,
                booking_readiness["score"] / 100,
            ),
            confidence_explanation=booking_readiness["explanation"],
            alternative_options=[],
            grounding_notices=grounding_notices,
            modules_used=list(unified.modules_succeeded),
            modules_unavailable=list(unified.modules_failed),
        )

    # ------------------------------------------------------------------

    def _presentation_drivers(
        self,
        explanation: dict[str, Any],
        *,
        flight: dict[str, Any] | None,
        accommodation: dict[str, Any] | None,
        budget: dict[str, Any] | None,
    ) -> list[dict[str, str]]:
        """Prevent an independent regional budget baseline from reading as
        though it reconciles to separately generated mock supplier options.

        Until live provider prices and FX conversion are connected, the
        regional model and selected mock options are different evidence
        sources.  Keep every non-budget driver unchanged; replace only a
        conflicting budget breakdown with an explicit provenance statement.
        """
        drivers = [
            dict(driver)
            for driver in explanation.get("recommendation_drivers", [])
        ]
        if not budget:
            return drivers

        currency = budget.get("currency")
        flight_conflicts = (
            flight is not None
            and currency == flight.get("currency")
            and budget.get("flight_cost_usd") is not None
            and flight.get("estimated_price") is not None
            and budget["flight_cost_usd"] != flight["estimated_price"]
        )
        accommodation_conflicts = (
            accommodation is not None
            and currency == accommodation.get("currency")
            and budget.get("accommodation_usd") is not None
            and accommodation.get("total_price") is not None
            and budget["accommodation_usd"] != accommodation["total_price"]
        )
        if not (flight_conflicts or accommodation_conflicts):
            return drivers

        replacement = {
            "module": "budget_intelligence",
            "driver": (
                f"The {str(budget.get('budget_style', 'selected')).title()} budget "
                f"is a static regional planning baseline in {currency or 'USD'}. "
                "It is not a reconciled quote; recalculate it with live flight, "
                "accommodation, and exchange-rate data before booking."
            ),
        }
        for index, driver in enumerate(drivers):
            if driver.get("module") == "budget_intelligence":
                drivers[index] = replacement
                break
        else:
            drivers.append(replacement)
        return drivers

    def _top_option(self, result: AgentResult | None) -> dict[str, Any] | None:
        """The module's own already-labelled BEST_OVERALL pick
        (ai/trip_brain/discovery_adapters.py's `_top_option()`,
        computed once, reused here verbatim) — never recomputed."""
        if result is None or result.status == AgentStatus.FAILED:
            return None
        top = result.data.get("top_option")
        return top or None

    def _current_provider_option(
        self, option: dict[str, Any] | None
    ) -> dict[str, Any] | None:
        if not option:
            return None
        source = str(option.get("data_source", "")).upper()
        return option if self._is_live_source(source) else None

    def _normalise_trip_brief(
        self,
        brief: dict[str, Any] | None,
        *,
        destination: str,
        duration_days: int,
        interests: list[str],
    ) -> dict[str, Any]:
        value = dict(brief or {})
        value.setdefault("origin", "")
        value.setdefault("departure_options", [])
        value.setdefault("destination", destination)
        value.setdefault("local_areas", [])
        value.setdefault("duration_days", max(int(duration_days or 1), 1))
        value.setdefault("start_date", None)
        value.setdefault("end_date", None)
        value.setdefault("month", None)
        value.setdefault("year", None)
        value.setdefault(
            "date_precision",
            "EXACT"
            if value.get("start_date") and value.get("end_date")
            else "UNSPECIFIED",
        )
        value.setdefault("travel_period", "Dates not supplied")
        value.setdefault(
            "travellers", {"adults": 1, "children": 0, "infants": 0}
        )
        value.setdefault("budget", {})
        value.setdefault("nationality", None)
        value.setdefault("interests", list(interests))
        value.setdefault("stay_plan", [])
        value.setdefault("special_occasion", None)
        value.setdefault("companion_plan", None)
        return value

    def _apply_trip_specific_details(
        self,
        outline: list[dict[str, Any]],
        brief: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Carry traveller-declared stay changes and dated occasions into
        the daily outline without implying that any property is booked."""
        try:
            trip_start = date.fromisoformat(str(brief.get("start_date")))
        except (TypeError, ValueError):
            trip_start = None

        occasion = brief.get("special_occasion") or {}
        occasion_date = occasion.get("date")
        for entry in outline:
            day_date = (
                trip_start + timedelta(days=int(entry["day"]) - 1)
                if trip_start
                else None
            )
            for stay in brief.get("stay_plan") or []:
                try:
                    stay_start = date.fromisoformat(str(stay.get("start_date")))
                    stay_end = date.fromisoformat(str(stay.get("end_date")))
                except (TypeError, ValueError):
                    continue
                if day_date and stay_start <= day_date < stay_end:
                    description = stay.get("property_name") or stay.get("style")
                    area = stay.get("area")
                    if description:
                        entry["accommodation"] = (
                            f"{description}{f' in {area}' if area else ''} — requested, not booked"
                        )
                    break

            if day_date and occasion_date == day_date.isoformat():
                occasion_type = occasion.get("type") or "Special occasion"
                notes = occasion.get("notes")
                entry["title"] = f"Day {entry['day']}: {occasion_type} celebration"
                if notes:
                    entry["evening"] = notes
                entry["notes"] = (
                    f"{entry.get('notes', '')} Confirm the celebration venue and reservations."
                ).strip()
        return outline

    def _declared_budget_summary(
        self, brief: dict[str, Any]
    ) -> dict[str, Any] | None:
        budget = brief.get("budget") or {}
        amount = budget.get("amount")
        if amount is None:
            return None
        currency = str(budget.get("currency") or "USD").upper()
        allocations = {
            "transport_allocation": 0.35,
            "accommodation_allocation": 0.35,
            "food_allocation": 0.15,
            "activities_allocation": 0.10,
            "contingency_allocation": 0.05,
        }
        return {
            "declared_budget": amount,
            "currency": currency,
            "duration_days": brief["duration_days"],
            "adults": brief["travellers"].get("adults", 1),
            "children": brief["travellers"].get("children", 0),
            "assessment_status": "NOT_YET_ASSESSED",
            "affordability_status": "UNKNOWN_UNTIL_LIVE_PRICES",
            **{
                key: round(float(amount) * share)
                for key, share in allocations.items()
            },
            "allocation_basis": (
                "Suggested allocation of the traveller's stated budget; "
                "these values are not price estimates."
            ),
            "data_source": "TRAVELLER_DECLARED_BUDGET",
        }

    def _booking_readiness(
        self,
        *,
        brief: dict[str, Any],
        flight: dict[str, Any] | None,
        accommodation: dict[str, Any] | None,
        events: list[dict[str, Any]],
    ) -> dict[str, Any]:
        score = 0
        score += 10 if brief.get("destination") else 0
        score += 10 if brief.get("origin") else 0
        score += 10 if brief.get("duration_days") else 0
        score += 10 if brief.get("travellers", {}).get("adults") else 0
        score += 5 if brief.get("travel_period") != "Dates not supplied" else 0
        score += 5 if (brief.get("budget") or {}).get("amount") is not None else 0
        score += 5 if brief.get("interests") else 0
        score += 15 if brief.get("date_precision") == "EXACT" else 0
        score += 10 if brief.get("nationality") else 0
        score += 10 if flight else 0
        score += 10 if accommodation else 0
        score = min(score, 100)

        needed: list[str] = []
        if brief.get("date_precision") != "EXACT":
            needed.append("Choose exact departure and return dates.")
        if not brief.get("nationality"):
            needed.append(
                "Add each traveller's passport nationality for official entry checks."
            )
        if not flight or not accommodation:
            needed.append(
                "Run current flight and accommodation searches, then reconcile the prices."
            )
        companion = brief.get("companion_plan") or {}
        if companion and (
            not companion.get("arrival_date") or not companion.get("departure_date")
        ):
            needed.append(
                f"Add your companion's {brief.get('destination') or 'destination'} "
                "arrival and departure dates before booking shared accommodation."
            )
        if self._has_event_interest(brief.get("interests", [])) and not any(
            event.get("data_source") == "TICKETMASTER_DISCOVERY_API"
            for event in events
        ):
            needed.append(
                "Confirm any football match or event on an official dated calendar."
            )

        label = (
            "BOOKING_READY"
            if score == 100 and not needed
            else "PLANNING_IN_PROGRESS"
        )
        return {
            "score": score,
            "status": label,
            "items_needed": needed,
            "budget_status": (
                "NOT_YET_ASSESSED"
                if (brief.get("budget") or {}).get("amount") is not None
                else "BUDGET_NOT_PROVIDED"
            ),
            "explanation": (
                f"{score}% planning readiness. "
                + (
                    "The itinerary is ready for final booking checks."
                    if not needed
                    else "Complete the listed checks before treating this as a bookable trip."
                )
            ),
        }

    def _coherent_risks(
        self,
        *,
        brief: dict[str, Any],
        visa: dict[str, Any] | None,
        weather: dict[str, Any] | None,
        events: list[dict[str, Any]],
        flight: dict[str, Any] | None,
        accommodation: dict[str, Any] | None,
    ) -> list[str]:
        risks: list[str] = []
        if brief.get("date_precision") != "EXACT":
            risks.append(
                "Exact travel dates are not set, so availability and bookable prices cannot be checked."
            )
        if not flight or not accommodation:
            risks.append(
                "No reconciled current flight and accommodation prices are included."
            )
        if (brief.get("budget") or {}).get("amount") is not None:
            risks.append(
                "The stated budget has not yet been tested against current supplier prices."
            )
        else:
            risks.append("No total trip budget has been supplied.")

        if weather:
            risks.extend(str(item) for item in weather.get("risks", []))
        if visa:
            risks.extend(str(item) for item in visa.get("risks", []))
        if self._has_event_interest(brief.get("interests", [])) and not any(
            event.get("data_source") == "TICKETMASTER_DISCOVERY_API"
            for event in events
        ):
            risks.append(
                "Football fixtures and other events are ideas until an official dated listing is confirmed."
            )
        return list(dict.fromkeys(item for item in risks if item))

    def _coherent_assumptions(
        self,
        *,
        brief: dict[str, Any],
        flight: dict[str, Any] | None,
        accommodation: dict[str, Any] | None,
    ) -> list[str]:
        assumptions = [
            "Daily activities are a curated planning outline; opening hours and availability still require checking."
        ]
        if brief.get("date_precision") == "MONTH":
            assumptions.append(
                f"{brief.get('travel_period')} is treated as a broad travel window, not an exact booking date."
            )
        if not flight:
            assumptions.append(
                f"The departure point remains {brief.get('origin') or 'to be confirmed'}; no substitute airport was selected."
            )
        if not accommodation and brief.get("stay_plan"):
            assumptions.append(
                "The requested two-stage stay is preserved, but neither property nor rate is confirmed."
            )
        elif not accommodation:
            assumptions.append(
                "Accommodation remains unselected until a current provider search is completed."
            )
        return assumptions

    def _coherent_drivers(
        self,
        *,
        brief: dict[str, Any],
        weather: dict[str, Any] | None,
        events: list[dict[str, Any]],
    ) -> list[dict[str, str]]:
        drivers = [
            {
                "module": "canonical_trip_brief",
                "driver": (
                    f"The outline preserves {brief.get('duration_days')} days, "
                    f"{brief.get('origin') or 'the stated origin'}, "
                    f"{brief.get('travel_period')}, and the supplied party size."
                ),
            }
        ]
        if brief.get("interests"):
            drivers.append(
                {
                    "module": "traveller_interests",
                    "driver": (
                        "Activities are shaped around "
                        + ", ".join(str(item) for item in brief["interests"])
                        + " without inventing confirmed fixtures or tickets."
                    ),
                }
            )
        if weather:
            drivers.append(
                {
                    "module": "weather_intelligence",
                    "driver": (
                        f"The seasonal profile reports {weather.get('season', 'the selected season')} "
                        f"with a {str(weather.get('weather_status', 'unknown')).lower()} suitability status."
                    ),
                }
            )
        if events:
            drivers.append(
                {
                    "module": "event_intelligence",
                    "driver": (
                        "Only event results matching the destination and requested interests are retained."
                    ),
                }
            )
        return drivers

    def _assessment(self, result: AgentResult | None) -> dict[str, Any] | None:
        """Visa/Weather Intelligence's single-assessment shape (not a
        ranked list) — the whole `data` dict, unchanged."""
        if result is None or result.status == AgentStatus.FAILED:
            return None
        return result.data or None

    def _options(self, result: AgentResult | None) -> list[dict[str, Any]]:
        """A ranked module's already-computed public options, unchanged."""
        if result is None or result.status == AgentStatus.FAILED:
            return []
        return list(result.data.get("options", []))

    def _executive_summary(
        self,
        brief: dict[str, Any],
        flight: dict[str, Any] | None,
        accommodation: dict[str, Any] | None,
        budget: dict[str, Any] | None,
        visa: dict[str, Any] | None,
        weather: dict[str, Any] | None,
        events: list[dict[str, Any]],
        confidence: float,
        modules_succeeded: list[str],
        readiness: dict[str, Any],
    ) -> str:
        """A natural-language paragraph over facts already decided by
        each module — every clause only appears if the fact it quotes
        is actually present; nothing here is invented or re-derived."""
        if not modules_succeeded:
            return "I wasn't able to put together a recommendation yet — let's gather a bit more detail first."

        destination = brief.get("destination") or "this trip"
        origin = brief.get("origin")
        travellers = brief.get("travellers", {})
        party = travellers.get("adults", 1)
        children = travellers.get("children", 0)
        party_text = f"{party} adult{'s' if party != 1 else ''}"
        if children:
            party_text += f" and {children} child{'ren' if children != 1 else ''}"
        parts = [
            f"This is a {brief.get('duration_days')}-day planning outline for "
            f"{destination}"
            + (f" from {origin}" if origin else "")
            + f" during {brief.get('travel_period')} for {party_text}."
        ]

        departure_options = brief.get("departure_options") or []
        if len(departure_options) > 1:
            parts.append(
                "The outbound flight search should compare "
                + " and ".join(str(value) for value in departure_options)
                + "."
            )

        stay_plan = brief.get("stay_plan") or []
        if stay_plan:
            stays: list[str] = []
            for stay in stay_plan:
                description = stay.get("property_name") or stay.get("style")
                if not description:
                    continue
                area = stay.get("area")
                dates = (
                    f"{stay.get('start_date')} to {stay.get('end_date')}"
                    if stay.get("start_date") and stay.get("end_date")
                    else "dates to be confirmed"
                )
                stays.append(
                    f"{description}{f' in {area}' if area else ''} ({dates})"
                )
            if stays:
                parts.append(
                    "The requested stay sequence is "
                    + ", followed by ".join(stays)
                    + "; live availability and prices still need checking."
                )

        occasion = brief.get("special_occasion") or {}
        if occasion.get("type"):
            parts.append(
                f"The {occasion['type'].lower()} on {occasion.get('date') or 'the stated date'} "
                "is included in the daily plan."
            )

        companion = brief.get("companion_plan") or {}
        if companion.get("origin"):
            relationship = str(companion.get("relationship") or "companion").lower()
            parts.append(
                f"Your {relationship}'s separate journey from {companion['origin']} is kept separate "
                "from your flight; their exact dates are still needed for shared bookings."
            )

        if flight:
            airline = flight.get("airline")
            price = flight.get("estimated_price")
            currency = flight.get("currency", "")
            if airline and price is not None:
                source = str(flight.get("data_source", "MOCK")).upper()
                if self._is_live_source(source):
                    parts.append(
                        f"A current provider search found {airline} at {currency} {price}; "
                        "recheck availability before booking."
                    )
                elif self._is_sandbox_source(source):
                    parts.append(
                        f"Duffel sandbox test data returned {airline} at {currency} {price}; "
                        "this is not a purchasable fare."
                    )
                else:
                    parts.append(
                        f"A planning estimate uses {airline} at around {currency} {price}; "
                        "check a live provider before booking."
                    )

        if accommodation:
            name = accommodation.get("property_name")
            acc_type = str(accommodation.get("accommodation_type", "")).replace("_", " ").lower()
            if name:
                stay_desc = f"a {acc_type}" if acc_type else "a property"
                source = str(accommodation.get("data_source", "MOCK")).upper()
                if self._is_live_source(source):
                    parts.append(
                        f"A current provider search found {name}, {stay_desc}; "
                        "recheck the rate and availability before booking."
                    )
                elif self._is_sandbox_source(source):
                    parts.append(
                        f"Duffel Stays sandbox test data returned {name}, {stay_desc}; "
                        "it is not available to book from this result."
                    )
                else:
                    parts.append(
                        f"The plan uses {name}, {stay_desc}, as an indicative stay; "
                        "check live rates and availability before booking."
                    )

        if budget:
            parts.append(
                f"The stated {budget['currency']} {budget['declared_budget']:,} "
                "budget is preserved, but affordability has not been assessed "
                "against current prices."
            )

        if visa and visa.get("visa_status"):
            visa_status = str(visa.get("visa_status", "")).upper()
            if visa_status == "CHECK_MANUALLY":
                parts.append(
                    "Entry requirements could not be determined from the available "
                    "guidance; check the official authority before travel."
                )
            elif visa.get("travel_authorisation_required"):
                authorisation = visa.get("visa_type", "travel authorisation")
                parts.append(
                    f"Planning guidance indicates {authorisation} travel authorisation is "
                    "required before departure; verify this with the official authority."
                )
            elif visa.get("visa_required"):
                parts.append(
                    "Planning guidance indicates a visa is required for this trip "
                    f"({visa.get('visa_type', 'see visa summary')}); verify this with "
                    "the official authority."
                )
            elif visa_status in {"VISA_NOT_REQUIRED", "NOT_REQUIRED"}:
                parts.append(
                    "Planning guidance indicates no visa is required for this trip; "
                    "verify this with the official authority."
                )

        if weather and weather.get("recommendation"):
            parts.append(f"Seasonal weather profile: {weather['recommendation']}")

        if events:
            matched = [
                option["name"]
                for option in events
                if option.get("interests_matched")
            ]
            if matched:
                parts.append(
                    "Curated event ideas include "
                    + ", ".join(matched[:2])
                    + "; confirm exact dates and availability with official live sources."
                )

        del confidence
        parts.append(
            f"Planning readiness is {readiness['score']}%; this is not a "
            "booking confirmation."
        )
        return " ".join(parts)

    # ------------------------------------------------------------------

    def _grounding_notices(
        self,
        destination: dict[str, Any] | None,
        flight: dict[str, Any] | None,
        accommodation: dict[str, Any] | None,
        budget: dict[str, Any] | None,
        visa: dict[str, Any] | None,
        weather: dict[str, Any] | None,
        events: list[dict[str, Any]],
        event_evidence: dict[str, Any],
        interests: list[str],
        brief: dict[str, Any],
    ) -> list[GroundingNotice]:
        notices: list[GroundingNotice] = []

        if destination:
            notices.append(
                GroundingNotice(
                    domain="destination",
                    level="CURATED",
                    title="Curated destination guidance",
                    message=(
                        "Destination suggestions come from Tralvana's curated catalogue, "
                        "not a live places or opening-hours search."
                    ),
                    data_source=str(destination.get("data_source", "TRALVANA_CURATED")),
                    is_current=False,
                    requires_confirmation=True,
                )
            )

        if flight:
            notices.append(self._provider_notice("flight", flight))
        else:
            notices.append(
                GroundingNotice(
                    domain="flight",
                    level="GUIDANCE",
                    title="Current flight search pending",
                    message=(
                        "No airline, flight number, or fare is shown because a current "
                        "bookable provider result is not available."
                    ),
                    data_source="NO_CURRENT_BOOKABLE_RESULT",
                    is_current=False,
                    requires_confirmation=True,
                )
            )

        if accommodation:
            notices.append(self._provider_notice("accommodation", accommodation))
        else:
            notices.append(
                GroundingNotice(
                    domain="accommodation",
                    level="GUIDANCE",
                    title="Current accommodation search pending",
                    message=(
                        "No property or price is shown because a current bookable "
                        "provider result is not available."
                    ),
                    data_source="NO_CURRENT_BOOKABLE_RESULT",
                    is_current=False,
                    requires_confirmation=True,
                )
            )

        if budget:
            notices.append(
                GroundingNotice(
                    domain="budget",
                    level="ESTIMATE",
                    title="Traveller budget allocation",
                    message=(
                        f"The {budget['currency']} figures divide the traveller's own "
                        "stated budget into planning envelopes. They are not supplier "
                        "prices and affordability remains unassessed."
                    ),
                    data_source=str(
                        budget.get("data_source", "TRAVELLER_DECLARED_BUDGET")
                    ),
                    is_current=False,
                    requires_confirmation=True,
                )
            )
        elif not (brief.get("budget") or {}).get("amount"):
            notices.append(
                GroundingNotice(
                    domain="budget",
                    level="GUIDANCE",
                    title="Budget required",
                    message=(
                        "No total budget was supplied, so the plan does not claim "
                        "that the trip is affordable."
                    ),
                    data_source="NO_TRAVELLER_BUDGET",
                    is_current=False,
                    requires_confirmation=True,
                )
            )

        if visa:
            notices.append(
                GroundingNotice(
                    domain="visa",
                    level="GUIDANCE",
                    title="Entry guidance—not legal advice",
                    message=(
                        "Entry guidance comes from Tralvana's general rule set, not a live "
                        "government, embassy, or Timatic check. Verify it officially before travel."
                    ),
                    data_source=str(visa.get("data_source", "TRALVANA_GENERAL_RULES")),
                    is_current=False,
                    requires_confirmation=True,
                )
            )

        if weather:
            notices.append(
                GroundingNotice(
                    domain="weather",
                    level="CLIMATE_PROFILE",
                    title="Seasonal profile—not a forecast",
                    message=(
                        "Weather guidance is based on a general seasonal climate profile, "
                        "not a current forecast or live safety alert."
                    ),
                    data_source=str(weather.get("data_source", "TRALVANA_CLIMATE_PROFILE")),
                    is_current=False,
                    requires_confirmation=True,
                )
            )

        if events:
            source = str(
                events[0].get("data_source", "TRALVANA_CURATED_EVENT_IDEAS")
            )
            retrieved_at = events[0].get("retrieved_at")
            live = source == "TICKETMASTER_DISCOVERY_API"
            notices.append(
                GroundingNotice(
                    domain="events",
                    level="LIVE" if live else "CURATED",
                    title=(
                        "Live event listings"
                        if live
                        else "Curated event search ideas"
                    ),
                    message=(
                        "Event dates and public links were retrieved from "
                        "Ticketmaster Discovery API. Ticket inventory, pricing, "
                        "and final event status must still be confirmed."
                        if live
                        else (
                            "Event Intelligence matched the traveller's interests to "
                            "curated search ideas. It did not confirm a live calendar, "
                            "fixture, ticket, price, or availability."
                        )
                    ),
                    data_source=source,
                    is_current=live,
                    requires_confirmation=True,
                    retrieved_at=str(retrieved_at) if retrieved_at else None,
                )
            )
        elif (
            event_evidence.get("data_source") == "TICKETMASTER_DISCOVERY_API"
            and event_evidence.get("provider_status") == "AVAILABLE"
        ):
            retrieved_at = event_evidence.get("retrieved_at")
            notices.append(
                GroundingNotice(
                    domain="events",
                    level="LIVE",
                    title="Live event search completed",
                    message=(
                        "Ticketmaster Discovery API was checked for the destination "
                        "and travel dates but returned no matching listings. Generic "
                        "activities remain ideas rather than confirmed events."
                    ),
                    data_source="TICKETMASTER_DISCOVERY_API",
                    is_current=True,
                    requires_confirmation=True,
                    retrieved_at=str(retrieved_at) if retrieved_at else None,
                )
            )
        elif self._has_event_interest(interests):
            notices.append(
                GroundingNotice(
                    domain="events",
                    level="IDEA",
                    title="Event ideas require confirmation",
                    message=(
                        "Fashion and football activities in the daily outline remain "
                        "planning ideas because Event Intelligence did not return a "
                        "usable current listing for the trip."
                    ),
                    data_source="NO_CONFIRMED_EVENT_RESULT",
                    is_current=False,
                    requires_confirmation=True,
                )
            )

        return notices

    def _provider_notice(
        self, domain: str, recommendation: dict[str, Any]
    ) -> GroundingNotice:
        source = str(recommendation.get("data_source", "MOCK")).upper()
        retrieved_at = recommendation.get("retrieved_at")
        label = "Flight" if domain == "flight" else "Accommodation"

        if self._is_live_source(source):
            return GroundingNotice(
                domain=domain,
                level="LIVE",
                title=f"Current {label.lower()} provider result",
                message=(
                    f"{label} data came from a live provider search. Prices and "
                    "availability can still change before booking."
                ),
                data_source=source,
                is_current=True,
                requires_confirmation=True,
                retrieved_at=str(retrieved_at) if retrieved_at else None,
            )

        if self._is_sandbox_source(source):
            return GroundingNotice(
                domain=domain,
                level="SANDBOX",
                title=f"{label} sandbox test data",
                message=(
                    f"{label} results came from a provider's sandbox environment. "
                    "They demonstrate the integration but are not available to purchase."
                ),
                data_source=source,
                is_current=False,
                requires_confirmation=True,
                retrieved_at=str(retrieved_at) if retrieved_at else None,
            )

        fallback = source == "MOCK_FALLBACK"
        return GroundingNotice(
            domain=domain,
            level="ESTIMATE",
            title=f"Estimated {label.lower()} result",
            message=(
                f"{label} data is deterministic mock planning data"
                + (" used after a provider failure" if fallback else "")
                + ", not live inventory or a bookable quote."
            ),
            data_source=source,
            is_current=False,
            requires_confirmation=True,
            retrieved_at=str(retrieved_at) if retrieved_at else None,
        )

    @staticmethod
    def _is_live_source(source: str) -> bool:
        """Only explicit production-shaped labels can be called current.

        Unknown or future provider labels fail closed to ESTIMATE in
        `_provider_notice`; a provider cannot become "live" merely because
        its name contains a vendor brand.
        """
        return source in {"LIVE", "LIVE_PROVIDER", "PRODUCTION", "PRODUCTION_PROVIDER"}

    @staticmethod
    def _is_sandbox_source(source: str) -> bool:
        return "SANDBOX" in source

    @staticmethod
    def _has_event_interest(interests: list[str]) -> bool:
        return any(
            term in str(interest).lower()
            for interest in interests
            for term in (
                "fashion", "style", "football", "soccer", "match", "event",
                "concert", "festival", "music", "theatre", "theater",
            )
        )


trip_assembly_engine = TripAssemblyEngine()

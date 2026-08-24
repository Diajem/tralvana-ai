"""OpenAI-backed interpretation and itinerary adaptation for Tralvana.

The model is deliberately kept behind the existing deterministic planning
boundary.  It extracts and organises what the traveller said, then adapts the
day-by-day outline.  Supplier availability, prices, visa rules, weather data,
and booking claims remain owned by the existing grounded modules.
"""

from __future__ import annotations

import json
import logging
import os
import re
from datetime import date, datetime, timedelta
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from ai.concierge.conversation_session import ConversationMessage
from ai.concierge.intent_classifier import ClassifiedIntent, Intent


logger = logging.getLogger(__name__)


class TripInterpretation(BaseModel):
    """Strict, typed result of interpreting one conversational trip turn."""

    model_config = ConfigDict(extra="forbid")

    intent: Literal[
        "PLAN_TRIP",
        "MODIFY_TRIP",
        "FLIGHT_SEARCH",
        "ACCOMMODATION_SEARCH",
        "DESTINATION_DISCOVERY",
        "BUDGET_ANALYSIS",
        "VISA_CHECK",
        "WEATHER_ANALYSIS",
        "DESTINATION_QUESTION",
        "TRAVEL_ADVICE",
        "BUDGET_ADVICE",
        "GENERAL_CONVERSATION",
    ]
    confidence: float = Field(ge=0, le=1)
    destination: str | None
    destination_region: str | None
    origin: str | None
    departure_options: list[str]
    airport_preference: str | None = None
    airline_preferences: list[str] = Field(default_factory=list)
    country_of_residence: str | None = None
    residency_documents: list[str] = Field(default_factory=list)
    local_areas: list[str]
    start_date: str | None
    end_date: str | None
    duration_days: int | None = Field(ge=1, le=180)
    month: int | None = Field(ge=1, le=12)
    travel_year: int | None = Field(ge=2020, le=2100)
    departure_day: int | None = Field(ge=1, le=31)
    year_explicit: bool
    adults: int | None = Field(ge=1, le=50)
    children: int | None = Field(ge=0, le=50)
    infants: int | None = Field(ge=0, le=20)
    minor_ages: list[int]
    nationalities: list[str]
    budget_amount: float | None = Field(ge=0)
    budget_currency: str | None
    cabin_class: str | None
    accommodation_preferences: list[str]
    interests: list[str]
    requested_activities: list[str]
    dining_preferences: list[str] = Field(default_factory=list)
    requested_event: str | None
    requested_event_type: str | None
    ticket_requested: bool
    dining_out_count: int | None = Field(ge=0, le=100)
    baggage_information_requested: bool
    accessibility_needs: list[str]
    dietary_requirements: list[str] = Field(default_factory=list)
    negative_constraints: list[str] = Field(default_factory=list)
    fields_to_clear: list[str] = Field(default_factory=list)
    special_occasion: str | None
    special_occasion_date: str | None
    special_occasion_notes: str | None
    companion_relationship: str | None
    companion_origin: str | None
    clarification_notes: list[str]

    def to_classified_intent(self) -> ClassifiedIntent:
        entities: dict[str, str] = {}

        scalar_values: dict[str, Any] = {
            "destination": self.destination,
            "destination_region": self.destination_region,
            "origin": self.origin,
            "airport_preference": self.airport_preference,
            "country_of_residence": self.country_of_residence,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "duration_days": self.duration_days,
            "month": self.month,
            "travel_year": self.travel_year,
            "departure_day": self.departure_day,
            "adults": self.adults,
            "children": self.children,
            "infants": self.infants,
            "budget_amount": self.budget_amount,
            "budget_currency": self.budget_currency,
            "cabin_class": self.cabin_class,
            "requested_event": self.requested_event,
            "requested_event_type": self.requested_event_type,
            "dining_out_count": self.dining_out_count,
            "special_occasion": self.special_occasion,
            "special_occasion_date": self.special_occasion_date,
            "special_occasion_notes": self.special_occasion_notes,
        }
        for key, value in scalar_values.items():
            if value is not None and str(value).strip():
                entities[key] = str(value)

        list_values = {
            "departure_options": self.departure_options,
            "airline_preferences": self.airline_preferences,
            "local_areas": self.local_areas,
            "minor_ages": self.minor_ages,
            "nationalities": self.nationalities,
            "residency_documents": self.residency_documents,
            "interests": self.interests,
            "requested_activities": self.requested_activities,
            "dining_preferences": self.dining_preferences,
            "accessibility_needs": self.accessibility_needs,
            "dietary_requirements": self.dietary_requirements,
            "negative_constraints": self.negative_constraints,
        }
        for key, values in list_values.items():
            cleaned = _clean_list(values)
            if cleaned:
                entities[key] = ",".join(cleaned)

        if self.nationalities:
            entities["nationality"] = str(self.nationalities[0]).strip()

        accommodation = _clean_list(self.accommodation_preferences)
        if accommodation:
            entities["accommodation_preference"] = accommodation[0]
            if len(accommodation) > 1:
                entities["additional_accommodation_preferences"] = ",".join(
                    accommodation[1:]
                )

        if self.start_date:
            entities["date_hint"] = self.start_date
            entities["date_precision"] = "EXACT" if self.end_date else "DAY"
            try:
                parsed_start = date.fromisoformat(self.start_date)
                entities.setdefault("month", str(parsed_start.month))
                entities.setdefault("travel_year", str(parsed_start.year))
                entities.setdefault("departure_day", str(parsed_start.day))
            except ValueError:
                pass
        elif self.month:
            entities["date_hint"] = str(self.month)
            entities["date_precision"] = "MONTH"

        if self.year_explicit:
            entities["year_explicit"] = "true"
        elif self.start_date and self.travel_year:
            entities["date_year_inferred"] = "true"
            entities["date_inference_note"] = (
                f"Year not supplied; using the next occurrence in {self.travel_year}."
            )

        if self.ticket_requested:
            entities["ticket_requested"] = "true"
            entities["requested_event_status"] = "REQUESTED_NOT_CONFIRMED"
        if self.baggage_information_requested:
            entities["baggage_information_requested"] = "true"
        cleared = [
            field
            for field in _clean_list(self.fields_to_clear)
            if field in _CLEARABLE_TRIP_FIELDS
        ]
        if cleared:
            entities["clear_fields"] = ",".join(cleared)

        # A relationship mention alone (for example, "my wife is interested
        # in shopping") does not describe a separate journey.  Only surface a
        # companion plan when the customer has also supplied that companion's
        # distinct origin.  The deterministic parser follows the same rule.
        if self.companion_relationship and self.companion_origin:
            entities["companion_relationship"] = self.companion_relationship
            entities["companion_origin"] = self.companion_origin

        return ClassifiedIntent(
            intent=Intent(self.intent),
            confidence=self.confidence,
            entities=entities,
        )


class PersonalisedDay(BaseModel):
    model_config = ConfigDict(extra="forbid")

    day: int = Field(ge=1, le=180)
    title: str
    theme: str
    morning: str
    afternoon: str
    evening: str
    accommodation: str
    notes: str


class PersonalisedItinerary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    daily_outline: list[PersonalisedDay]
    planning_notes: list[str]


_INTERPRETATION_INSTRUCTIONS = """
You are Tralvana's travel-request interpretation engine. Convert the current
customer message and the supplied conversation state into structured facts.

Rules:
- Preserve every explicit customer fact. Never replace a real origin, date,
  party count, age, nationality, preference, activity, or event with a guess.
- Resolve spelling mistakes and ordinary place aliases. For a broad region
  whose named activities clearly establish the practical base, use that city
  as destination and preserve the customer's broader place in
  destination_region (for example Disney World can establish Orlando as the
  base for a Florida trip). Otherwise keep the requested destination unchanged.
- Treat follow-up messages as updates to the existing plan. Keep earlier facts
  unless the customer clearly corrects, replaces, or removes them. Put fields
  the customer explicitly removes in fields_to_clear.
- If a day and month are supplied without a year, use the next occurrence of
  that date on or after the supplied current date and set year_explicit to
  false. If the year is stated, set it true. Compute end_date from start_date
  plus duration when possible.
- A request for N full days means duration_days=N and end_date is N days after
  start_date. A return date takes priority when both dates are explicit.
- Separate activities, transport logistics, and dining. Capture attractions,
  shops, parks and historical places in requested_activities. Put requested
  restaurant styles or meal experiences in dining_preferences. Never put a
  flight connection, airport, airline, baggage request, restaurant, meal,
  trattoria, tapas bar or dining instruction in requested_activities.
- Capture dining frequency, events, cabin, hotel needs, children's ages, every
  stated nationality, baggage questions, dietary requirements, accessibility
  needs, and negative constraints such as no alcohol.
- Keep home city, country of residence, flexible airport choice, and preferred
  airlines as separate facts. An airline must never appear as a departure city.
- Preserve traveller-specific immigration context in residency_documents using
  concise labels such as "Nigerian: Italian long-stay visa". Do not infer that
  residence alone is a visa or permit.
- Treat "package allowance" as a likely baggage-allowance request in a flight
  context. Do not invent an allowance; only mark that guidance was requested.
- A business meeting is an activity or purpose, not business-class airfare.
  Set cabin_class to business only when the customer explicitly requests a
  business-class seat or cabin.
- Do not infer trip duration from phrases such as "two day trips" or "drive in
  one day". Duration must describe the whole trip/stay or come from travel dates.
- A request that includes visa or entry questions remains PLAN_TRIP when the
  customer is asking for a complete journey; preserve all mixed nationalities.
- Set companion_relationship and companion_origin only when the customer
  explicitly says that person is travelling separately from a different
  origin. Merely mentioning a wife, husband, partner, friend, or children does
  not create a separate journey.
- Do not invent event dates, fashion shows, flight availability, hotel names,
  prices, baggage allowances, visa rules, or reservations.
- Use GENERAL_CONVERSATION with empty travel fields when the input is not a
  travel request. Put only short factual ambiguities in clarification_notes;
  do not include private reasoning.
""".strip()


_ITINERARY_INSTRUCTIONS = """
You are Tralvana's itinerary adaptation engine. Build a practical day-by-day
outline from the grounded trip brief and provider evidence supplied.

Rules:
- Return exactly duration_days entries numbered consecutively from 1.
- Honour the full party composition, children's ages, pace, accessibility,
  requested activities, dining count and dining preferences, interests, hotel preferences, special
  occasions, dates, separate arrivals, dietary needs and negative constraints.
- Never schedule or recommend something the customer excluded. For example,
  an alcohol-free request must not include bars, wine tastings or cocktails.
- Make arrival and departure days realistic. Balance major days with rest and
  avoid sending a family across distant areas repeatedly.
- Match the theme and the rest of each day to its scheduled requested activity.
  Do not place a museum inside a football day, a gorge inside a spa day, or a
  remote day trip inside a generic city-orientation template.
- Do not treat transport connections or dining requests as daytime attractions.
  If the traveller requested N restaurant meals, clearly plan N restaurant
  evenings rather than silently turning every evening into dining out.
- Named attractions may be proposed as itinerary ideas, but must be worded as
  needing official opening-time and ticket confirmation unless current
  provider evidence explicitly confirms them.
- Never invent an airline, fare, hotel, room, price, availability, booking,
  event date, ticket, baggage allowance, visa rule, or weather forecast.
- Use only provider events supplied in the evidence as current listings.
  Customer-requested events without provider confirmation must remain checks,
  not scheduled claims.
- If baggage information was requested, state that allowance depends on the
  selected live fare and must be checked before payment.
- A requested fashion show must not be treated as scheduled unless provider
  evidence confirms it. A retail shop visit may remain a flexible suggestion.
- Keep each field concise and customer-facing. planning_notes must contain only
  short caveats or unresolved choices, never hidden reasoning.
""".strip()


class OpenAITripIntelligence:
    """Thin, failure-safe OpenAI Responses API boundary."""

    def __init__(self, client: Any, model: str) -> None:
        self._client = client
        self.model = model

    @classmethod
    def from_environment(cls) -> OpenAITripIntelligence | None:
        api_key = os.environ.get("OPENAI_API_KEY", "").strip()
        enabled = os.environ.get("TRALVANA_OPENAI_ENABLED", "true").strip().lower()
        if not api_key or enabled not in {"1", "true", "yes", "on"}:
            return None
        try:
            from openai import AsyncOpenAI
        except ImportError:
            logger.warning("OpenAI trip intelligence is configured but the SDK is unavailable")
            return None

        try:
            timeout = float(os.environ.get("TRALVANA_OPENAI_TIMEOUT_SECONDS", "15"))
            model = os.environ.get("TRALVANA_OPENAI_MODEL", "gpt-5.6").strip()
            client = AsyncOpenAI(
                api_key=api_key,
                timeout=timeout,
                max_retries=0,
            )
        except Exception as exc:
            logger.warning(
                "OpenAI trip intelligence could not initialise (%s)",
                type(exc).__name__,
            )
            return None
        return cls(client=client, model=model)

    async def interpret(
        self,
        *,
        message: str,
        existing_entities: dict[str, str],
        history: list[ConversationMessage],
        current_date: date | None = None,
    ) -> ClassifiedIntent | None:
        payload = {
            "current_date": (current_date or datetime.now().date()).isoformat(),
            "existing_confirmed_trip_facts": existing_entities,
            "recent_conversation": [
                {"role": item.role, "content": item.content}
                for item in history[-8:]
            ],
            "current_customer_message": message,
        }
        try:
            response = await self._client.responses.parse(
                model=self.model,
                input=[
                    {"role": "system", "content": _INTERPRETATION_INSTRUCTIONS},
                    {"role": "user", "content": json.dumps(payload)},
                ],
                text_format=TripInterpretation,
                prompt_cache_key="tralvana-trip-interpretation-v2",
                reasoning={"effort": "low"},
                store=False,
            )
            parsed = response.output_parsed
            if not isinstance(parsed, TripInterpretation):
                return None
            return parsed.to_classified_intent()
        except Exception as exc:  # provider failure must not break trip planning
            logger.warning(
                "OpenAI trip interpretation failed (%s); using deterministic fallback",
                type(exc).__name__,
            )
            return None

    async def personalise_itinerary(
        self,
        *,
        trip_brief: dict[str, Any],
        provider_evidence: dict[str, Any],
        fallback_outline: list[dict[str, Any]],
    ) -> PersonalisedItinerary | None:
        duration = int(trip_brief.get("duration_days") or 0)
        if duration <= 0:
            return None
        payload = {
            "trip_brief": trip_brief,
            "provider_evidence": provider_evidence,
            "fallback_outline": fallback_outline,
        }
        try:
            response = await self._client.responses.parse(
                model=self.model,
                input=[
                    {"role": "system", "content": _ITINERARY_INSTRUCTIONS},
                    {"role": "user", "content": json.dumps(payload)},
                ],
                text_format=PersonalisedItinerary,
                prompt_cache_key="tralvana-itinerary-adaptation-v2",
                reasoning={"effort": "low"},
                store=False,
            )
            parsed = response.output_parsed
            if not isinstance(parsed, PersonalisedItinerary):
                return None
            expected_days = list(range(1, duration + 1))
            if [entry.day for entry in parsed.daily_outline] != expected_days:
                logger.warning(
                    "OpenAI itinerary returned an invalid day sequence; using fallback"
                )
                return None
            return parsed
        except Exception as exc:  # grounded deterministic itinerary remains available
            logger.warning(
                "OpenAI itinerary adaptation failed (%s); using deterministic fallback",
                type(exc).__name__,
            )
            return None


def should_use_openai_interpretation(
    *,
    rule_intent: Intent,
    active_goal: str | None,
    message: str,
) -> bool:
    """Avoid API cost for greetings while covering plans and refinements."""
    if active_goal == Intent.PLAN_TRIP.value:
        return True
    if rule_intent in {Intent.PLAN_TRIP, Intent.MODIFY_TRIP}:
        return True
    return len(message.split()) >= 18 and any(
        term in message.casefold()
        for term in ("trip", "holiday", "travel", "flight", "hotel", "visit")
    )


def merge_interpretations(
    rule_result: ClassifiedIntent,
    ai_result: ClassifiedIntent | None,
    message: str = "",
) -> ClassifiedIntent:
    """Prefer explicit structured extraction while retaining proven rules."""
    if ai_result is None:
        return rule_result

    entities = dict(rule_result.entities)
    ai_entities = dict(ai_result.entities)
    clear_fields = _clean_list(ai_entities.pop("clear_fields", "").split(","))
    entities.update(ai_entities)
    for field in clear_fields:
        if field in _CLEARABLE_TRIP_FIELDS:
            entities.pop(field, None)

    rule_nationalities = _clean_list(
        rule_result.entities.get("nationalities", "").split(",")
    )
    ai_nationalities = _clean_list(
        ai_result.entities.get("nationalities", "").split(",")
    )
    combined_nationalities = _normalise_nationalities(
        [*rule_nationalities, *ai_nationalities]
    )
    if combined_nationalities:
        entities["nationalities"] = ",".join(combined_nationalities)
        entities["nationality"] = combined_nationalities[0]

    residency_documents = _dedupe_residency_documents([
        *ai_result.entities.get("residency_documents", "").split(","),
        *rule_result.entities.get("residency_documents", "").split(","),
        *_residency_documents_from_message(message),
    ])
    if residency_documents:
        entities["residency_documents"] = ",".join(residency_documents)

    activities = _clean_list(entities.get("requested_activities", "").split(","))
    dining_preferences = _clean_list(
        entities.get("dining_preferences", "").split(",")
    )
    filtered_activities: list[str] = []
    for activity in activities:
        if _is_transport_instruction(activity):
            continue
        if _is_dining_instruction(activity):
            dining_preferences.append(activity)
            continue
        filtered_activities.append(activity)
    if filtered_activities:
        entities["requested_activities"] = ",".join(_clean_list(filtered_activities))
    else:
        entities.pop("requested_activities", None)
    dining_preferences = [
        value
        for value in _clean_list(dining_preferences)
        if value.casefold().strip() not in {
            "dining together", "dine out together", "dine out together as a family",
        }
    ]
    if dining_preferences:
        entities["dining_preferences"] = ",".join(dining_preferences)
    else:
        entities.pop("dining_preferences", None)

    lowered = message.casefold()
    if (
        entities.get("cabin_class", "").casefold() == "business"
        and not _explicit_business_cabin(lowered)
        and rule_result.entities.get("cabin_class", "").casefold() != "business"
    ):
        entities.pop("cabin_class", None)
    if "no alcohol" in lowered or "alcohol-free" in lowered:
        constraints = _clean_list(
            [*entities.get("negative_constraints", "").split(","), "No alcohol"]
        )
        entities["negative_constraints"] = ",".join(constraints)
    _normalise_dates(entities)

    intent = ai_result.intent
    if rule_result.intent == Intent.PLAN_TRIP:
        intent = Intent.PLAN_TRIP
    elif rule_result.intent == Intent.MODIFY_TRIP:
        intent = Intent.MODIFY_TRIP

    return ClassifiedIntent(
        intent=intent,
        confidence=max(rule_result.confidence, ai_result.confidence),
        entities=entities,
    )


def _normalise_dates(entities: dict[str, str]) -> None:
    start_raw = entities.get("start_date")
    end_raw = entities.get("end_date")
    if not start_raw:
        return
    try:
        start = date.fromisoformat(start_raw)
        end = date.fromisoformat(end_raw) if end_raw else None
    except ValueError:
        return
    if entities.get("date_year_inferred") == "true" and start < date.today():
        duration = (end - start).days if end and end > start else None
        try:
            start = start.replace(year=start.year + 1)
        except ValueError:
            start = start.replace(year=start.year + 1, day=28)
        end = start + timedelta(days=duration) if duration is not None else None
        entities["start_date"] = start.isoformat()
        if end:
            entities["end_date"] = end.isoformat()
        entities["date_inference_note"] = (
            f"Year not supplied; using the next occurrence in {start.year}."
        )
    entities["month"] = str(start.month)
    entities["travel_year"] = str(start.year)
    entities["departure_day"] = str(start.day)
    entities["date_hint"] = start.strftime("%-d %B %Y")
    if end and end > start:
        entities["end_date"] = end.isoformat()
        entities["duration_days"] = str((end - start).days)
        entities["date_precision"] = "EXACT"


def _clean_list(values: list[Any]) -> list[str]:
    return list(
        dict.fromkeys(
            str(value).strip()
            for value in values
            if str(value).strip()
        )
    )


def _normalise_nationalities(values: list[Any]) -> list[str]:
    """Expand dual labels and deduplicate nationality adjectives."""
    expanded: list[str] = []
    for value in values:
        cleaned = str(value).strip()
        if not cleaned:
            continue
        cleaned = cleaned.removeprefix("Dual ").removeprefix("dual ")
        parts = re.split(r"\s*[-/]\s*", cleaned)
        expanded.extend(part for part in parts if part)
    return _clean_list(expanded)


def _dedupe_residency_documents(values: list[Any]) -> list[str]:
    deduped: list[str] = []
    seen: set[str] = set()
    for value in _clean_list(values):
        key = re.sub(r"[-\s]+", " ", value.casefold()).replace("long term", "long stay")
        if key in seen:
            continue
        seen.add(key)
        deduped.append(value)
    return deduped


def _is_transport_instruction(value: str) -> bool:
    lowered = value.casefold()
    return any(
        term in lowered
        for term in (
            "connect through", "connection through", "connecting through",
            "airport", "airline", "flight", "baggage", "package allowance",
        )
    )


def _is_dining_instruction(value: str) -> bool:
    lowered = value.casefold()
    return any(
        term in lowered
        for term in (
            "dine", "dining", "restaurant", "trattoria", "tapas bar",
            "barbecue meal", "seafood meal", "dinner", "lunch at",
        )
    )


def _residency_documents_from_message(message: str) -> list[str]:
    """Preserve explicit traveller-specific Schengen document context."""
    lowered = message.casefold()
    status_match = re.search(
        r"\b(?:residing|living)\s+in\s+"
        r"(milan|rome|naples|warsaw|barcelona|madrid|paris|berlin)\b.{0,50}?\b"
        r"(long[- ](?:term|stay) visa|residence permit|work visa)\b",
        lowered,
    )
    if not status_match:
        return []
    nationality_matches = list(re.finditer(r"\b([a-z]+)\s+national\b", lowered[:status_match.start()]))
    if not nationality_matches:
        return []
    nationality = nationality_matches[-1].group(1)
    city, document = status_match.groups()
    country_by_city = {
        "milan": "Italian", "rome": "Italian", "naples": "Italian",
        "warsaw": "Polish", "barcelona": "Spanish", "madrid": "Spanish",
        "paris": "French", "berlin": "German",
    }
    return [
        f"{nationality.title()}: {country_by_city[city]} {document.replace('-', ' ')}"
    ]


_CLEARABLE_TRIP_FIELDS = {
    "destination",
    "destination_region",
    "local_areas",
    "origin",
    "departure_options",
    "airport_preference",
    "airline_preferences",
    "residency_documents",
    "start_date",
    "end_date",
    "date_hint",
    "duration_days",
    "budget_amount",
    "budget_currency",
    "requested_event",
    "requested_event_type",
    "requested_activities",
    "dining_preferences",
    "interests",
    "accommodation_preference",
}


def _explicit_business_cabin(message: str) -> bool:
    return any(
        phrase in message
        for phrase in (
            "business class",
            "business-class",
            "business cabin",
            "fly business",
            "flying business",
        )
    )

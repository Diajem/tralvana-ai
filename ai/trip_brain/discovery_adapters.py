"""
Discovery Module adapters — Trip Brain's only call sites into the six
Discovery modules.

Each adapter calls exactly the same public `service.recommend()` /
`check()` / `analyse()` entrypoint (via its `*_from_conversation()`
convenience wrapper) that `ConversationEngine` already calls today for
narrow intents — never a Provider, never another module's Repository
(docs/KNOWLEDGE_SOURCE_STRATEGY.md's boundary rule, restated in
ADR-017).

Flight, Accommodation, Destination, and Budget Intelligence don't expose a
top-level `confidence` field on their domain model; each adapter derives
one as the mean `match_score` across returned options, and picks out the
`BEST_OVERALL` option as the top pick — the exact second-order aggregation
docs/TRIP_BRAIN_ARCHITECTURE.md's Confidence Propagation section
describes, not a new scoring model. Visa and Weather Intelligence already
return an explicit `confidence` field and are passed through unchanged.

Per-module isolation (docs/TRIP_BRAIN_ARCHITECTURE.md's Failure Handling):
every adapter catches its own exceptions and returns a FAILED AgentResult
rather than letting one module's failure abort the others.
"""

from __future__ import annotations

from typing import Any

from ai.shared.agent_result import AgentResult
from ai.shared.agent_status import AgentStatus
from ai.trip_brain.context import TripBrainContext


def _avg_match_score(options: list[dict[str, Any]]) -> float:
    return sum(o["match_score"] for o in options) / len(options) if options else 0.0


def _top_option(options: list[dict[str, Any]]) -> dict[str, Any]:
    return next(
        (o for o in options if o["recommendation_type"] == "BEST_OVERALL"),
        options[0] if options else {},
    )


def _failed(agent_name: str, exc: Exception) -> AgentResult:
    return AgentResult(
        agent_name=agent_name,
        status=AgentStatus.FAILED,
        confidence=0.0,
        risks=[f"{agent_name} raised an exception: {exc}"],
    )


def run_flight_intelligence(context: TripBrainContext) -> AgentResult:
    try:
        from app.domains.flights.service import flight_intelligence_service
        output = flight_intelligence_service.recommend_from_conversation(
            traveller_id=context.traveller_id,
            trip_id=context.trip_id,
            entities=context.entities,
            profile=context.profile,
        )
    except Exception as exc:
        return _failed("flight_intelligence", exc)

    options = output["flight_options"]
    top = _top_option(options)
    return AgentResult(
        agent_name="flight_intelligence",
        status=AgentStatus.SUCCESS if options else AgentStatus.NEEDS_INFORMATION,
        confidence=round(_avg_match_score(options), 2),
        data={
            "count": len(options),
            "origin": output["origin"],
            "destination": output["destination"],
            "top_option": top,
            "flight_option_ids": [f["flight_option_id"] for f in options],
        },
        assumptions=output["assumptions"],
        risks=[r for f in options for r in f["risks"]][:5],
        next_actions=output["next_actions"],
    )


def run_accommodation_intelligence(context: TripBrainContext) -> AgentResult:
    try:
        from app.domains.accommodation.service import accommodation_intelligence_service
        output = accommodation_intelligence_service.recommend_from_conversation(
            traveller_id=context.traveller_id,
            trip_id=context.trip_id,
            entities=context.entities,
            profile=context.profile,
        )
    except Exception as exc:
        return _failed("accommodation_intelligence", exc)

    options = output["accommodation_options"]
    top = _top_option(options)
    return AgentResult(
        agent_name="accommodation_intelligence",
        status=AgentStatus.SUCCESS if options else AgentStatus.NEEDS_INFORMATION,
        confidence=round(_avg_match_score(options), 2),
        data={
            "count": len(options),
            "destination": output["destination"],
            "top_option": top,
            "accommodation_option_ids": [a["accommodation_option_id"] for a in options],
        },
        assumptions=output["assumptions"],
        risks=[r for a in options for r in a["risks"]][:5],
        next_actions=output["next_actions"],
    )


def run_destination_intelligence(context: TripBrainContext) -> AgentResult:
    try:
        from app.domains.destinations.service import destination_intelligence_service
        output = destination_intelligence_service.recommend_from_conversation(
            traveller_id=context.traveller_id,
            trip_id=context.trip_id,
            entities=context.entities,
            profile=context.profile,
        )
    except Exception as exc:
        return _failed("destination_intelligence", exc)

    options = output["destination_options"]
    top = _top_option(options)
    return AgentResult(
        agent_name="destination_intelligence",
        status=AgentStatus.SUCCESS if options else AgentStatus.NEEDS_INFORMATION,
        confidence=round(_avg_match_score(options), 2),
        data={
            "count": len(options),
            "city": output["city"],
            "top_option": top,
            "destination_option_ids": [d["destination_option_id"] for d in options],
        },
        assumptions=output["assumptions"],
        risks=[r for d in options for r in d["risks"]][:5],
        next_actions=output["next_actions"],
    )


def run_budget_intelligence(context: TripBrainContext) -> AgentResult:
    try:
        from app.domains.budget.service import budget_intelligence_service
        output = budget_intelligence_service.recommend_from_conversation(
            traveller_id=context.traveller_id,
            trip_id=context.trip_id,
            entities=context.entities,
            profile=context.profile,
        )
    except Exception as exc:
        return _failed("budget_intelligence", exc)

    options = output["budget_options"]
    top = _top_option(options)
    return AgentResult(
        agent_name="budget_intelligence",
        status=AgentStatus.SUCCESS if options else AgentStatus.NEEDS_INFORMATION,
        confidence=round(_avg_match_score(options), 2),
        data={
            "count": len(options),
            "destination": output["destination"],
            "top_option": top,
            "budget_option_ids": [o["budget_option_id"] for o in options],
        },
        assumptions=output["assumptions"],
        risks=[r for o in options for r in o["risks"]][:5],
        next_actions=output["next_actions"],
    )


def run_visa_intelligence(context: TripBrainContext) -> AgentResult:
    try:
        from app.domains.visa.service import visa_intelligence_service
        output = visa_intelligence_service.check_from_conversation(
            traveller_id=context.traveller_id,
            trip_id=context.trip_id,
            entities=context.entities,
            profile=context.profile,
        )
    except Exception as exc:
        return _failed("visa_intelligence", exc)

    return AgentResult(
        agent_name="visa_intelligence",
        status=AgentStatus.SUCCESS,
        confidence=output["confidence"],
        data=output,
        assumptions=output["assumptions"],
        risks=output["risks"],
        next_actions=[output["recommendation"]],
    )


def run_weather_intelligence(context: TripBrainContext) -> AgentResult:
    try:
        from app.domains.weather.service import weather_intelligence_service
        output = weather_intelligence_service.analyse_from_conversation(
            traveller_id=context.traveller_id,
            trip_id=context.trip_id,
            entities=context.entities,
            profile=context.profile,
        )
    except Exception as exc:
        return _failed("weather_intelligence", exc)

    return AgentResult(
        agent_name="weather_intelligence",
        status=AgentStatus.SUCCESS,
        confidence=output["confidence"],
        data=output,
        assumptions=output["assumptions"],
        risks=output["risks"],
        next_actions=[output["recommendation"]],
    )


MODULE_RUNNERS = {
    "flight": run_flight_intelligence,
    "accommodation": run_accommodation_intelligence,
    "destination": run_destination_intelligence,
    "budget": run_budget_intelligence,
    "visa": run_visa_intelligence,
    "weather": run_weather_intelligence,
}

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Callable

from ai.discovery.events.event_normalizer import event_normalizer
from ai.discovery.events.event_reasoner import event_reasoner
from ai.discovery.events.event_risk_assessor import event_risk_assessor
from ai.discovery.events.event_scorer import event_scorer
from travelos.intelligence_gateway.discovery_adapters import GatewayEventProvider


class EventIntelligence:
    """Provider-neutral event discovery with fail-closed provenance."""

    def __init__(
        self,
        provider: GatewayEventProvider | None = None,
        today_provider: Callable[[], date] = date.today,
    ) -> None:
        self._provider = provider or GatewayEventProvider()
        self._today_provider = today_provider

    def recommend(
        self,
        destination: str,
        start_date: str | None = None,
        end_date: str | None = None,
        interests: list[str] | None = None,
    ) -> dict[str, Any]:
        interests = interests or []
        raw = self._provider.search(
            destination=destination,
            start_date=start_date,
            end_date=end_date,
            interests=interests,
        )

        options: list[dict[str, Any]] = []
        excluded_outside_dates = 0
        excluded_outside_destination = 0
        excluded_irrelevant = 0
        for record in raw:
            event = event_normalizer.normalize(record)
            is_live = event.get("_evidence_level") == "LIVE"
            if is_live and not _matches_requested_destination(
                event, destination
            ):
                excluded_outside_destination += 1
                continue
            if is_live and not _inside_requested_dates(
                event,
                start_date=start_date,
                end_date=end_date,
                today=self._today_provider(),
            ):
                excluded_outside_dates += 1
                continue
            score = event_scorer.score(event, interests)
            if interests and not score["is_relevant"]:
                excluded_irrelevant += 1
                continue
            options.append(
                {
                    **event,
                    "match_score": score["match_score"],
                    "interests_matched": score["interests_matched"],
                    "reasoning": event_reasoner.explain(event, score),
                    "risks": event_risk_assessor.assess(event),
                    "assumptions": (
                        [
                            "This is a live provider listing; ticket inventory, "
                            "pricing, and final event details still require confirmation."
                        ]
                        if is_live
                        else [
                            "This is a curated search idea, not a confirmed event listing."
                        ]
                    ),
                }
            )

        ranked = sorted(options, key=lambda option: option["match_score"], reverse=True)
        for index, option in enumerate(ranked):
            option["recommendation_type"] = (
                "BEST_OVERALL" if index == 0 else "ALTERNATIVE"
            )
            option.pop("_tags", None)
            option.pop("_requested_interests", None)
            option.pop("_evidence_level", None)
            option.pop("_local_date", None)

        result = self._provider.last_result
        used_fallback = getattr(self._provider, "used_mock_fallback", False)
        is_live = bool(
            result
            and result.provider_name == "ticketmaster_event_provider"
            and not used_fallback
        )
        if used_fallback:
            data_source = "MOCK_FALLBACK"
        elif is_live:
            data_source = "TICKETMASTER_DISCOVERY_API"
        else:
            data_source = "TRALVANA_CURATED_EVENT_IDEAS"
        provider_status = result.status.value if result else "UNAVAILABLE"
        retrieved_at = result.retrieved_at if result else None

        if is_live:
            assumptions = [
                "Event dates and public links were retrieved from Ticketmaster "
                "Discovery API; ticket inventory and pricing are not guaranteed."
            ]
            next_actions = [
                "Open the official event page and confirm current status, price, "
                "ticket inventory, venue rules, and accessibility details.",
                "Recheck the listing before changing non-refundable travel plans.",
            ]
            summary = (
                f"{len(ranked)} live event listing(s) matched for {destination}. "
                "Availability and pricing still require confirmation."
            )
            if excluded_outside_dates or excluded_irrelevant:
                summary += (
                    f" Excluded {excluded_outside_dates} listing(s) outside the "
                    f"travel dates, {excluded_outside_destination} listing(s) outside "
                    f"{destination}, and {excluded_irrelevant} unrelated listing(s)."
                )
        elif used_fallback:
            assumptions = [
                "Ticketmaster live search was unavailable; results are curated "
                "fallback ideas with no confirmed date, ticket, price, or availability."
            ]
            next_actions = [
                "Retry the live event search.",
                "Check the official organiser, venue, league, club, or fashion calendar.",
            ]
            summary = (
                f"{len(ranked)} curated fallback event idea(s) matched for "
                f"{destination}; none is a confirmed listing."
            )
        else:
            assumptions = [
                "Event results are deterministic curated ideas; no live calendar, "
                "fixture, ticket, price, or availability provider was queried."
            ]
            next_actions = [
                "Check the official organiser, venue, league, club, or fashion calendar.",
                "Confirm the exact date and availability before changing the itinerary.",
            ]
            summary = (
                f"{len(ranked)} curated event idea(s) matched for {destination}. "
                "None is a confirmed date-specific listing."
            )

        return {
            "destination": destination,
            "start_date": start_date,
            "end_date": end_date,
            "event_options": ranked,
            "data_source": data_source,
            "provider_status": provider_status,
            "retrieved_at": retrieved_at,
            "assumptions": assumptions,
            "next_actions": next_actions,
            "recommended_agents": ["experience_agent"],
            "summary": summary,
            "filter_summary": {
                "provider_result_count": len(raw),
                "excluded_outside_travel_dates": excluded_outside_dates,
                "excluded_outside_destination": excluded_outside_destination,
                "excluded_as_irrelevant": excluded_irrelevant,
                "returned_event_count": len(ranked),
            },
        }


event_intelligence = EventIntelligence()


_COUNTRY_REQUESTS = {
    "france", "ghana", "ireland", "jamaica", "japan", "nigeria", "spain",
    "uae", "united arab emirates", "uk", "united kingdom", "usa",
    "united states", "united states of america",
}


def _matches_requested_destination(
    event: dict[str, Any], requested_destination: str
) -> bool:
    requested = " ".join(requested_destination.casefold().split())
    if not requested or requested in _COUNTRY_REQUESTS:
        return True
    event_destination = " ".join(
        str(event.get("destination", "")).casefold().split()
    )
    venue = " ".join(str(event.get("venue_area", "")).casefold().split())
    return requested == event_destination or requested in venue


def _inside_requested_dates(
    event: dict[str, Any],
    *,
    start_date: str | None,
    end_date: str | None,
    today: date,
) -> bool:
    """Fail closed when a live listing cannot prove it fits the trip window."""
    event_date = _event_local_date(event)
    if event_date is None:
        return False

    requested_start = _iso_date(start_date)
    start = max(requested_start, today) if requested_start else today
    end = _iso_date(end_date)
    if start and event_date < start:
        return False
    if end and event_date > end:
        return False
    return True


def _event_local_date(event: dict[str, Any]) -> date | None:
    local_date = event.get("_local_date")
    parsed_local = _iso_date(str(local_date)) if local_date else None
    if parsed_local:
        return parsed_local

    starts_at = event.get("starts_at")
    if not starts_at:
        return None
    value = str(starts_at).strip()
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).date()
    except ValueError:
        return _iso_date(value)


def _iso_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None

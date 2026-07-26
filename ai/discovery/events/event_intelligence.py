from __future__ import annotations

from typing import Any

from ai.discovery.events.event_normalizer import event_normalizer
from ai.discovery.events.event_reasoner import event_reasoner
from ai.discovery.events.event_risk_assessor import event_risk_assessor
from ai.discovery.events.event_scorer import event_scorer
from travelos.intelligence_gateway.discovery_adapters import GatewayEventProvider


class EventIntelligence:
    """Provider-neutral event discovery with fail-closed provenance."""

    def __init__(self, provider: GatewayEventProvider | None = None) -> None:
        self._provider = provider or GatewayEventProvider()

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
        for record in raw:
            event = event_normalizer.normalize(record)
            score = event_scorer.score(event, interests)
            is_live = event.get("_evidence_level") == "LIVE"
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
        }


event_intelligence = EventIntelligence()

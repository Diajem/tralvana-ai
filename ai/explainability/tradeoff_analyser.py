"""
Trade-off Analyser — deterministic comparisons between the option Trip
Brain recommended and an alternative the same Discovery module already
computed and labelled (docs/EXPLAINABILITY_ENGINE.md's Trade-off
Analysis section). Every comparison reads fields already present in
AgentResult.data — no score is read, recomputed, or blended, and no
option is re-ranked.

Grounded in labels each module's own labelling algorithm already assigns
(docs/DISCOVERY_LAYER_PATTERN.md) — LOWEST_PRICE (flight), BEST_BUDGET
(accommodation), LOWEST_COST (budget) — surfaced onto AgentResult.data as
`alternative_option` by ai/trip_brain/discovery_adapters.py.
"""

from __future__ import annotations

from ai.shared.agent_result import AgentResult
from ai.shared.agent_status import AgentStatus

_FAVOURABLE_WEATHER = ("excellent", "good")
_SIMPLE_VISA_STATUSES = ("visa_free", "visa_on_arrival")
_ELEVATED_BUDGET_TIERS = ("comfort", "luxury")


def _ok(result: AgentResult | None) -> bool:
    return result is not None and result.status != AgentStatus.FAILED


def _flight_tradeoff(result: AgentResult | None) -> str | None:
    if not _ok(result):
        return None
    top = result.data.get("top_option") or {}
    alt = result.data.get("alternative_option")
    if not alt or not top:
        return None
    top_price, alt_price = top.get("estimated_price"), alt.get("estimated_price")
    if not isinstance(top_price, (int, float)) or not isinstance(alt_price, (int, float)):
        return None
    if alt_price >= top_price:
        return None
    return (
        f"Flights: a cheaper option is available ({alt.get('currency', '')} {alt_price} vs "
        f"{top.get('currency', '')} {top_price}) — it has {alt.get('stops', 0)} stop(s) and takes "
        f"{alt.get('total_duration', 'longer')}, versus {top.get('stops', 0)} stop(s) and "
        f"{top.get('total_duration', 'the recommended time')} for the recommended flight."
    )


def _accommodation_tradeoff(result: AgentResult | None) -> str | None:
    if not _ok(result):
        return None
    top = result.data.get("top_option") or {}
    alt = result.data.get("alternative_option")
    if not alt or not top:
        return None
    top_price, alt_price = top.get("nightly_price"), alt.get("nightly_price")
    if not isinstance(top_price, (int, float)) or not isinstance(alt_price, (int, float)):
        return None
    if alt_price >= top_price:
        return None
    return (
        f"Accommodation: a lower-cost stay is available ({alt.get('currency', '')} {alt_price}/night vs "
        f"{top.get('currency', '')} {top_price}/night) — rated {alt.get('star_rating', '?')} star(s) "
        f"versus {top.get('star_rating', '?')} star(s) for the recommended pick."
    )


def _budget_tradeoff(result: AgentResult | None) -> str | None:
    if not _ok(result):
        return None
    top = result.data.get("top_option") or {}
    alt = result.data.get("alternative_option")
    if not alt or not top:
        return None
    top_cost, alt_cost = top.get("total_cost_usd"), alt.get("total_cost_usd")
    if not isinstance(top_cost, (int, float)) or not isinstance(alt_cost, (int, float)):
        return None
    if alt_cost >= top_cost:
        return None
    return (
        f"Budget: a lower overall tier is available ({alt.get('budget_style', 'a cheaper tier')} at "
        f"${alt_cost} vs {top.get('budget_style', 'the recommended tier')} at ${top_cost}) — "
        "trading some comfort for savings."
    )


def _visa_vs_destination_tradeoff(
    visa: AgentResult | None, destination: AgentResult | None
) -> str | None:
    if not _ok(visa) or not _ok(destination):
        return None
    status = str(visa.data.get("visa_status", "")).lower()
    if not status or status in _SIMPLE_VISA_STATUSES:
        return None
    top = destination.data.get("top_option") or {}
    match_score = top.get("match_score")
    if not isinstance(match_score, (int, float)) or match_score < 0.6:
        return None
    return (
        f"Visa vs destination: {top.get('name', 'this destination')} matched your preferences well, "
        f"but entry requirements are more involved ({str(visa.data.get('visa_status', 'unknown')).replace('_', ' ')}) "
        "than a visa-free alternative would be."
    )


def _weather_vs_price_tradeoff(
    weather: AgentResult | None, budget: AgentResult | None
) -> str | None:
    if not _ok(weather):
        return None
    status = str(weather.data.get("weather_status", "")).lower()
    if not any(s in status for s in _FAVOURABLE_WEATHER):
        return None
    if not _ok(budget):
        return None
    top = budget.data.get("top_option") or {}
    style = str(top.get("budget_style", "")).lower()
    if style not in _ELEVATED_BUDGET_TIERS:
        return None
    return (
        "Weather vs price: the best weather window for this trip lines up with a higher-cost "
        f"({style}) budget tier — a shoulder-season month could lower costs at the expense of "
        "less ideal conditions."
    )


def analyse(
    results_by_module: dict[str, AgentResult], conflicts: list[str] | None = None
) -> list[str]:
    tradeoffs: list[str] = []

    for detector, agent_name in (
        (_flight_tradeoff, "flight_intelligence"),
        (_accommodation_tradeoff, "accommodation_intelligence"),
        (_budget_tradeoff, "budget_intelligence"),
    ):
        result = detector(results_by_module.get(agent_name))
        if result:
            tradeoffs.append(result)

    visa_destination = _visa_vs_destination_tradeoff(
        results_by_module.get("visa_intelligence"), results_by_module.get("destination_intelligence")
    )
    if visa_destination:
        tradeoffs.append(visa_destination)

    weather_price = _weather_vs_price_tradeoff(
        results_by_module.get("weather_intelligence"), results_by_module.get("budget_intelligence")
    )
    if weather_price:
        tradeoffs.append(weather_price)

    for conflict in conflicts or []:
        if conflict not in tradeoffs:
            tradeoffs.append(conflict)

    return tradeoffs

"""
Explanation Builder — assembles every part of the structured explanation
that isn't confidence, trade-offs, assumptions, or risks (each of those
has its own dedicated module — docs/EXPLAINABILITY_ENGINE.md).
Recommendation drivers, alternatives considered, missing information,
what-would-change, source attribution, and the one summary sentence all
read fields Discovery modules and Trip Brain already produced — nothing
here recomputes a score or invents travel logic.
"""

from __future__ import annotations

from typing import Any

from ai.shared.agent_result import AgentResult
from ai.shared.agent_status import AgentStatus

# Keyword -> which explanation field a follow-up question is really asking
# about (docs/EXPLAINABILITY_ENGINE.md's Conversation Integration section).
# First match wins; order matters for overlapping phrasing.
_QUESTION_FOCUS: tuple[tuple[tuple[str, ...], str], ...] = (
    (("cheaper", "why not", "instead of", "other option"), "tradeoffs"),
    (("assumption",), "assumptions"),
    (("confiden",), "confidence"),
    (("risk",), "risks"),
    (("change", "different answer", "what if"), "what_would_change"),
)


def focus_for_question(question: str | None) -> str | None:
    if not question:
        return None
    text = question.lower()
    for keywords, focus in _QUESTION_FOCUS:
        if any(kw in text for kw in keywords):
            return focus
    return None


def build_source_modules(results: list[AgentResult]) -> list[dict[str, str]]:
    return [{"module": r.agent_name, "status": r.status.value} for r in results]


def build_recommendation_drivers(results: list[AgentResult]) -> list[dict[str, str]]:
    drivers: list[dict[str, str]] = []
    for result in results:
        if result.status == AgentStatus.FAILED:
            continue
        driver = _driver_text(result.data)
        if driver:
            drivers.append({"module": result.agent_name, "driver": driver})
    return drivers


def _driver_text(data: dict[str, Any]) -> str:
    top = data.get("top_option")
    if isinstance(top, dict) and top.get("reasoning"):
        return str(top["reasoning"])
    if data.get("recommendation"):
        return str(data["recommendation"])
    return ""


def build_alternatives_considered(results: list[AgentResult]) -> list[dict[str, Any]]:
    alternatives: list[dict[str, Any]] = []
    for result in results:
        if result.status == AgentStatus.FAILED:
            continue
        data = result.data
        top = data.get("top_option")
        alt = data.get("alternative_option")
        if alt and top:
            alternatives.append({
                "module": result.agent_name,
                "alternative": _option_label(alt),
                "why_not_chosen": _why_not_chosen(top, alt),
            })
        count = data.get("count")
        if isinstance(count, int) and count > 1:
            alternatives.append({
                "module": result.agent_name,
                "alternative": f"{count - 1} other option(s)",
                "why_not_chosen": "Ranked below the recommended option by the module's own scoring.",
            })
    return alternatives


def _option_label(option: dict[str, Any]) -> str:
    for key in ("airline", "property_name", "name", "budget_style"):
        if option.get(key):
            return str(option[key])
    return "an alternative option"


def _why_not_chosen(top: dict[str, Any], alt: dict[str, Any]) -> str:
    top_score, alt_score = top.get("match_score"), alt.get("match_score")
    if isinstance(top_score, (int, float)) and isinstance(alt_score, (int, float)):
        return (
            f"Scored lower overall (match score {alt_score}) than the recommended "
            f"option (match score {top_score})."
        )
    return "Ranked below the recommended option."


def build_missing_information(results: list[AgentResult]) -> list[str]:
    missing: list[str] = []
    for result in results:
        for item in result.missing_information:
            if item not in missing:
                missing.append(item)
        for assumption in result.assumptions:
            lowered = assumption.lower()
            if lowered.startswith("no ") and any(
                kw in lowered for kw in ("supplied", "linked", "provided", "found", "available")
            ):
                if assumption not in missing:
                    missing.append(assumption)
    return missing


def build_what_would_change(
    missing_information: list[str],
    modules_failed: list[str],
    conflicts: list[str],
) -> list[str]:
    changes: list[str] = []
    for name in modules_failed:
        changes.append(
            f"Retrying {name}, or trying again shortly, would let it contribute to the recommendation."
        )
    for item in missing_information:
        changes.append(f"Providing the missing detail behind “{item}” would refine this recommendation.")
    for conflict in conflicts:
        changes.append(f"Resolving this in your favour would change the pick: {conflict}")
    return changes


def build_summary(
    results: list[AgentResult],
    confidence: float,
    destination: str,
    modules_failed: list[str],
    question: str | None = None,
) -> str:
    where = f" for {destination}" if destination else ""
    succeeded = [r for r in results if r.status != AgentStatus.FAILED]
    failure_clause = f", with {len(modules_failed)} unavailable" if modules_failed else ""
    base = (
        f"This recommendation{where} draws on {len(succeeded)} module(s)"
        f"{failure_clause}, at {confidence:.2f} confidence."
    )

    focus = focus_for_question(question)
    suffixes = {
        "tradeoffs": " Here's the main trade-off behind that choice.",
        "assumptions": " Here's what was assumed to reach it.",
        "confidence": " Here's why confidence is at that level.",
        "risks": " Here are the risks that shaped it.",
        "what_would_change": " Here's what could change it.",
    }
    return base + suffixes.get(focus, "")

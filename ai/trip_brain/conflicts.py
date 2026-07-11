"""
Conflict Resolution — the Coordinator resolves *presentation* conflicts
(what to say first, what to flag), never *scoring* conflicts (whose
number is right). No module's score, ranking, or label is ever
recomputed, overridden, or blended (docs/ORCHESTRATION_PATTERN.md's
Conflict Resolution section).

The one worked example that section documents — Budget Intelligence's
`BEST_OVERALL` tier disagreeing with Accommodation Intelligence's
`BEST_OVERALL` pick — is implemented here as a plain assumption appended
to the Accommodation result, never mutating either module's own output.
"""

from __future__ import annotations

from ai.shared.agent_result import AgentResult
from ai.shared.agent_status import AgentStatus

_LOW_BUDGET_TIERS = {"backpacker", "budget"}
_HIGH_STAR_RATING = 4


def detect_conflicts(module_results: dict[str, AgentResult]) -> list[str]:
    conflicts: list[str] = []

    budget = module_results.get("budget")
    accommodation = module_results.get("accommodation")
    if (
        budget is None
        or accommodation is None
        or budget.status == AgentStatus.FAILED
        or accommodation.status == AgentStatus.FAILED
    ):
        return conflicts

    budget_tier = (budget.data.get("top_option") or {}).get("budget_style", "").lower()
    star_rating = (accommodation.data.get("top_option") or {}).get("star_rating")

    if budget_tier in _LOW_BUDGET_TIERS and isinstance(star_rating, (int, float)) and star_rating >= _HIGH_STAR_RATING:
        note = (
            "Your best-value accommodation pick is above your "
            f"{budget_tier}-tier budget guidance — consider the "
            "BEST_FOR_BUDGET-labelled accommodation option instead."
        )
        conflicts.append(note)
        accommodation.assumptions.append(note)

    return conflicts

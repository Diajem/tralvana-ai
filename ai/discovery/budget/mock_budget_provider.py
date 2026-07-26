from __future__ import annotations

from typing import Any

from ai.discovery.budget.budget_cost_model import (
    CITY_REGION,
    STYLES,
    raw_budget_candidate,
    resolve_region,
)

# The five budget styles every Discovery module in this codebase already
# uses as a free-text field (Flight/Accommodation/Destination Intelligence
# request payloads). Budget Intelligence is the first module to treat these
# five styles as the candidates themselves rather than a scoring input.
STYLES = list(STYLES)


class MockBudgetProvider:
    """
    Deterministic mock budget-tier generator — no external calls.

    Same interface a real provider would implement: search(destination,
    duration_days, adults, children) -> list[dict], one raw candidate per
    budget style. Swapping in a real pricing feed later means implementing
    this method against that API and passing the instance to
    BudgetIntelligence(provider=...) — nothing downstream changes.

    Unlike Flight/Accommodation Intelligence, destination is optional: with
    no destination (or one outside the region lookup), rates fall back to
    the "default" global-average band rather than producing no candidates —
    comparing budget styles is still a useful answer without a resolved
    destination. See docs/BUDGET_INTELLIGENCE_ENGINE.md.
    """

    def search(
        self,
        destination: str | None,
        duration_days: int = 7,
        adults: int = 1,
        children: int = 0,
    ) -> list[dict[str, Any]]:
        return [
            raw_budget_candidate(
                destination=destination,
                budget_style=style,
                duration_days=duration_days,
                adults=adults,
                children=children,
            )
            for style in STYLES
        ]

    def styles(self) -> list[str]:
        return list(STYLES)

    def regions(self) -> list[str]:
        return sorted(CITY_REGION.values())

    def _region(self, destination: str | None) -> str:
        return resolve_region(destination)


mock_budget_provider = MockBudgetProvider()

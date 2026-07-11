"""
Assumption Explainer — preserves every module's own assumption text
verbatim (docs/TRIP_BRAIN_ARCHITECTURE.md's Explainability Strategy:
never regenerate or summarise away a module's own explanation). The only
transformation applied is order-preserving deduplication across modules
that happen to state the same assumption.

Also classifies assumption text into the confidence-reduction categories
docs/EXPLAINABILITY_ENGINE.md documents, using substring matching against
wording every Discovery module already uses — not a new taxonomy invented
here, just a read of existing conventions.
"""

from __future__ import annotations

from ai.shared.agent_result import AgentResult

_CATEGORY_KEYWORDS: dict[str, tuple[str, ...]] = {
    "missing traveller information": (
        "no traveller profile", "no profile", "no goal budget", "no destination",
        "no departure date", "no passport", "default cabin", "default budget",
    ),
    # Checked before "mock or incomplete provider data" — phrasing like
    # "not in the mock catalogue" contains both "mock" and a more specific
    # unknown-destination signal; the specific category should win.
    "unknown destination or rule": (
        "not in the mock catalogue", "outside every mock catalogue",
        "could not be resolved", "didn't resolve", "not covered",
    ),
    "mock or incomplete provider data": (
        "mock", "no live", "indicative only", "deterministic",
    ),
}


def collect(results: list[AgentResult]) -> list[str]:
    seen: list[str] = []
    for result in results:
        for assumption in result.assumptions:
            if assumption not in seen:
                seen.append(assumption)
    return seen


def categorize(assumption: str) -> str | None:
    text = assumption.lower()
    for category, keywords in _CATEGORY_KEYWORDS.items():
        if any(keyword in text for keyword in keywords):
            return category
    return None

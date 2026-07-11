"""
Explainability Strategy — Trip Brain adds exactly one synthesis sentence
naming *what* was checked, never *why* any module concluded what it did
(docs/TRIP_BRAIN_ARCHITECTURE.md's Explainability Strategy section). Each
module's own explanation text is preserved verbatim elsewhere
(ResponseComposer._section_for, unchanged) — this module only produces
the one preamble sentence.
"""

from __future__ import annotations

from ai.trip_brain.module_selection import ALL_MODULES

_MODULE_LABELS: dict[str, str] = {
    "destination": "destination ideas",
    "flight": "flights",
    "accommodation": "accommodation",
    "budget": "a budget breakdown",
    "visa": "an entry-requirements check",
    "weather": "a weather and safety assessment",
}


def build_synthesis_note(destination: str, modules_succeeded: list[str]) -> str:
    if not modules_succeeded:
        return ""

    succeeded_set = set(modules_succeeded)
    labels = [_MODULE_LABELS[name] for name in ALL_MODULES if name in succeeded_set]

    if len(labels) == 1:
        joined = labels[0]
    elif len(labels) == 2:
        joined = " and ".join(labels)
    else:
        joined = ", ".join(labels[:-1]) + f", and {labels[-1]}"

    where = f" for your {destination} trip" if destination else " for your trip"
    return f"Here's what I found{where}: {joined}."

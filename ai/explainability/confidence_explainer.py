"""
Confidence Explainer — converts a numeric confidence value (Trip Brain's
aggregated overall_confidence, or a single module's own confidence field)
into traveller-friendly language (docs/EXPLAINABILITY_ENGINE.md's
Confidence Explanation section).

No confidence value is computed here — this module only labels and
explains a value produced elsewhere (ai/trip_brain/confidence.py, or a
Discovery module's own scoring).
"""

from __future__ import annotations

from ai.explainability import assumption_explainer
from ai.shared.agent_result import AgentResult

_BANDS: tuple[tuple[float, str], ...] = (
    (0.90, "Very high confidence"),
    (0.75, "High confidence"),
    (0.60, "Moderate confidence"),
    (0.40, "Low confidence"),
    (0.0, "Very low confidence"),
)


def band_label(confidence: float) -> str:
    for threshold, label in _BANDS:
        if confidence >= threshold:
            return label
    return _BANDS[-1][1]


def explain(
    confidence: float,
    results: list[AgentResult],
    modules_failed: list[str] | None = None,
    conflicts: list[str] | None = None,
) -> str:
    label_with_score = f"{band_label(confidence)} ({confidence:.2f})"
    reasons: list[str] = []

    if modules_failed:
        joined = ", ".join(modules_failed)
        reasons.append(f"part of the plan ({joined}) could not be completed")

    if conflicts:
        reasons.append("some module results disagreed with each other")

    categories_found: list[str] = []
    for result in results:
        for assumption in result.assumptions:
            category = assumption_explainer.categorize(assumption)
            if category and category not in categories_found:
                categories_found.append(category)
    reasons.extend(categories_found)

    if not reasons and any(r.assumptions for r in results):
        reasons.append("some assumptions were applied to fill in missing details")

    if not reasons:
        return f"{label_with_score}."
    return f"{label_with_score} — " + "; ".join(reasons) + "."

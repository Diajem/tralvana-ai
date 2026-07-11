"""
Confidence Aggregation — second-order aggregation over values every
Discovery module already produces, not a new scoring model
(docs/TRIP_BRAIN_ARCHITECTURE.md's Confidence Propagation section):

    overall_confidence = weighted_average(per_module_confidence,
                                           weight=module_relevance)
                          x completion_penalty

`module_relevance` is the weight ModuleSelector assigned when a module was
selected. `completion_penalty` reduces confidence proportionally to how
many selected modules failed — a fully-succeeded request is not
penalized, a partially-succeeded one is.
"""

from __future__ import annotations


def aggregate_confidence(
    confidences: dict[str, float],
    weights: dict[str, float],
    succeeded: list[str],
) -> float:
    selected = list(confidences.keys())
    if not selected:
        return 0.0

    succeeded_set = set(succeeded)
    weight_total = sum(weights[name] for name in succeeded_set)
    if weight_total == 0:
        return 0.0

    weighted_sum = sum(confidences[name] * weights[name] for name in succeeded_set)
    base = weighted_sum / weight_total
    completion_penalty = len(succeeded) / len(selected)

    return round(base * completion_penalty, 2)

"""
Explainability Engine — turns module-level reasoning from the Discovery
Layer and Trip Brain into one traveller-facing structured explanation.

Reuses existing reasoning only — never invents new travel logic, never
recalculates a Discovery module's score. See docs/EXPLAINABILITY_ENGINE.md
and docs/ADR/ADR-019-explainability-engine.md.
"""

from ai.explainability.explainability_engine import ExplainabilityEngine, explainability_engine

__all__ = ["ExplainabilityEngine", "explainability_engine"]

"""
Explainability Engine — the single entry point that turns module-level
reasoning (Discovery module AgentResults, optionally already merged by
Trip Brain) into one traveller-facing structured explanation
(docs/EXPLAINABILITY_ENGINE.md).

Reuses existing reasoning only: every field below is read from
AgentResult.data/assumptions/risks/missing_information, or from values
Trip Brain already computed (overall_confidence, conflicts). Nothing here
scores, ranks, or recalculates anything a Discovery module or Trip Brain
already decided — docs/ADR/ADR-019-explainability-engine.md.
"""

from __future__ import annotations

from typing import Any

from ai.explainability import (
    assumption_explainer,
    confidence_explainer,
    explanation_builder,
    risk_explainer,
    tradeoff_analyser,
)
from ai.shared.agent_result import AgentResult
from ai.shared.agent_status import AgentStatus


class ExplainabilityEngine:
    def explain(
        self,
        results: list[AgentResult] | None,
        *,
        overall_confidence: float | None = None,
        modules_selected: list[str] | None = None,
        modules_failed: list[str] | None = None,
        conflicts: list[str] | None = None,
        destination: str = "",
        question: str | None = None,
    ) -> dict[str, Any]:
        results = results or []
        modules_failed = (
            modules_failed
            if modules_failed is not None
            else [r.agent_name for r in results if r.status == AgentStatus.FAILED]
        )
        # modules_selected isn't part of the returned dict (source_modules,
        # built from `results`, already carries every module attempted and
        # its status) but is accepted so Trip Brain's UnifiedRecommendation
        # can be passed through wholesale without the caller filtering it.
        del modules_selected
        conflicts = conflicts or []
        confidence = (
            overall_confidence if overall_confidence is not None else self._mean_confidence(results)
        )

        by_module = {r.agent_name: r for r in results}

        assumptions = assumption_explainer.collect(results)
        risks = risk_explainer.collect(results, modules_failed)
        tradeoffs = tradeoff_analyser.analyse(by_module, conflicts)
        confidence_explanation = confidence_explainer.explain(confidence, results, modules_failed, conflicts)
        missing_information = explanation_builder.build_missing_information(results)
        drivers = explanation_builder.build_recommendation_drivers(results)
        alternatives = explanation_builder.build_alternatives_considered(results)
        what_would_change = explanation_builder.build_what_would_change(
            missing_information, modules_failed, conflicts
        )
        source_modules = explanation_builder.build_source_modules(results)
        summary = explanation_builder.build_summary(results, confidence, destination, modules_failed, question)

        return {
            "summary": summary,
            "recommendation_drivers": drivers,
            "tradeoffs": tradeoffs,
            "assumptions": assumptions,
            "risks": risks,
            "missing_information": missing_information,
            "confidence": confidence,
            "confidence_explanation": confidence_explanation,
            "alternatives_considered": alternatives,
            "what_would_change_the_result": what_would_change,
            "source_modules": source_modules,
        }

    def answer_question(self, explanation: dict[str, Any], question: str) -> str:
        """
        Format one of the explanation's own fields into a short chat reply
        for a conversational follow-up (docs/EXPLAINABILITY_ENGINE.md's
        Conversation Integration section). Never generates new content —
        every sentence returned here already exists in `explanation`.
        """
        focus = explanation_builder.focus_for_question(question)

        if focus == "tradeoffs" and explanation["tradeoffs"]:
            return explanation["summary"] + "\n\n" + "\n".join(f"- {t}" for t in explanation["tradeoffs"])
        if focus == "assumptions" and explanation["assumptions"]:
            return explanation["summary"] + "\n\n" + "\n".join(f"- {a}" for a in explanation["assumptions"])
        if focus == "confidence":
            return explanation["summary"] + "\n\n" + explanation["confidence_explanation"]
        if focus == "risks" and explanation["risks"]:
            return explanation["summary"] + "\n\n" + "\n".join(f"- {r}" for r in explanation["risks"])
        if focus == "what_would_change" and explanation["what_would_change_the_result"]:
            return (
                explanation["summary"]
                + "\n\n"
                + "\n".join(f"- {c}" for c in explanation["what_would_change_the_result"])
            )

        drivers = explanation["recommendation_drivers"]
        if drivers:
            lines = [f"- **{d['module']}:** {d['driver']}" for d in drivers]
            return explanation["summary"] + "\n\n" + "\n".join(lines)
        return explanation["summary"]

    def _mean_confidence(self, results: list[AgentResult]) -> float:
        succeeded = [r for r in results if r.status != AgentStatus.FAILED]
        if not succeeded:
            return 0.0
        return round(sum(r.confidence for r in succeeded) / len(succeeded), 2)


explainability_engine = ExplainabilityEngine()

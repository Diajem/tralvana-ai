"""
POST /explain — the Explainability Engine's HTTP surface
(docs/API_EXPLAINABILITY.md). Three ways to ask for an explanation, tried
in order: explicit module_results, a conversation_id (looks up the
conversation's cached Trip Brain result), or a trip_id (same lookup, keyed
by trip instead of conversation). Never re-runs a Discovery module or Trip
Brain — it only reads and explains what already ran.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(tags=["explainability"])


class ModuleResultInput(BaseModel):
    agent_name: str
    status: str = "success"
    confidence: float = 0.0
    data: dict[str, Any] = {}
    assumptions: list[str] = []
    missing_information: list[str] = []
    risks: list[str] = []
    recommendations: list[str] = []
    next_actions: list[str] = []


class ExplainRequest(BaseModel):
    conversation_id: str | None = None
    trip_id: str | None = None
    module_results: list[ModuleResultInput] | None = None
    question: str | None = None


class SourceModule(BaseModel):
    module: str
    status: str


class RecommendationDriver(BaseModel):
    module: str
    driver: str


class AlternativeConsidered(BaseModel):
    module: str
    alternative: str
    why_not_chosen: str


class ExplanationResponse(BaseModel):
    summary: str
    recommendation_drivers: list[RecommendationDriver]
    tradeoffs: list[str]
    assumptions: list[str]
    risks: list[str]
    missing_information: list[str]
    confidence: float
    confidence_explanation: str
    alternatives_considered: list[AlternativeConsidered]
    what_would_change_the_result: list[str]
    source_modules: list[SourceModule]


@router.post("/explain", response_model=ExplanationResponse)
async def explain(request: ExplainRequest) -> dict:
    from ai.explainability.explainability_engine import explainability_engine
    from ai.shared.agent_result import AgentResult
    from ai.shared.agent_status import AgentStatus

    if request.module_results:
        try:
            results = [
                AgentResult(
                    agent_name=m.agent_name,
                    status=AgentStatus(m.status),
                    confidence=m.confidence,
                    data=m.data,
                    assumptions=m.assumptions,
                    missing_information=m.missing_information,
                    risks=m.risks,
                    recommendations=m.recommendations,
                    next_actions=m.next_actions,
                )
                for m in request.module_results
            ]
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=f"Invalid module result: {exc}") from exc

        return explainability_engine.explain(results, question=request.question)

    from ai.concierge.conversation_engine import conversation_engine

    session = None
    if request.conversation_id:
        session = conversation_engine.get_session(request.conversation_id)
    if session is None and request.trip_id:
        session = conversation_engine.get_session_by_trip_id(request.trip_id)

    if session is None or session.last_recommendation is None:
        raise HTTPException(
            status_code=404,
            detail="No recommendation found to explain — provide module_results, "
            "or a conversation_id/trip_id with a prior PLAN_TRIP result.",
        )

    unified = session.last_recommendation
    explanation = dict(unified.explanation)
    if request.question:
        # Re-derive only the question-sensitive summary line — every other
        # field is the same structured data Trip Brain already computed.
        from ai.explainability import explanation_builder

        explanation["summary"] = explanation_builder.build_summary(
            unified.results, unified.overall_confidence, unified.destination,
            unified.modules_failed, request.question,
        )
    return explanation

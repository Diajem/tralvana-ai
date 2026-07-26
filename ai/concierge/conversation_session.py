"""Conversation session domain model and stable JSON representation."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Any

from ai.shared.agent_result import AgentResult
from ai.shared.agent_status import AgentStatus
from ai.trip_brain.models import UnifiedRecommendation

SESSION_SCHEMA_VERSION = 1


@dataclass
class ConversationMessage:
    role: str  # user | assistant | system
    content: str
    timestamp: str
    intent: str | None = None


@dataclass
class ConversationSession:
    conversation_id: str
    created_at: str
    updated_at: str
    traveller_id: str | None = None
    trip_id: str | None = None
    goal_id: str | None = None
    history: list[ConversationMessage] = field(default_factory=list)
    active_goal: str | None = None
    pending_questions: list[str] = field(default_factory=list)
    planning_entities: dict[str, str] = field(default_factory=dict)
    context_summary: str = ""
    last_recommendation: UnifiedRecommendation | None = None

    def add_message(self, role: str, content: str, intent: str | None = None) -> None:
        now = datetime.now(timezone.utc).isoformat()
        self.history.append(
            ConversationMessage(role=role, content=content, timestamp=now, intent=intent)
        )
        self.updated_at = now


def serialize_session(session: ConversationSession) -> str:
    """Encode a session without pickle or implementation-specific objects."""
    payload = {
        "schema_version": SESSION_SCHEMA_VERSION,
        "conversation_id": session.conversation_id,
        "created_at": session.created_at,
        "updated_at": session.updated_at,
        "traveller_id": session.traveller_id,
        "trip_id": session.trip_id,
        "goal_id": session.goal_id,
        "history": [
            {
                "role": message.role,
                "content": message.content,
                "timestamp": message.timestamp,
                "intent": message.intent,
            }
            for message in session.history
        ],
        "active_goal": session.active_goal,
        "pending_questions": session.pending_questions,
        "planning_entities": session.planning_entities,
        "context_summary": session.context_summary,
        "last_recommendation": _recommendation_to_dict(session.last_recommendation),
    }
    return json.dumps(
        payload,
        default=_json_default,
        separators=(",", ":"),
        sort_keys=True,
    )


def deserialize_session(payload: str | bytes) -> ConversationSession:
    """Restore a session and reject unsupported or malformed records."""
    if isinstance(payload, bytes):
        payload = payload.decode("utf-8")
    data = json.loads(payload)
    if not isinstance(data, dict):
        raise ValueError("conversation session payload must be an object")
    if data.get("schema_version") != SESSION_SCHEMA_VERSION:
        raise ValueError("unsupported conversation session schema")

    history_data = data.get("history", [])
    if not isinstance(history_data, list):
        raise ValueError("conversation session history must be a list")

    recommendation_data = data.get("last_recommendation")
    return ConversationSession(
        conversation_id=_required_string(data, "conversation_id"),
        created_at=_required_string(data, "created_at"),
        updated_at=_required_string(data, "updated_at"),
        traveller_id=_optional_string(data.get("traveller_id")),
        trip_id=_optional_string(data.get("trip_id")),
        goal_id=_optional_string(data.get("goal_id")),
        history=[
            ConversationMessage(
                role=_required_string(item, "role"),
                content=_required_string(item, "content"),
                timestamp=_required_string(item, "timestamp"),
                intent=_optional_string(item.get("intent")),
            )
            for item in history_data
            if isinstance(item, dict)
        ],
        active_goal=_optional_string(data.get("active_goal")),
        pending_questions=_string_list(data.get("pending_questions", [])),
        planning_entities=_string_dict(data.get("planning_entities", {})),
        context_summary=str(data.get("context_summary", "")),
        last_recommendation=(
            _recommendation_from_dict(recommendation_data)
            if isinstance(recommendation_data, dict)
            else None
        ),
    )


def _recommendation_to_dict(
    recommendation: UnifiedRecommendation | None,
) -> dict[str, Any] | None:
    if recommendation is None:
        return None
    return {
        "results": [result.to_dict() for result in recommendation.results],
        "modules_selected": recommendation.modules_selected,
        "modules_succeeded": recommendation.modules_succeeded,
        "modules_failed": recommendation.modules_failed,
        "overall_confidence": recommendation.overall_confidence,
        "synthesis_note": recommendation.synthesis_note,
        "conflicts": recommendation.conflicts,
        "explanation": recommendation.explanation,
        "destination": recommendation.destination,
    }


def _recommendation_from_dict(data: dict[str, Any]) -> UnifiedRecommendation:
    results_data = data.get("results", [])
    if not isinstance(results_data, list):
        raise ValueError("recommendation results must be a list")
    return UnifiedRecommendation(
        results=[
            AgentResult(
                agent_name=_required_string(item, "agent_name"),
                status=AgentStatus(_required_string(item, "status")),
                confidence=float(item.get("confidence", 0.0)),
                data=_dict(item.get("data", {})),
                assumptions=_string_list(item.get("assumptions", [])),
                missing_information=_string_list(item.get("missing_information", [])),
                risks=_string_list(item.get("risks", [])),
                recommendations=_string_list(item.get("recommendations", [])),
                next_actions=_string_list(item.get("next_actions", [])),
            )
            for item in results_data
            if isinstance(item, dict)
        ],
        modules_selected=_string_list(data.get("modules_selected", [])),
        modules_succeeded=_string_list(data.get("modules_succeeded", [])),
        modules_failed=_string_list(data.get("modules_failed", [])),
        overall_confidence=float(data.get("overall_confidence", 0.0)),
        synthesis_note=str(data.get("synthesis_note", "")),
        conflicts=_string_list(data.get("conflicts", [])),
        explanation=_dict(data.get("explanation", {})),
        destination=str(data.get("destination", "")),
    )


def _required_string(data: dict[str, Any], key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"conversation session field {key!r} must be a non-empty string")
    return value


def _optional_string(value: Any) -> str | None:
    return value if isinstance(value, str) else None


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        raise ValueError("conversation session field must be a list")
    return [str(item) for item in value]


def _string_dict(value: Any) -> dict[str, str]:
    if not isinstance(value, dict):
        raise ValueError("conversation session field must be an object")
    return {str(key): str(item) for key, item in value.items()}


def _dict(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError("conversation session field must be an object")
    return value


def _json_default(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    raise TypeError(f"{type(value).__name__} is not JSON serializable")

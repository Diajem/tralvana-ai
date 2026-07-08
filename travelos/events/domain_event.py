from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class DomainEvent:
    """
    Base class for all TravelOS domain events.

    Every event carries a unique ID and UTC timestamp.
    Concrete events add domain-specific fields.
    """

    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    occurred_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    payload: dict[str, Any] = field(default_factory=dict)

    @property
    def event_type(self) -> str:
        return self.__class__.__name__

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "occurred_at": self.occurred_at,
            "payload": self.payload,
        }


# ---------------------------------------------------------------------------
# Traveller events
# ---------------------------------------------------------------------------

@dataclass
class TravellerCreated(DomainEvent):
    traveller_id: str = ""
    name: str = ""
    home_city: str = ""
    nationality: str = ""

    def to_dict(self) -> dict[str, Any]:
        d = super().to_dict()
        d["payload"].update({
            "traveller_id": self.traveller_id,
            "name": self.name,
            "home_city": self.home_city,
            "nationality": self.nationality,
        })
        return d


# ---------------------------------------------------------------------------
# Goal events
# ---------------------------------------------------------------------------

@dataclass
class GoalCreated(DomainEvent):
    goal_id: str = ""
    traveller_id: str = ""
    goal_type: str = ""
    title: str = ""

    def to_dict(self) -> dict[str, Any]:
        d = super().to_dict()
        d["payload"].update({
            "goal_id": self.goal_id,
            "traveller_id": self.traveller_id,
            "goal_type": self.goal_type,
            "title": self.title,
        })
        return d


# ---------------------------------------------------------------------------
# Trip events
# ---------------------------------------------------------------------------

@dataclass
class TripPlanned(DomainEvent):
    trip_id: str = ""
    traveller_id: str = ""
    destination: str = ""
    duration_days: int = 0
    status: str = ""
    confidence: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        d = super().to_dict()
        d["payload"].update({
            "trip_id": self.trip_id,
            "traveller_id": self.traveller_id,
            "destination": self.destination,
            "duration_days": self.duration_days,
            "status": self.status,
            "confidence": self.confidence,
        })
        return d


# ---------------------------------------------------------------------------
# Conversation events
# ---------------------------------------------------------------------------

@dataclass
class ConversationStarted(DomainEvent):
    conversation_id: str = ""
    traveller_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        d = super().to_dict()
        d["payload"].update({
            "conversation_id": self.conversation_id,
            "traveller_id": self.traveller_id,
        })
        return d


@dataclass
class ConversationCompleted(DomainEvent):
    conversation_id: str = ""
    intent: str = ""
    confidence: float = 0.0
    trip_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        d = super().to_dict()
        d["payload"].update({
            "conversation_id": self.conversation_id,
            "intent": self.intent,
            "confidence": self.confidence,
            "trip_id": self.trip_id,
        })
        return d


# ---------------------------------------------------------------------------
# Knowledge events
# ---------------------------------------------------------------------------

@dataclass
class KnowledgeUpdated(DomainEvent):
    entity_type: str = ""
    entity_id: str = ""
    update_type: str = ""  # added | updated | removed

    def to_dict(self) -> dict[str, Any]:
        d = super().to_dict()
        d["payload"].update({
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "update_type": self.update_type,
        })
        return d

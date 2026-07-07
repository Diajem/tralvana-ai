import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


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
    history: list[ConversationMessage] = field(default_factory=list)
    active_goal: str | None = None
    pending_questions: list[str] = field(default_factory=list)
    context_summary: str = ""

    def add_message(self, role: str, content: str, intent: str | None = None) -> None:
        now = datetime.now(timezone.utc).isoformat()
        self.history.append(
            ConversationMessage(role=role, content=content, timestamp=now, intent=intent)
        )
        self.updated_at = now

    def to_dict(self) -> dict[str, Any]:
        return {
            "conversation_id": self.conversation_id,
            "traveller_id": self.traveller_id,
            "trip_id": self.trip_id,
            "active_goal": self.active_goal,
            "pending_questions": self.pending_questions,
            "context_summary": self.context_summary,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "message_count": len(self.history),
        }


class ConversationStore:
    """In-memory session store. Swapped for Redis or DB in Sprint 3."""

    def __init__(self) -> None:
        self._sessions: dict[str, ConversationSession] = {}

    def create(self, traveller_id: str | None = None) -> ConversationSession:
        now = datetime.now(timezone.utc).isoformat()
        session = ConversationSession(
            conversation_id=str(uuid.uuid4()),
            created_at=now,
            updated_at=now,
            traveller_id=traveller_id,
        )
        self._sessions[session.conversation_id] = session
        return session

    def get(self, conversation_id: str) -> ConversationSession | None:
        return self._sessions.get(conversation_id)

    def save(self, session: ConversationSession) -> None:
        self._sessions[session.conversation_id] = session


conversation_store = ConversationStore()

import uuid
from dataclasses import dataclass, field
from typing import Any


@dataclass
class AgentContext:
    session_id: str
    traveller_id: str | None = None
    traveller_profile: dict[str, Any] | None = None
    intent: str | None = None
    entities: dict[str, str] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


def new_context(traveller_id: str | None = None) -> AgentContext:
    return AgentContext(
        session_id=str(uuid.uuid4()),
        traveller_id=traveller_id,
    )

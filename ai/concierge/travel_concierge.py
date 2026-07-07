from typing import Any

from ai.concierge.conversation_engine import ConversationEngine, conversation_engine
from ai.concierge.response_composer import ResponseComposer


class TravelConcierge:
    """
    Single AI entry point for all traveller interactions.

    Every conversation message flows through here — no code should call
    the ConversationEngine, TravelManager, or specialist agents directly.

    This is the stable public interface that the API layer depends on.
    Internal implementation (engine, agents, registry) can change without
    touching the API layer.
    """

    def __init__(self, engine: ConversationEngine | None = None) -> None:
        self._engine = engine or conversation_engine
        self._composer = ResponseComposer()

    async def handle(
        self,
        message: str,
        traveller_id: str | None = None,
        conversation_id: str | None = None,
    ) -> dict[str, Any]:
        """Process a traveller message end-to-end and return a structured reply."""
        return await self._engine.process(message, traveller_id, conversation_id)

    def greeting(self, traveller_name: str | None = None) -> str:
        """Return an opening greeting for new conversations."""
        return self._composer.compose_greeting(traveller_name)


travel_concierge = TravelConcierge()

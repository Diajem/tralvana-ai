from typing import Any

from app.conversation.conversation_session import ConversationSession, ConversationStore, conversation_store
from app.conversation.intent_classifier import ClassifiedIntent, IntentClassifier
from app.conversation.response_composer import ResponseComposer


class ConversationEngine:
    """
    Central state machine for traveller conversations.

    Responsibilities:
    - Create and restore conversation sessions.
    - Classify intent on every turn.
    - Track active goal and pending clarification questions.
    - Dispatch to specialist agents via the Orchestrator.
    - Compose and return natural-language replies.
    """

    def __init__(
        self,
        store: ConversationStore,
        classifier: IntentClassifier,
        composer: ResponseComposer,
    ) -> None:
        self._store = store
        self._classifier = classifier
        self._composer = composer

    def start_session(self, traveller_id: str | None = None) -> ConversationSession:
        return self._store.create(traveller_id)

    def get_session(self, conversation_id: str) -> ConversationSession | None:
        return self._store.get(conversation_id)

    async def process_message(
        self, conversation_id: str, message: str
    ) -> dict[str, Any]:
        session = self._store.get(conversation_id)
        if not session:
            return {"error": "Session not found", "conversation_id": conversation_id}

        classified = self._classifier.classify(message)
        session.add_message("user", message, intent=classified.intent)
        self._update_goal(session, classified)

        reply = await self._dispatch(session, message, classified)

        session.add_message("assistant", reply, intent=classified.intent)
        self._store.save(session)

        return {
            "conversation_id": conversation_id,
            "reply": reply,
            "intent": classified.intent,
            "confidence": classified.confidence,
            "entities": classified.entities,
            "active_goal": session.active_goal,
            "pending_questions": session.pending_questions,
        }

    # ------------------------------------------------------------------
    # Dispatcher
    # ------------------------------------------------------------------

    async def _dispatch(
        self,
        session: ConversationSession,
        message: str,
        classified: ClassifiedIntent,
    ) -> str:
        intent = classified.intent
        name = self._get_traveller_name(session)

        if intent == "plan_trip":
            return await self._handle_plan_trip(session, classified, name)

        if intent == "modify_trip":
            session.pending_questions = [
                "Which trip would you like to modify?",
                "What change do you need?",
            ]
            return self._composer.compose_clarification(session.pending_questions)

        return self._composer.compose(intent, None, name, session.pending_questions or None)

    # ------------------------------------------------------------------
    # Handlers
    # ------------------------------------------------------------------

    async def _handle_plan_trip(
        self,
        session: ConversationSession,
        classified: ClassifiedIntent,
        traveller_name: str | None,
    ) -> str:
        destination = classified.entities.get("destination")

        if not destination:
            session.pending_questions = [
                "Where would you like to go?",
                "When are you planning to travel?",
            ]
            return self._composer.compose_clarification(session.pending_questions)

        session.pending_questions = []

        try:
            from ai.orchestration.orchestrator import default_orchestrator
            result = await default_orchestrator.run(
                "travel_manager",
                {
                    "destination": destination,
                    "dates": {"hint": classified.entities.get("date_hint")},
                },
                traveller_id=session.traveller_id,
            )
            return self._composer.compose("plan_trip", result.output, traveller_name)
        except Exception as exc:
            return self._composer.compose_error(str(exc))

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _update_goal(self, session: ConversationSession, classified: ClassifiedIntent) -> None:
        goal_intents = {"plan_trip", "modify_trip", "view_profile", "update_preferences"}
        if classified.intent in goal_intents:
            session.active_goal = classified.intent

    def _get_traveller_name(self, session: ConversationSession) -> str | None:
        if not session.traveller_id:
            return None
        try:
            from ai.memory.traveller_intelligence_service import traveller_intelligence_service
            data = traveller_intelligence_service.build_context_data(session.traveller_id)
            if data:
                return data.get("identity", {}).get("name")
        except Exception:
            pass
        return None


conversation_engine = ConversationEngine(
    store=conversation_store,
    classifier=IntentClassifier(),
    composer=ResponseComposer(),
)

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from ai.concierge.decision_engine import Decision, DecisionEngine
from ai.concierge.intent_classifier import Intent, IntentClassifier
from ai.concierge.response_composer import ResponseComposer
from ai.manager.travel_manager import travel_manager
from ai.shared.agent_context import AgentContext
from ai.shared.agent_result import AgentResult


# ---------------------------------------------------------------------------
# Session model
# ---------------------------------------------------------------------------

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


class _SessionStore:
    def __init__(self) -> None:
        self._sessions: dict[str, ConversationSession] = {}

    def create(self, traveller_id: str | None = None) -> ConversationSession:
        now = datetime.now(timezone.utc).isoformat()
        s = ConversationSession(
            conversation_id=str(uuid.uuid4()),
            created_at=now,
            updated_at=now,
            traveller_id=traveller_id,
        )
        self._sessions[s.conversation_id] = s
        return s

    def get_or_create(
        self, conversation_id: str | None, traveller_id: str | None
    ) -> ConversationSession:
        if conversation_id and conversation_id in self._sessions:
            s = self._sessions[conversation_id]
            if traveller_id and not s.traveller_id:
                s.traveller_id = traveller_id
            return s
        return self.create(traveller_id)

    def save(self, session: ConversationSession) -> None:
        self._sessions[session.conversation_id] = session


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class ConversationEngine:
    """
    Central state machine for the TravelOS conversation layer.

    Per-turn flow:
    1. Restore or create session.
    2. Classify intent.
    3. Fetch traveller profile.
    4. Run DecisionEngine.
    5. Dispatch to TravelManager (if ready).
    6. Compose response via ResponseComposer.
    7. Persist session.
    """

    def __init__(self) -> None:
        self._store = _SessionStore()
        self._classifier = IntentClassifier()
        self._decision = DecisionEngine()
        self._composer = ResponseComposer()

    async def process(
        self,
        message: str,
        traveller_id: str | None = None,
        conversation_id: str | None = None,
    ) -> dict[str, Any]:
        session = self._store.get_or_create(conversation_id, traveller_id)
        session.add_message("user", message)

        classified = self._classifier.classify(message)
        profile = self._fetch_profile(session.traveller_id)
        traveller_name = profile.get("identity", {}).get("name") if profile else None

        decision = self._decision.decide(classified.intent, classified.entities, profile)
        self._update_session(session, classified.intent, decision)

        results: list[AgentResult] = []
        if decision.has_enough_information and decision.requires_agents:
            ctx = AgentContext(
                session_id=session.conversation_id,
                traveller_id=session.traveller_id,
                traveller_profile=profile,
                intent=classified.intent.value,
                entities=classified.entities,
            )
            results = await travel_manager.execute(
                classified.intent,
                ctx,
                decision,
                {
                    "destination": classified.entities.get("destination", ""),
                    "dates": {"hint": classified.entities.get("date_hint")},
                },
            )

        response_text = self._composer.compose(
            classified.intent, decision, results, traveller_name
        )
        session.add_message("assistant", response_text, intent=classified.intent.value)
        self._store.save(session)

        return self._build_output(session, classified, decision, results, response_text)

    # ------------------------------------------------------------------

    def _build_output(
        self,
        session: ConversationSession,
        classified: Any,
        decision: Decision,
        results: list[AgentResult],
        response_text: str,
    ) -> dict[str, Any]:
        all_assumptions = list(decision.assumptions)
        all_missing = list(decision.follow_up_questions)
        all_next_actions: list[str] = []

        for r in results:
            all_assumptions.extend(r.assumptions)
            all_missing.extend(r.missing_information)
            all_next_actions.extend(r.next_actions)

        # Average agent confidence when agents ran; fall back to classifier confidence.
        if results:
            confidence = sum(r.confidence for r in results) / len(results)
        else:
            confidence = classified.confidence

        return {
            "conversation_id": session.conversation_id,
            "intent": classified.intent.value,
            "response": response_text,
            "confidence": round(confidence, 2),
            "assumptions": all_assumptions,
            "missing_information": all_missing,
            "next_actions": list(dict.fromkeys(all_next_actions)),  # deduplicate, preserve order
            "recommended_agents": decision.requires_agents,
        }

    def _update_session(
        self, session: ConversationSession, intent: Intent, decision: Decision
    ) -> None:
        goal_intents = {
            Intent.PLAN_TRIP, Intent.MODIFY_TRIP,
            Intent.VIEW_PROFILE, Intent.UPDATE_PREFERENCES,
        }
        if intent in goal_intents:
            session.active_goal = intent.value
        session.pending_questions = decision.follow_up_questions

    def _fetch_profile(self, traveller_id: str | None) -> dict[str, Any] | None:
        if not traveller_id:
            return None
        try:
            from ai.memory.traveller_intelligence_service import traveller_intelligence_service
            return traveller_intelligence_service.build_context_data(traveller_id)
        except Exception:
            return None


conversation_engine = ConversationEngine()

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from ai.concierge.decision_engine import Decision, DecisionEngine
from ai.concierge.intent_classifier import Intent, IntentClassifier
from ai.concierge.response_composer import ResponseComposer
from ai.explainability.explainability_engine import explainability_engine
from ai.manager.travel_manager import travel_manager
from ai.shared.agent_context import AgentContext
from ai.shared.agent_result import AgentResult
from ai.shared.agent_status import AgentStatus
from ai.trip_brain.coordinator import trip_brain
from ai.trip_brain.models import UnifiedRecommendation


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
    goal_id: str | None = None
    history: list[ConversationMessage] = field(default_factory=list)
    active_goal: str | None = None
    pending_questions: list[str] = field(default_factory=list)
    context_summary: str = ""
    # The most recent Trip Brain result for this conversation, cached so
    # EXPLAIN_RECOMMENDATION follow-ups (and POST /explain) can reuse it
    # without re-running the six Discovery modules
    # (docs/EXPLAINABILITY_ENGINE.md's Conversation Integration section).
    # Narrow, single-module intents don't populate this — only PLAN_TRIP.
    last_recommendation: UnifiedRecommendation | None = None

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

    def get(self, conversation_id: str) -> ConversationSession | None:
        return self._sessions.get(conversation_id)

    def find_by_trip_id(self, trip_id: str) -> ConversationSession | None:
        return next((s for s in self._sessions.values() if s.trip_id == trip_id), None)


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

        # Attach a Goal to PLAN_TRIP conversations that don't yet have one
        if classified.intent == Intent.PLAN_TRIP and not session.goal_id:
            session.goal_id = self._create_goal(session, message, classified.entities)

        results: list[AgentResult] = []
        # Generate a Trip Plan when destination + date are known
        if (
            classified.intent == Intent.PLAN_TRIP
            and decision.has_enough_information
            and not session.trip_id
        ):
            session.trip_id = self._create_trip(session, classified.entities, profile)

        # Flight-related requests route directly to Flight Intelligence
        # (ai/discovery/flights/), not through the specialist-agent registry.
        if classified.intent == Intent.FLIGHT_SEARCH and decision.has_enough_information:
            flight_result = self._get_flight_recommendations(session, classified.entities, profile)
            if flight_result:
                results = [flight_result]

        # Accommodation-related requests route directly to Accommodation
        # Intelligence (ai/discovery/accommodation/), same pattern as flights.
        if classified.intent == Intent.ACCOMMODATION_SEARCH and decision.has_enough_information:
            accommodation_result = self._get_accommodation_recommendations(
                session, classified.entities, profile
            )
            if accommodation_result:
                results = [accommodation_result]

        # Destination-discovery requests route directly to Destination
        # Intelligence (ai/discovery/destinations/), same pattern as flights
        # and accommodation. Always ready — no destination is required since
        # the "no city" catalogue mode is itself a valid, useful response.
        if classified.intent == Intent.DESTINATION_DISCOVERY:
            destination_result = self._get_destination_recommendations(
                session, classified.entities, profile
            )
            if destination_result:
                results = [destination_result]

        # Budget-analysis requests route directly to Budget Intelligence
        # (ai/discovery/budget/), same pattern as flights, accommodation,
        # and destinations. Always ready — no destination is required since
        # comparing tiers at default global rates is itself a useful answer.
        if classified.intent == Intent.BUDGET_ANALYSIS:
            budget_result = self._get_budget_recommendations(
                session, classified.entities, profile
            )
            if budget_result:
                results = [budget_result]

        # Visa-check requests route directly to Visa Intelligence
        # (ai/discovery/visa/), same pattern as flights and accommodation.
        # Unlike Budget/Destination, both nationality and destination are
        # required before a real assessment can be produced.
        if classified.intent == Intent.VISA_CHECK and decision.has_enough_information:
            visa_result = self._get_visa_assessment(
                session, classified.entities, profile
            )
            if visa_result:
                results = [visa_result]

        # Weather-analysis requests route directly to Weather Intelligence
        # (ai/discovery/weather/), same pattern as flights and accommodation.
        # Only a destination is required — an omitted month finds the best
        # month to visit, same "useful either way" idea as Destination
        # Intelligence's city vs. no-city dual mode.
        if classified.intent == Intent.WEATHER_ANALYSIS and decision.has_enough_information:
            weather_result = self._get_weather_assessment(
                session, classified.entities, profile
            )
            if weather_result:
                results = [weather_result]

        synthesis_note: str | None = None
        confidence_override: float | None = None

        # PLAN_TRIP — the broad-planning intent — routes through Trip Brain
        # (ai/trip_brain/), which calls the six real Discovery modules
        # directly, instead of TravelManager's placeholder specialist
        # agents. See docs/ADR/ADR-017-trip-brain.md and ADR-018. Below,
        # TravelManager / AgentRegistry remain the live dispatcher for
        # MODIFY_TRIP, DESTINATION_QUESTION, TRAVEL_ADVICE, and
        # BUDGET_ADVICE — they were never made unused, only bypassed for
        # PLAN_TRIP specifically (T-023 investigated full retirement and
        # found this branch still load-bearing; see ADR-018).
        if classified.intent == Intent.PLAN_TRIP and decision.has_enough_information:
            unified = await trip_brain.plan(
                traveller_id=session.traveller_id,
                trip_id=session.trip_id,
                goal_id=session.goal_id,
                entities=classified.entities,
                profile=profile,
            )
            results = unified.results
            synthesis_note = unified.synthesis_note
            confidence_override = unified.overall_confidence
            session.last_recommendation = unified
        elif decision.has_enough_information and decision.requires_agents:
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

        # EXPLAIN_RECOMMENDATION — a follow-up about the most recent Trip
        # Brain result in this conversation (ai/explainability/). Never
        # re-runs any Discovery module or Trip Brain — it only reads and
        # phrases what session.last_recommendation already computed
        # (docs/EXPLAINABILITY_ENGINE.md's Conversation Integration
        # section). response_text is composed directly by
        # ExplainabilityEngine.answer_question() rather than
        # ResponseComposer.compose() — compose() would re-render every
        # module's full section verbatim on every follow-up (its
        # `_section_for` loop over `results`), which buries the actual
        # answer under a repeat of the original PLAN_TRIP response.
        # `results` is still kept so assumptions/missing_information from
        # the underlying recommendation continue to populate the response
        # envelope below (_build_output) — only the chat text bypasses
        # ResponseComposer, which is otherwise unchanged for every intent.
        response_text: str | None = None
        if classified.intent == Intent.EXPLAIN_RECOMMENDATION:
            if session.last_recommendation is None:
                response_text = (
                    "I don't have a recent recommendation to explain yet — ask me to plan "
                    "a trip, and I'll be able to walk you through why once I have."
                )
            else:
                results = session.last_recommendation.results
                response_text = explainability_engine.answer_question(
                    session.last_recommendation.explanation, message
                )
                confidence_override = session.last_recommendation.explanation["confidence"]

        if response_text is None:
            response_text = self._composer.compose(
                classified.intent, decision, results, traveller_name, synthesis_note=synthesis_note
            )
        session.add_message("assistant", response_text, intent=classified.intent.value)
        self._store.save(session)

        return self._build_output(
            session, classified, decision, results, response_text, confidence_override
        )

    # ------------------------------------------------------------------

    def _build_output(
        self,
        session: ConversationSession,
        classified: Any,
        decision: Decision,
        results: list[AgentResult],
        response_text: str,
        confidence_override: float | None = None,
    ) -> dict[str, Any]:
        all_assumptions = list(decision.assumptions)
        all_missing = list(decision.follow_up_questions)
        all_next_actions: list[str] = []

        for r in results:
            all_assumptions.extend(r.assumptions)
            all_missing.extend(r.missing_information)
            all_next_actions.extend(r.next_actions)

        # Trip Brain supplies its own weighted, completion-penalized
        # confidence (docs/TRIP_BRAIN_ARCHITECTURE.md's Confidence
        # Propagation) rather than a flat average across module results.
        if confidence_override is not None:
            confidence = confidence_override
        elif results:
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
            "goal_id": session.goal_id,
            "trip_id": session.trip_id,
        }

    def get_session(self, conversation_id: str) -> ConversationSession | None:
        """Look up a session by id — used by POST /explain to reuse the
        latest Trip Brain result instead of recomputing it."""
        return self._store.get(conversation_id)

    def get_session_by_trip_id(self, trip_id: str) -> ConversationSession | None:
        """Same as get_session, keyed by trip_id instead of conversation_id
        — for callers that only have the trip, not the conversation."""
        return self._store.find_by_trip_id(trip_id)

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

    def _create_trip(
        self,
        session: ConversationSession,
        entities: dict[str, str],
        profile: dict[str, Any] | None,
    ) -> str | None:
        try:
            from app.domains.trips.service import trip_planning_service
            trip = trip_planning_service.plan_from_conversation(
                traveller_id=session.traveller_id,
                goal_id=session.goal_id,
                entities=entities,
                profile=profile,
            )
            return trip["trip_id"]
        except Exception:
            return None

    def _get_flight_recommendations(
        self,
        session: ConversationSession,
        entities: dict[str, str],
        profile: dict[str, Any] | None,
    ) -> AgentResult | None:
        try:
            from app.domains.flights.service import flight_intelligence_service
            output = flight_intelligence_service.recommend_from_conversation(
                traveller_id=session.traveller_id,
                trip_id=session.trip_id,
                entities=entities,
                profile=profile,
            )
        except Exception:
            return None

        options = output["flight_options"]
        top = next(
            (f for f in options if f["recommendation_type"] == "BEST_OVERALL"),
            options[0] if options else None,
        )
        avg_confidence = sum(f["match_score"] for f in options) / len(options) if options else 0.0
        risks = [r for f in options for r in f["risks"]][:5]

        return AgentResult(
            agent_name="flight_intelligence",
            status=AgentStatus.SUCCESS if options else AgentStatus.NEEDS_INFORMATION,
            confidence=round(avg_confidence, 2),
            data={
                "count": len(options),
                "origin": output["origin"],
                "destination": output["destination"],
                "top_option": top or {},
                "flight_option_ids": [f["flight_option_id"] for f in options],
            },
            assumptions=output["assumptions"],
            risks=risks,
            next_actions=output["next_actions"],
        )

    def _get_accommodation_recommendations(
        self,
        session: ConversationSession,
        entities: dict[str, str],
        profile: dict[str, Any] | None,
    ) -> AgentResult | None:
        try:
            from app.domains.accommodation.service import accommodation_intelligence_service
            output = accommodation_intelligence_service.recommend_from_conversation(
                traveller_id=session.traveller_id,
                trip_id=session.trip_id,
                entities=entities,
                profile=profile,
            )
        except Exception:
            return None

        options = output["accommodation_options"]
        top = next(
            (a for a in options if a["recommendation_type"] == "BEST_OVERALL"),
            options[0] if options else None,
        )
        avg_confidence = sum(a["match_score"] for a in options) / len(options) if options else 0.0
        risks = [r for a in options for r in a["risks"]][:5]

        return AgentResult(
            agent_name="accommodation_intelligence",
            status=AgentStatus.SUCCESS if options else AgentStatus.NEEDS_INFORMATION,
            confidence=round(avg_confidence, 2),
            data={
                "count": len(options),
                "destination": output["destination"],
                "top_option": top or {},
                "accommodation_option_ids": [a["accommodation_option_id"] for a in options],
            },
            assumptions=output["assumptions"],
            risks=risks,
            next_actions=output["next_actions"],
        )

    def _get_destination_recommendations(
        self,
        session: ConversationSession,
        entities: dict[str, str],
        profile: dict[str, Any] | None,
    ) -> AgentResult | None:
        try:
            from app.domains.destinations.service import destination_intelligence_service
            output = destination_intelligence_service.recommend_from_conversation(
                traveller_id=session.traveller_id,
                trip_id=session.trip_id,
                entities=entities,
                profile=profile,
            )
        except Exception:
            return None

        options = output["destination_options"]
        top = next(
            (d for d in options if d["recommendation_type"] == "BEST_OVERALL"),
            options[0] if options else None,
        )
        avg_confidence = sum(d["match_score"] for d in options) / len(options) if options else 0.0
        risks = [r for d in options for r in d["risks"]][:5]

        return AgentResult(
            agent_name="destination_intelligence",
            status=AgentStatus.SUCCESS if options else AgentStatus.NEEDS_INFORMATION,
            confidence=round(avg_confidence, 2),
            data={
                "count": len(options),
                "city": output["city"],
                "top_option": top or {},
                "destination_option_ids": [d["destination_option_id"] for d in options],
            },
            assumptions=output["assumptions"],
            risks=risks,
            next_actions=output["next_actions"],
        )

    def _get_budget_recommendations(
        self,
        session: ConversationSession,
        entities: dict[str, str],
        profile: dict[str, Any] | None,
    ) -> AgentResult | None:
        try:
            from app.domains.budget.service import budget_intelligence_service
            output = budget_intelligence_service.recommend_from_conversation(
                traveller_id=session.traveller_id,
                trip_id=session.trip_id,
                entities=entities,
                profile=profile,
            )
        except Exception:
            return None

        options = output["budget_options"]
        top = next(
            (o for o in options if o["recommendation_type"] == "BEST_OVERALL"),
            options[0] if options else None,
        )
        avg_confidence = sum(o["match_score"] for o in options) / len(options) if options else 0.0
        risks = [r for o in options for r in o["risks"]][:5]

        return AgentResult(
            agent_name="budget_intelligence",
            status=AgentStatus.SUCCESS if options else AgentStatus.NEEDS_INFORMATION,
            confidence=round(avg_confidence, 2),
            data={
                "count": len(options),
                "destination": output["destination"],
                "top_option": top or {},
                "budget_option_ids": [o["budget_option_id"] for o in options],
            },
            assumptions=output["assumptions"],
            risks=risks,
            next_actions=output["next_actions"],
        )

    def _get_visa_assessment(
        self,
        session: ConversationSession,
        entities: dict[str, str],
        profile: dict[str, Any] | None,
    ) -> AgentResult | None:
        try:
            from app.domains.visa.service import visa_intelligence_service
            output = visa_intelligence_service.check_from_conversation(
                traveller_id=session.traveller_id,
                trip_id=session.trip_id,
                entities=entities,
                profile=profile,
            )
        except Exception:
            return None

        return AgentResult(
            agent_name="visa_intelligence",
            status=AgentStatus.SUCCESS,
            confidence=output["confidence"],
            data=output,
            assumptions=output["assumptions"],
            risks=output["risks"],
            next_actions=[output["recommendation"]],
        )

    def _get_weather_assessment(
        self,
        session: ConversationSession,
        entities: dict[str, str],
        profile: dict[str, Any] | None,
    ) -> AgentResult | None:
        try:
            from app.domains.weather.service import weather_intelligence_service
            output = weather_intelligence_service.analyse_from_conversation(
                traveller_id=session.traveller_id,
                trip_id=session.trip_id,
                entities=entities,
                profile=profile,
            )
        except Exception:
            return None

        return AgentResult(
            agent_name="weather_intelligence",
            status=AgentStatus.SUCCESS,
            confidence=output["confidence"],
            data=output,
            assumptions=output["assumptions"],
            risks=output["risks"],
            next_actions=[output["recommendation"]],
        )

    def _create_goal(
        self,
        session: ConversationSession,
        message: str,
        entities: dict[str, str],
    ) -> str | None:
        try:
            from app.domains.goals.service import goal_service
            goal = goal_service.create_from_conversation(session.traveller_id, message, entities)
            return goal["goal_id"]
        except Exception:
            return None


conversation_engine = ConversationEngine()

from typing import Any

from ai.concierge.conversation_session import ConversationSession
from ai.concierge.decision_engine import Decision, DecisionEngine
from ai.concierge.intent_classifier import ClassifiedIntent, Intent, IntentClassifier
from ai.concierge.response_composer import ResponseComposer
from ai.concierge.session_store import SessionStore, build_session_store
from ai.explainability.explainability_engine import explainability_engine
from ai.ports import PlanningPort, get_planning_port
from ai.shared.agent_result import AgentResult
from ai.shared.agent_status import AgentStatus
from ai.trip_brain.coordinator import TripBrain, trip_brain


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
    5. Dispatch to Trip Brain or a focused Discovery service.
    6. Compose response via ResponseComposer.
    7. Persist session.
    """

    def __init__(
        self,
        store: SessionStore | None = None,
        planning_port: PlanningPort | None = None,
        brain: TripBrain | None = None,
    ) -> None:
        self._store = store if store is not None else build_session_store()
        self._planning_port = planning_port
        self._trip_brain = brain or trip_brain
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

        classified = self._continue_plan_if_needed(
            session, self._classifier.classify(message)
        )
        classified = self._add_active_trip_context(session, classified, message)
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

        if classified.intent in {
            Intent.DESTINATION_QUESTION,
            Intent.TRAVEL_ADVICE,
        }:
            destination_result = self._get_destination_recommendations(
                session, classified.entities, profile
            )
            if destination_result:
                results = [destination_result]

        if classified.intent == Intent.BUDGET_ADVICE:
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

        if (
            classified.intent in {Intent.PLAN_TRIP, Intent.MODIFY_TRIP}
            and decision.has_enough_information
        ):
            unified = await self._trip_brain.plan(
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

    def _continue_plan_if_needed(
        self,
        session: ConversationSession,
        classified: ClassifiedIntent,
    ) -> ClassifiedIntent:
        """Merge facts across turns while a trip plan is awaiting answers.

        A reply such as "10 August to 17 August" has no standalone planning
        verb, so the rule-based classifier correctly sees it as general
        conversation. In an unfinished PLAN_TRIP session, however, it is an
        answer to the planner's pending question and must retain that intent.
        """
        continuing_plan = (
            session.active_goal == Intent.PLAN_TRIP.value
            and bool(session.pending_questions)
            and session.last_recommendation is None
        )
        if classified.intent != Intent.PLAN_TRIP and not continuing_plan:
            return classified

        merged = {**session.planning_entities, **classified.entities}
        session.planning_entities = merged
        return ClassifiedIntent(
            intent=Intent.PLAN_TRIP,
            confidence=(
                classified.confidence
                if classified.intent == Intent.PLAN_TRIP
                else max(0.8, classified.confidence)
            ),
            entities=merged,
        )

    def _add_active_trip_context(
        self,
        session: ConversationSession,
        classified: ClassifiedIntent,
        message: str,
    ) -> ClassifiedIntent:
        """Ground follow-up advice and changes in the active planning session."""
        contextual_intents = {
            Intent.MODIFY_TRIP,
            Intent.DESTINATION_QUESTION,
            Intent.TRAVEL_ADVICE,
            Intent.BUDGET_ADVICE,
        }
        if classified.intent not in contextual_intents:
            return classified

        new_entities = dict(classified.entities)
        merged = {**session.planning_entities, **new_entities}
        if session.trip_id:
            merged["trip_id"] = session.trip_id
        if (
            not merged.get("destination")
            and session.last_recommendation
            and session.last_recommendation.destination
        ):
            merged["destination"] = session.last_recommendation.destination
        if classified.intent == Intent.MODIFY_TRIP and new_entities:
            merged["modification_detail"] = message
        return ClassifiedIntent(
            intent=classified.intent,
            confidence=classified.confidence,
            entities=merged,
        )

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
            trip = self._port.create_trip(
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
            output = self._port.recommend_flights(
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
            output = self._port.recommend_accommodation(
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
            output = self._port.recommend_destinations(
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
            output = self._port.recommend_budget(
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
            output = self._port.check_visa(
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
            output = self._port.analyse_weather(
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
            goal = self._port.create_goal(session.traveller_id, message, entities)
            return goal["goal_id"]
        except Exception:
            return None

    @property
    def _port(self) -> PlanningPort:
        return self._planning_port or get_planning_port()


conversation_engine = ConversationEngine()

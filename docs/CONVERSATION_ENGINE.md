# Conversation Engine — Architecture

## Overview

The Conversation Engine is the central state machine for all traveller interactions in TravelOS.
Every message sent by a traveller passes through this layer. No code bypasses it.

**Business goal:** The traveller should feel they are speaking to an experienced travel consultant,
not a generic chatbot.

---

## Full Request Flow

```
POST /conversation/message
       │
       ▼
TravelConcierge.handle(message, traveller_id, conversation_id)
       │  Single AI entry point — nothing calls below this directly
       ▼
ConversationEngine.process(message, traveller_id, conversation_id)
       │
       ├─ _SessionStore.get_or_create()             → ConversationSession
       ├─ IntentClassifier.classify(message)        → ClassifiedIntent
       ├─ _fetch_profile(traveller_id)              → dict | None (from MemoryService)
       ├─ DecisionEngine.decide(intent, entities, profile)
       │       ├── has_enough_information?
       │       ├── requires_agents: [list]
       │       ├── follow_up_questions: [list]
       │       ├── is_safety_sensitive: bool
       │       └── requires_live_data: bool
       │
       ├─ [if has_enough_information]
       │       └─ TravelManager.execute(intent, context, decision, input_data)
       │               └─ AgentRegistry.get(name) → AgentClass
       │                       └─ asyncio.gather(*[agent.run(...) for each agent])
       │                               ├─ BudgetAgent.run()     → AgentResult
       │                               ├─ FlightAgent.run()     → AgentResult
       │                               ├─ HotelAgent.run()      → AgentResult
       │                               ├─ ExperienceAgent.run() → AgentResult
       │                               └─ VisaAgent.run()       → AgentResult
       │
       ├─ ResponseComposer.compose(intent, decision, results, name)
       │       └─ Coherent traveller-facing answer
       │
       ├─ session.add_message("assistant", response)
       ├─ _SessionStore.save(session)
       └─ return structured output dict
```

---

## Directory Structure

```
ai/
├── concierge/
│   ├── travel_concierge.py       ← Public API entry point
│   ├── conversation_engine.py    ← State machine + session management
│   ├── decision_engine.py        ← Decides agents + information requirements
│   ├── intent_classifier.py      ← Classifies message intent
│   └── response_composer.py      ← Composes traveller-facing answer
├── manager/
│   └── travel_manager.py         ← Dispatches to specialist agents concurrently
├── registry/
│   └── agent_registry.py         ← Maps names → agent classes
├── agents/
│   ├── budget_agent.py
│   ├── experience_agent.py
│   ├── flight_agent.py
│   ├── hotel_agent.py
│   └── visa_agent.py
├── shared/
│   ├── agent_context.py          ← Context passed to every agent
│   ├── agent_result.py           ← Rich structured result from every agent
│   └── agent_status.py           ← SUCCESS | NEEDS_INFORMATION | FAILED | PARTIAL | SKIPPED
└── memory/
    ├── memory_service.py
    └── traveller_intelligence_service.py
```

---

## ConversationSession

```python
@dataclass
class ConversationSession:
    conversation_id: str          # UUID — permanent identifier
    traveller_id: str | None      # links to TIP (set at start or on first message)
    trip_id: str | None           # set when an active trip is in scope
    history: list[ConversationMessage]
    active_goal: str | None       # current goal intent (plan_trip, view_profile, etc.)
    pending_questions: list[str]  # questions waiting to be answered
    context_summary: str          # rolling summary (Sprint 3+)
    created_at: str               # ISO 8601 UTC
    updated_at: str               # ISO 8601 UTC
```

---

## AgentResult

Every specialist agent returns a structured `AgentResult`:

```python
@dataclass
class AgentResult:
    agent_name: str
    status: AgentStatus           # SUCCESS | NEEDS_INFORMATION | FAILED | PARTIAL | SKIPPED
    confidence: float             # 0.0 – 1.0
    data: dict                    # agent-specific output
    assumptions: list[str]        # what the agent assumed
    missing_information: list[str]
    risks: list[str]
    recommendations: list[str]
    next_actions: list[str]
```

---

## POST /conversation/message

**Request:**
```json
{
  "traveller_id": "uuid-or-null",
  "message": "I want to plan a trip to Lagos next month",
  "conversation_id": "uuid-or-null"
}
```

**Response:**
```json
{
  "conversation_id": "uuid",
  "intent": "PLAN_TRIP",
  "response": "Here's what I've put together for your trip. ...",
  "confidence": 0.62,
  "assumptions": ["Budget style: balanced", "Cabin preference: economy"],
  "missing_information": [],
  "next_actions": ["confirm_flight_budget", "confirm_travel_dates"],
  "recommended_agents": ["flight_agent", "hotel_agent", "budget_agent", "experience_agent", "visa_agent"]
}
```

---

## Concurrent Agent Execution

Specialist agents run concurrently via `asyncio.gather()`. One failing agent does not block the rest — failures are caught and returned as `AgentStatus.FAILED` results.

---

## Sprint Roadmap

| Feature | Sprint |
|---------|--------|
| Rule-based intent classification | 1 ✅ |
| DecisionEngine (deterministic) | 1 ✅ |
| Mock specialist agents | 1 ✅ |
| Template-based ResponseComposer | 1 ✅ |
| Redis session persistence | 3 |
| LLM intent classification | 3 |
| LLM response generation | 3 |
| Live flight search | 4 |
| Live hotel search | 4 |
| Live visa data | 5 |
| Authentication | 2 |

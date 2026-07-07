# Conversation Engine — Architecture

## Overview

The Conversation Engine is the central state machine for all traveller interactions in TravelOS.
Every message sent by a traveller passes through this layer before any AI or booking logic is
invoked.

## Responsibility Boundaries

| Layer | Responsibility |
|-------|---------------|
| **ConversationRouter** (`services/api/app/conversation/conversation_router.py`) | Receive HTTP requests, validate input, return HTTP responses |
| **ConversationEngine** (`services/api/app/conversation/conversation_engine.py`) | Maintain session state, classify intent, dispatch work, compose reply |
| **IntentClassifier** (`services/api/app/conversation/intent_classifier.py`) | Classify each message into one of 8 intents |
| **ConversationStore** (`services/api/app/conversation/conversation_session.py`) | Store and retrieve conversation sessions (in-memory, Sprint 1) |
| **ResponseComposer** (`services/api/app/conversation/response_composer.py`) | Assemble natural-language replies from agent outputs |
| **TravelConciergeAgent** (`ai/agents/travel_concierge_agent.py`) | AI-side entry point; maps intent to structured agent output |
| **Orchestrator** (`ai/orchestration/orchestrator.py`) | Route work to the correct specialist agent via AgentRegistry |

---

## Request Flow

```
POST /conversation/{id}/message
       │
       ▼
ConversationEngine.process_message(conversation_id, message)
       │
       ├─ ConversationStore.get(conversation_id)         → ConversationSession
       ├─ IntentClassifier.classify(message)             → ClassifiedIntent
       ├─ session.add_message("user", message, intent)
       ├─ ConversationEngine._dispatch(session, classified)
       │        │
       │        ├── [plan_trip]    → _handle_plan_trip()
       │        │       └─ Orchestrator.run("travel_manager", {...})
       │        │               └─ TravelManagerAgent.run()
       │        ├── [modify_trip]  → compose_clarification()
       │        ├── [view_profile] → compose(intent, None)
       │        └── [general]     → compose("general_conversation", None)
       │
       ├─ session.add_message("assistant", reply)
       ├─ ConversationStore.save(session)
       └─ return {reply, intent, confidence, entities, active_goal, pending_questions}
```

---

## ConversationSession State

```python
@dataclass
class ConversationSession:
    conversation_id: str          # UUID — permanent session identifier
    traveller_id: str | None      # links session to a TIP (set at /start)
    trip_id: str | None           # set when an active trip is in scope
    history: list[ConversationMessage]  # full turn-by-turn history
    active_goal: str | None       # current traveller intent in scope
    pending_questions: list[str]  # questions engine is waiting to resolve
    context_summary: str          # rolling summary (populated in Sprint 3)
    created_at: str               # ISO 8601 UTC
    updated_at: str               # ISO 8601 UTC
```

### Message Record

```python
@dataclass
class ConversationMessage:
    role: str        # "user" | "assistant" | "system"
    content: str
    timestamp: str
    intent: str | None
```

---

## Active Goal Tracking

The engine sets `session.active_goal` whenever the classified intent is goal-forming:

| Intent | active_goal |
|--------|-------------|
| `plan_trip` | `plan_trip` |
| `modify_trip` | `modify_trip` |
| `view_profile` | `view_profile` |
| `update_preferences` | `update_preferences` |
| Other intents | Unchanged |

This allows follow-up turns to restore context without re-classifying.

---

## Pending Questions

When the engine needs information before it can proceed (e.g. no destination extracted
for a plan_trip intent), it sets `session.pending_questions` and returns a
`compose_clarification()` response. On the next turn, the engine checks whether the
answers are now in the message text.

---

## API Endpoints

### POST /conversation/start

Creates a new session. Optionally links it to a traveller profile.

**Request:**
```json
{ "traveller_id": "uuid-or-null" }
```

**Response `201`:**
```json
{
  "conversation_id": "uuid",
  "greeting": "Hello, Peter! I'm Tralvana, your AI travel concierge. Where would you like to go?"
}
```

### POST /conversation/{conversation_id}/message

Send a message. Returns the engine reply and session state snapshot.

**Request:**
```json
{ "message": "I want to plan a trip to Lagos next month" }
```

**Response `200`:**
```json
{
  "conversation_id": "uuid",
  "reply": "I'll help you plan that trip. I'm arranging flights, accommodation, itinerary for Lagos.",
  "intent": "plan_trip",
  "confidence": 0.85,
  "entities": { "destination": "Lagos", "date_hint": "next month" },
  "active_goal": "plan_trip",
  "pending_questions": []
}
```

### GET /conversation/{conversation_id}

Retrieve session metadata and message count.

---

## Sprint 1 Constraints

- Sessions stored in process memory. Lost on server restart.
- IntentClassifier is rule-based (keyword matching).
- ResponseComposer is template-based.
- TravelConciergeAgent returns stub outputs (no live APIs).
- No authentication — conversation ID is the only access control.

## Planned Extensions

| Feature | Sprint |
|---------|--------|
| Redis session store | 3 |
| LLM-powered intent classification | 3 |
| LLM-powered response generation | 3 |
| Rolling context_summary via LLM | 3 |
| Multi-turn goal resolution | 3 |
| Trip ID linking | 4 |
| Authentication | 2 |
